#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# run.sh - Orchestrator: install -> ingest -> execute -> publish
# Platform-agnostic: works in GitLab CI and GitHub Actions.
#   GitLab env:  CI_PROJECT_DIR, CI_PIPELINE_ID, CI_JOB_TOKEN (unused), GL_AGENT_TOKEN
#   GitHub env:  GITHUB_WORKSPACE, GITHUB_RUN_ID, GH_TOKEN
# ---------------------------------------------------------------------------
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SRC/lib.sh"

OUT_DIR="${WORKSPACE:-$PWD}/agent-out"
mkdir -p "$OUT_DIR"
: > "$OUT_DIR/ci.env"

echo "=============================================================="
echo " Unified Agent Runtime (cicd-hub)"
echo " backend=${AGENT_TOOL:-copilot}  model=${BYOK_MODEL:-}"
echo " platform=${HUB_PLATFORM:-auto-detected}"
echo "=============================================================="

# --- platform auto-detection + platform glue -------------------------------
detect_platform

# --- peek per-run config from the manifest BEFORE install -----------------
# GitHub Actions env is static (no per-run variables): the manifest is the
# only carrier of the requested backend/model. GitLab pipeline vars take
# precedence when present (they carry the same values).
REF="${CI_COMMIT_REF_NAME:-${GITHUB_REF_NAME:-main}}"
if MANIFEST_PEEK="$(raw "${HUB_PROJECT_ID}" "agent-run/manifest.json" "$REF" 2>/dev/null)" \
   && [ -n "$MANIFEST_PEEK" ]; then
  TOOL_PEEK="$(printf '%s' "$MANIFEST_PEEK" | jq -r '.agentTool // empty' 2>/dev/null || true)"
  if [ -n "${AGENT_TOOL:-}" ]; then
    log "agent backend: ${AGENT_TOOL} (pipeline variable; manifest says '${TOOL_PEEK:-?}')"
  elif [ -n "$TOOL_PEEK" ]; then
    export AGENT_TOOL="$TOOL_PEEK"
    log "agent backend: ${AGENT_TOOL} (from manifest)"
  fi
  # Per-run model override: request-level values win over repo/project
  # defaults. (pre-install so preflight_byok probes the requested model)
  MODEL_PEEK="$(printf '%s' "$MANIFEST_PEEK" | jq -r '.model // empty' 2>/dev/null || true)"
  FB_PEEK="$(printf '%s' "$MANIFEST_PEEK" | jq -r '.fallbackModel // empty' 2>/dev/null || true)"
  [ -n "$MODEL_PEEK" ] && { export BYOK_MODEL="$MODEL_PEEK"; log "run model: $MODEL_PEEK (from manifest)"; }
  [ -n "$FB_PEEK" ] && { export BYOK_FALLBACK_MODEL="$FB_PEEK"; }
  unset MANIFEST_PEEK TOOL_PEEK MODEL_PEEK FB_PEEK
fi

# --- BYOK preflight: wait for the inference endpoint to be healthy ---------
# (free-tier routers have transient 503 windows; the pipeline must not die
#  because the model backend blipped at trigger time)
preflight_byok

"$SRC/install-agent.sh"
"$SRC/ingest.sh"

# --- Execute. Non-zero exit must NOT skip publishing -----------------------
RC=0
if ! "$SRC/execute.sh"; then RC=$?; fi

export AGENT_EXIT_CODE="$RC"
"$SRC/publish.sh" || warn "publish.sh reported a problem"

# --- read back publish results (child-process exports cannot reach us) ------
# publish.sh writes agent-out/ci.env precisely so the orchestrator can
# recover the branch/MR-URL after the child exits.
[ -f "$OUT_DIR/ci.env" ] && . "$OUT_DIR/ci.env"

# --- optional webhook callback to the hub service --------------------------
if [ -n "${HUB_CALLBACK_URL:-}" ]; then
  notify_hub "finished" "exit=${RC} branch=${AGENT_RESULT_BRANCH:-${BRANCH:-none}} mr=${AGENT_RESULT_MR_URL:-${MR_URL:-none}}" \
    || warn "hub callback failed (non-fatal)"
fi

if [ "$RC" -ne 0 ]; then
  echo "=============================================================="
  warn "Agent run finished with exit code ${RC}"
  echo "=============================================================="
fi
exit 0   # artifacts + MR comment carry the real status
