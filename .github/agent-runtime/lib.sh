#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# lib.sh - shared helpers, platform-detection and BYOK preflight.
# Works in GitLab CI (CI_* env) and GitHub Actions (GITHUB_* env).
# ---------------------------------------------------------------------------
set -euo pipefail

log()  { printf '\033[1;36m[agent]\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m[ ok ]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[fail]\033[0m %s\n' "$*" >&2; exit 1; }

WORKSPACE="${CI_PROJECT_DIR:-${GITHUB_WORKSPACE:-$PWD}}"
export WORKSPACE

# ---------------------------------------------------------------------------
# Platform detection: GITLAB | GITHUB
# ---------------------------------------------------------------------------
detect_platform() {
  if [ -n "${CI_PROJECT_ID:-}" ]; then
    HUB_PLATFORM=GITLAB
    HUB_PROJECT_ID="$CI_PROJECT_ID"
    HUB_RUN_ID="${CI_PIPELINE_ID:-local}"
    HUB_JOB_ID="${CI_JOB_ID:-local}"
  elif [ -n "${GITHUB_REPOSITORY:-}" ]; then
    HUB_PLATFORM=GITHUB
    HUB_PROJECT_ID="$GITHUB_REPOSITORY"
    HUB_RUN_ID="${GITHUB_RUN_ID:-local}"
    HUB_JOB_ID="${GITHUB_RUN_ID:-local}"
  else
    HUB_PLATFORM=LOCAL
    HUB_PROJECT_ID="${TARGET_PROJECT_ID:-local}"
    HUB_RUN_ID="local"
    HUB_JOB_ID="local"
  fi
  export HUB_PLATFORM HUB_PROJECT_ID HUB_RUN_ID HUB_JOB_ID
}

# ---------------------------------------------------------------------------
# Token resolution: the pipeline owns ALL repo mutations. The agent never
# sees any token.
# ---------------------------------------------------------------------------
require_token() {
  case "${HUB_PLATFORM:-}" in
    GITLAB)
      [ -n "${GL_AGENT_TOKEN:-}" ] || die "GL_AGENT_TOKEN missing"
      ;;
    GITHUB)
      [ -n "${GH_TOKEN:-}" ] || [ -n "${AGENT_GH_PAT:-}" ] || die "GH_TOKEN/AGENT_GH_PAT missing"
      ;;
    *) : ;;
  esac
}

# api <METHOD> <path> [curl args...] -> body on stdout
api() {
  local method="$1" path="$2"; shift 2
  local body code auth=() tok
  case "${HUB_PLATFORM:-}" in
    GITLAB)  auth=(-H "PRIVATE-TOKEN: ${GL_AGENT_TOKEN}")
             base="https://gitlab.com/api/v4" ;;
    GITHUB)  # Publish operations need a PAT; ephemeral GH_TOKEN may be
             # policy-blocked from PR creation. AGENT_GH_PAT wins when set.
             tok="${AGENT_GH_PAT:-${GH_TOKEN:-}}"
             auth=(-H "Authorization: Bearer ${tok}"
                  -H "Accept: application/vnd.github+json")
             base="https://api.github.com" ;;
    *)       die "api() called before detect_platform" ;;
  esac
  body="$(mktemp)"
  code="$(curl -sS -m 120 -o "$body" -w '%{http_code}' "${auth[@]}" \
            -H 'Content-Type: application/json' -X "$method" "${base}${path}" "$@")" \
    || { rm -f "$body"; return 1; }
  if [ "${code}" -ge 400 ]; then
    warn "HTTP ${code} on ${method} ${path}"
    head -c 400 "$body" >&2 || true; echo >&2
    rm -f "$body"; return 1
  fi
  cat "$body"; rm -f "$body"
}

# URL-encode a repository file path ('/' -> '%2F')
enc_path() { printf '%s' "${1//\//%2F}"; }
enc_uri()  { printf '%s' "$1" | jq -sRr @uri; }

# Fetch a raw platform file: raw <project> <path> <ref>
raw() {
  local pid="$1" fpath="$2" ref="$3"
  case "${HUB_PLATFORM:-}" in
    GITLAB)
      curl -sS -m 90 -H "PRIVATE-TOKEN: ${GL_AGENT_TOKEN}" \
        "https://gitlab.com/api/v4/projects/${pid}/repository/files/$(enc_path "$fpath")/raw?ref=$(enc_uri "$ref")" \
        || return 1
      ;;
    GITHUB)
      curl -sS -m 90 -H "Authorization: Bearer ${GH_TOKEN}" \
        "https://api.github.com/repos/${pid}/contents/$(enc_path "$fpath")?ref=$(enc_uri "$ref")" \
        | jq -r '.content' | base64 -d 2>/dev/null || return 1
      ;;
    *) return 1 ;;
  esac
}

