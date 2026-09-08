#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# execute.sh - Clone the target repo and run the coding agent in fully
#              autonomous YOLO/autopilot mode until the task completes.
# ---------------------------------------------------------------------------
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SRC/lib.sh"
[ -f /tmp/byok.env ] && source /tmp/byok.env
export CI=1 NO_COLOR=1 TERM=dumb

OUT_DIR="$WORKSPACE/agent-out"
PROMPT="$OUT_DIR/prompt.md"
WORK_DIR="$WORKSPACE/.work/repo"
[ -s "$PROMPT" ] || die "No prompt at $PROMPT (run ingest.sh first)"

require_token

# ---------------------------------------------------------------------------
# 1. Resolve + clone the target repository
# ---------------------------------------------------------------------------
TARGET_BRANCH="${TARGET_BRANCH:-main}"
if [ -n "${TARGET_REPO_URL:-}" ]; then
  REPO_URL="$TARGET_REPO_URL"
else
  REPO_URL="$(repo_url)"
  [ -n "$REPO_URL" ] || die "Could not resolve repo URL for ${HUB_PROJECT_ID}"
fi

rm -rf "$WORK_DIR"; mkdir -p "$(dirname "$WORK_DIR")"
log "Cloning ${REPO_URL} (branch ${TARGET_BRANCH})"
if ! git clone --quiet --branch "$TARGET_BRANCH" --single-branch \
        "$(auth_url "$REPO_URL")" "$WORK_DIR" 2>/dev/null; then
  warn "branch '${TARGET_BRANCH}' not cloneable; cloning default branch"
  git clone --quiet "$(auth_url "$REPO_URL")" "$WORK_DIR"
fi
ok "Clone ready at $WORK_DIR"

# ---------------------------------------------------------------------------
# 2. Run the agent - no TTY, no prompts, no interactivity
# ---------------------------------------------------------------------------
PROMPT_TEXT="$(cat "$PROMPT")"
LOG="$OUT_DIR/agent.log"
: > "$LOG"

TIMEOUT="${AGENT_TIMEOUT_SECONDS:-3600}"
TOOL="${AGENT_TOOL:-copilot}"
CONTINUES="${MAX_AUTOPILOT_CONTINUES:-40}"

log "Launching '${TOOL}' in autopilot/YOLO mode (timeout ${TIMEOUT}s)"

cd "$WORK_DIR"

RC=0
case "$TOOL" in
  copilot)
    timeout "$TIMEOUT" copilot --autopilot --yolo \
      --max-autopilot-continues "$CONTINUES" \
      --model "${COPILOT_MODEL}" \
      -p "$PROMPT_TEXT" < /dev/null >> "$LOG" 2>&1 || RC=$?
    ;;
  opencode)
    timeout "$TIMEOUT" opencode --non-interactive --continue \
      run "$PROMPT_TEXT" >> "$LOG" 2>&1 || RC=$?
    ;;
  *) die "Unknown AGENT_TOOL '$TOOL'" ;;
esac

echo "---- last 40 lines of agent log ----"
tail -40 "$LOG" || true
echo "------------------------------------"

if [ "$RC" -ne 0 ]; then
  warn "agent exited with code ${RC} (124 = timeout)"
fi

# sanity: did the agent actually touch anything?
if [ -z "$(git -C "$WORK_DIR" status --porcelain)" ]; then
  warn "agent produced no file changes"
else
  ok "agent produced changes:"
  git -C "$WORK_DIR" --no-pager status --short | head -20
fi

exit "$RC"
