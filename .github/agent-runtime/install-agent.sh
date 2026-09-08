#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# install-agent.sh - install the chosen coding-agent CLI and wire up BYOK.
#   copilot  -> npm i -g @github/copilot, COPILOT_PROVIDER_* env (no GH login)
#   opencode -> npm i -g opencode-ai, generated opencode.json
# ---------------------------------------------------------------------------
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SRC/lib.sh"

TOOL="${AGENT_TOOL:-copilot}"
export npm_config_loglevel=error

log "Installing agent backend: ${TOOL}"

case "$TOOL" in
  copilot)
    npm install -g --no-fund --no-audit "@github/copilot@latest" || \
      die "failed to install @github/copilot"
    command -v copilot >/dev/null 2>&1 || die "'copilot' binary not on PATH after install"
    ok "copilot $(copilot --version 2>/dev/null | head -1 || echo '(version unknown)')"

    : "${BYOK_BASE_URL:?BYOK_BASE_URL required}"
    MODEL="${BYOK_ACTIVE_MODEL:-${BYOK_MODEL:-glm-5.3-free}}"
    [ -n "${BYOK_API_KEY:-}" ] || warn "BYOK_API_KEY is empty"

    export COPILOT_PROVIDER_TYPE="openai"
    export COPILOT_PROVIDER_BASE_URL="$BYOK_BASE_URL"
    export COPILOT_PROVIDER_API_KEY="${BYOK_API_KEY:-}"
    export COPILOT_MODEL="$MODEL"
    export COPILOT_OFFLINE="true"

    log "BYOK -> type=openai base=$BYOK_BASE_URL model=$MODEL offline=true"
    {
      echo "export COPILOT_PROVIDER_TYPE='openai'"
      echo "export COPILOT_PROVIDER_BASE_URL='$BYOK_BASE_URL'"
      echo "export COPILOT_PROVIDER_API_KEY='${BYOK_API_KEY:-}'"
      echo "export COPILOT_MODEL='$MODEL'"
      echo "export COPILOT_OFFLINE='true'"
    } > /tmp/byok.env
    ;;

  opencode)
    npm install -g --no-fund --no-audit "opencode-ai@latest" || \
      die "failed to install opencode-ai"
    command -v opencode >/dev/null 2>&1 || die "'opencode' binary not on PATH after install"
    ok "opencode $(opencode --version 2>/dev/null | head -1 || echo '(version unknown)')"

    CFG_DIR="${HOME}/.config/opencode"
    mkdir -p "$CFG_DIR"
    MODEL="${BYOK_ACTIVE_MODEL:-${BYOK_MODEL:-glm-5.3-free}}"
    cat > "$CFG_DIR/opencode.json" <<JSON
{
  "\$schema": "https://opencode.ai/config.json",
  "provider": {
    "byok": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "BYOK",
      "options": {
        "baseURL": "${BYOK_BASE_URL}",
        "apiKey": "${BYOK_API_KEY:-}"
      },
      "models": {
        "${MODEL}": { "name": "${MODEL}" }
      }
    }
  },
  "model": "byok/${MODEL}"
}
JSON
    export OPENCODE_CONFIG="$CFG_DIR/opencode.json"
    ok "opencode BYOK config -> $CFG_DIR/opencode.json (model byok/${MODEL})"
    {
      echo "export OPENCODE_CONFIG='$CFG_DIR/opencode.json'"
    } > /tmp/byok.env
    ;;

  *) die "Unknown AGENT_TOOL '$TOOL' (expected: copilot | opencode)" ;;
esac

export CI=1 NO_COLOR=1 TERM=dumb
ok "Agent backend '${TOOL}' ready"
