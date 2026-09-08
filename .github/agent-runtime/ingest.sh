#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# ingest.sh - Pull the dynamic agent configuration.
#
# The hub service committed agent-run/manifest.json to the config branch of
# the target repo. This script fetches it, extracts AGENTS.md /
# SYSTEM_INSTRUCTIONS.md / SKILLS.md / TASK / persona / MCP servers and
# composes the final non-interactive prompt.
# ---------------------------------------------------------------------------
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SRC/lib.sh"

OUT_DIR="$WORKSPACE/agent-out"
CTX_DIR="$OUT_DIR/context"
mkdir -p "$CTX_DIR"

# ref to read from: the branch/commit this pipeline runs on
REF="${CI_COMMIT_REF_NAME:-${GITHUB_REF_NAME:-main}}"

log "Ingesting agent manifest from ${HUB_PROJECT_ID}@${REF}"

MANIFEST="$CTX_DIR/manifest.json"
if raw "$HUB_PROJECT_ID" "agent-run/manifest.json" "$REF" > "$MANIFEST" 2>/dev/null \
   && [ -s "$MANIFEST" ]; then
  MANIFEST_BYTES="$(wc -c < "$MANIFEST" | tr -d '[:space:]')"
  ok "manifest.json fetched: ${MANIFEST_BYTES} bytes"
else
  # fall back to pipeline-variable mode (TASK variable set at trigger time)
  warn "manifest.json not found - falling back to TASK pipeline variable"
  : > "$MANIFEST"
fi

jq_m() { jq -r "$1 // empty" "$MANIFEST" 2>/dev/null || true; }

# ---- extract the four configuration documents ------------------------------
jq_m '.agentsMd'             > "$CTX_DIR/AGENTS.md"
jq_m '.systemInstructionsMd' > "$CTX_DIR/SYSTEM_INSTRUCTIONS.md"
jq_m '.skillsMd'             > "$CTX_DIR/SKILLS.md"
jq_m '.task'                 > "$CTX_DIR/TASK.md"

# persona is shorthand; expand into system instructions if no full doc given
PERSONA="$(jq_m '.persona')"
if [ -n "$PERSONA" ] && [ ! -s "$CTX_DIR/SYSTEM_INSTRUCTIONS.md" ]; then
  cat > "$CTX_DIR/SYSTEM_INSTRUCTIONS.md" <<EOF
# Agent persona: ${PERSONA}

You are ${PERSONA}. You operate autonomously inside a CI pipeline with no
human available. Make reasonable decisions, document assumptions, and
deliver complete, working results.
EOF
fi

# MCP servers -> written where the CLI agents look for them
MCP="$(jq -c '.mcpServers // empty' "$MANIFEST" 2>/dev/null || true)"
if [ -n "$MCP" ] && [ "$MCP" != "null" ]; then
  mkdir -p "$WORKSPACE/.copilot" "$HOME/.copilot" 2>/dev/null || true
  printf '%s\n' "$MCP" > "$WORKSPACE/.copilot/mcp.json" 2>/dev/null || true
  MCP_KEYS="$(printf '%s' "$MCP" | jq -r 'keys | join(", ")')"
  ok "MCP servers configured: ${MCP_KEYS}"
fi

# inline TASK variable (manual triggers) overrides everything
if [ -n "${TASK:-}" ]; then
  printf '%s\n' "$TASK" > "$CTX_DIR/TASK.md"
  ok "TASK <- inline pipeline variable (${#TASK} chars)"
fi

[ -s "$CTX_DIR/TASK.md" ] || die "No task found in manifest or TASK variable."

# ---- compose the final prompt ------------------------------------------------
PROMPT="$OUT_DIR/prompt.md"
: > "$PROMPT"

emit() {
  local title="$1" file="$2"
  [ -s "$file" ] || return 0
  {
    echo ""
    echo "================================================================"
    echo "## ${title}"
    echo "================================================================"
    echo ""
    cat "$file"
    echo ""
  } >> "$PROMPT"
}

emit "SYSTEM INSTRUCTIONS (your role and persona)" "$CTX_DIR/SYSTEM_INSTRUCTIONS.md"
emit "REPOSITORY AGENT CONTRACT (AGENTS.md)"        "$CTX_DIR/AGENTS.md"
emit "SKILLS AVAILABLE TO YOU"                       "$CTX_DIR/SKILLS.md"

{
  echo ""
  echo "================================================================"
  echo "## RUN CONTEXT"
  echo "================================================================"
  echo ""
  echo "- Platform          : ${HUB_PLATFORM}"
  echo "- Project           : ${HUB_PROJECT_ID}"
  echo "- Base branch       : ${TARGET_BRANCH:-main}"
  echo "- Agent backend     : ${AGENT_TOOL:-copilot}"
  echo "- Model             : ${BYOK_ACTIVE_MODEL:-${BYOK_MODEL:-}}"
  echo "- Run id            : ${HUB_RUN_ID}"
  echo ""
} >> "$PROMPT"

emit "TASK (complete this end-to-end, then stop)" "$CTX_DIR/TASK.md"

{
  echo ""
  echo "## OUTPUT CONTRACT"
  echo ""
  echo "When the task is complete you MUST have:"
  echo "  1. Made all source changes inside this repository working tree."
  echo "  2. Written AGENT_SUMMARY.md in the repository root containing:"
  echo "       - What you changed and why"
  echo "       - Files added/modified"
  echo "       - How to verify (exact commands)"
  echo "       - Risks, assumptions, follow-ups"
  echo "  3. Left all changes saved to disk (uncommitted is fine)."
  echo "Do NOT commit, push, or create MRs/PRs -"
  echo "the pipeline performs all git + platform operations for you."
  echo ""
} >> "$PROMPT"

ok "Prompt composed -> $PROMPT ($(stat -c%s "$PROMPT" 2>/dev/null || wc -c < "$PROMPT" | tr -d '[:space:]') bytes)"