# Resolve the http(s) clone URL of the target project
repo_url() {
  case "${HUB_PLATFORM:-}" in
    GITLAB)
      api GET "/projects/${HUB_PROJECT_ID}" \
        | jq -r '.http_url_to_repo // empty'
      ;;
    GITHUB)
      if [ -n "${TARGET_REPO_URL:-}" ]; then echo "$TARGET_REPO_URL"; return 0; fi
      echo "https://github.com/${HUB_PROJECT_ID}.git"
      ;;
    *) echo "${TARGET_REPO_URL:-}" ;;
  esac
}

# Push-authenticated clone URL (token injected for git only)
auth_url() {
  local url="$1" tok
  case "${HUB_PLATFORM:-}" in
    GITLAB)  printf '%s' "$url" | sed -E "s#^https://#https://oauth2:${GL_AGENT_TOKEN}@#" ;;
    GITHUB)  tok="${AGENT_GH_PAT:-${GH_TOKEN:-}}"
             printf '%s' "$url" | sed -E "s#^https://#https://x-access-token:${tok}@#" ;;
    *)       printf '%s' "$url" ;;
  esac
}

# Slugify text -> lowercase alnum + dashes
slugify() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' \
    | jq -sRr 'gsub("[^a-z0-9]+";"-") | gsub("^-+|-+$";"")' | cut -c1-48
}

# ---------------------------------------------------------------------------
# BYOK preflight: poll the OpenAI-compatible endpoint until a tiny completion
# succeeds, switching primary->fallback model if the primary is unhealthy.
# Sets BYOK_ACTIVE_MODEL for install-agent.sh.
# ---------------------------------------------------------------------------
preflight_byok() {
  local base="${BYOK_BASE_URL:-}" key="${BYOK_API_KEY:-}"
  local model="${BYOK_MODEL:-glm-5.3-free}" fb="${BYOK_FALLBACK_MODEL:-qwen3.8-27b}"
  [ -n "$base" ] && [ -n "$key" ] || { warn "BYOK env incomplete - skipping preflight"; return 0; }

  local attempt=0 max="${PREFLIGHT_MAX_WAIT_SECONDS:-900}" started
  local probe_out
  probe_out="$(mktemp)"        # portable (no hardcoded /tmp on Windows hosts)
  started=$(date +%s)

  probe() {  # probe <model> -> 0 healthy
    curl -sS -m 60 -o "$probe_out" -w '%{http_code}' \
      -X POST "$base/chat/completions" \
      -H "Authorization: Bearer $key" -H 'Content-Type: application/json' \
      -d "{\"model\":\"$1\",\"messages\":[{\"role\":\"user\",\"content\":\"Reply OK\"}],\"max_tokens\":10}" \
      | grep -q '^200$'
  }

  while true; do
    attempt=$((attempt+1))
    if probe "$model"; then
      BYOK_ACTIVE_MODEL="$model"; export BYOK_ACTIVE_MODEL
      ok "BYOK preflight: model '$model' healthy (attempt $attempt)"
      return 0
    fi
    if probe "$fb"; then
      BYOK_ACTIVE_MODEL="$fb"; export BYOK_ACTIVE_MODEL
      warn "BYOK preflight: primary '$model' unhealthy - falling back to '$fb'"
      return 0
    fi
    if [ $(( $(date +%s) - started )) -ge "$max" ]; then
      die "BYOK endpoint unhealthy after ${max}s (both '$model' and '$fb')"
    fi
    log "BYOK preflight: endpoint still warming up (attempt $attempt) - waiting 30s"
    sleep 30
  done
}

# Post a status callback to the hub service (best-effort)
notify_hub() {
  local status="$1" detail="$2"
  [ -n "${HUB_CALLBACK_URL:-}" ] || return 0
  local payload
  payload="$(jq -n --arg p "${HUB_PLATFORM:-}" --arg pid "${HUB_PROJECT_ID:-}" \
                    --arg run "${HUB_RUN_ID:-}" --arg s "$status" --arg d "$detail" \
             '{platform:$p, projectId:$pid, pipelineId:$run, status:$s, detail:$d, at:(now|floor)}')"
  curl -sS -m 30 -o /dev/null -X POST "$HUB_CALLBACK_URL" \
    -H 'Content-Type: application/json' -d "$payload" || return 1
  ok "hub notified: $status"
}
