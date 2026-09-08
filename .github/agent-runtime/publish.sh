#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# publish.sh - Commit the agent's work to a new branch, push it, open a
#              Merge Request (GitLab) or Pull Request (GitHub) and post an
#              enhancement summary comment - all via the REST API.
# The agent NEVER sees the token; this script owns every mutation.
# ---------------------------------------------------------------------------
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SRC/lib.sh"

OUT_DIR="$WORKSPACE/agent-out"
WORK_DIR="$WORKSPACE/.work/repo"
mkdir -p "$OUT_DIR"
: > "$OUT_DIR/ci.env"
note_env() { printf '%s=%s\n' "$1" "$2" >> "$OUT_DIR/ci.env"; }
note_env "AGENT_TOOL" "${AGENT_TOOL:-copilot}"
note_env "BRANCH"     ""
note_env "MR_URL"     ""

require_token
[ -d "$WORK_DIR/.git" ] || { warn "No clone at $WORK_DIR - nothing to publish"; exit 0; }

cd "$WORK_DIR"

# ---------------------------------------------------------------------------
# 1. Branch + commit
# ---------------------------------------------------------------------------
TARGET_BRANCH="${TARGET_BRANCH:-main}"
STAMP="$(date -u +%Y%m%d-%H%M%S)"
TASK_SLUG="$(slugify "${TASK_SLUG_OVERRIDE:-$(head -1 "$OUT_DIR/context/TASK.md" 2>/dev/null || echo task)}")"
[ -n "$TASK_SLUG" ] || TASK_SLUG="task"
BRANCH="agent/${STAMP}-${TASK_SLUG}"

git checkout -q -B "$BRANCH" 2>/dev/null || git checkout -q "$BRANCH"

if [ -z "$(git status --porcelain)" ]; then
  warn "Agent produced no changes - skipping commit"
  notify_hub "no-changes" "branch=${BRANCH}" || true
  exit 0
fi

# never commit build artefacts
find . -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
find . -name '*.py[co]' -delete 2>/dev/null || true
rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage node_modules 2>/dev/null || true

git add -A
git -c user.name="cicd-hub Agent" -c user.email="agent@hub.invalid" \
    commit -q -m "feat(agent): ${TASK_SLUG}

Autonomously produced by the unified agent runtime.
Backend: ${AGENT_TOOL:-copilot}  Model: ${BYOK_ACTIVE_MODEL:-}
Platform: ${HUB_PLATFORM}  Run: ${HUB_RUN_ID}"

ok "Committed changes on branch '$BRANCH'"
git --no-pager log --oneline -1
note_env "BRANCH" "$BRANCH"
export AGENT_RESULT_BRANCH="$BRANCH"

# ---------------------------------------------------------------------------
# 2. Push (token-authenticated)
# ---------------------------------------------------------------------------
REPO_URL="$(repo_url)"
case "${HUB_PLATFORM}" in
  GITLAB)
    git push -q "$(auth_url "$REPO_URL")" "HEAD:refs/heads/$BRANCH" \
      -o ci.skip 2>/dev/null || git push -q "$(auth_url "$REPO_URL")" "HEAD:refs/heads/$BRANCH"
    ;;
  GITHUB)
    git push -q "$(auth_url "$REPO_URL")" "HEAD:refs/heads/$BRANCH"
    ;;
esac
ok "Pushed $BRANCH"
notify_hub "pushed" "branch=${BRANCH}" || true

# ---------------------------------------------------------------------------
# 3. Description from AGENT_SUMMARY.md (agent-written) + git metadata
# ---------------------------------------------------------------------------
SUMMARY=""
if [ -s "$WORK_DIR/AGENT_SUMMARY.md" ]; then
  SUMMARY="$(cat "$WORK_DIR/AGENT_SUMMARY.md")"
  ok "Found AGENT_SUMMARY.md (${#SUMMARY} chars)"
else
  warn "Agent did not write AGENT_SUMMARY.md - falling back to git metadata"
fi

DIFFSTAT="$(git --no-pager diff --stat "$TARGET_BRANCH"..."$BRANCH" 2>/dev/null | tail -40 || true)"
CHANGED="$(git --no-pager diff --name-status "$TARGET_BRANCH"..."$BRANCH" 2>/dev/null || true)"
TASK_BODY="$(head -60 "$OUT_DIR/context/TASK.md" 2>/dev/null || echo '(unknown)')"

DESC="## Autonomous agent run

**Platform:** \`${HUB_PLATFORM}\`  **Backend:** \`${AGENT_TOOL:-copilot}\`  **Model:** \`${BYOK_ACTIVE_MODEL:-}\`
**Run:** \`${HUB_RUN_ID}\`

### Task
${TASK_BODY}

### Agent summary
${SUMMARY:-_(none provided)_}

### Files changed
\`\`\`
${CHANGED:-(unavailable)}
\`\`\`

### Diffstat
\`\`\`
${DIFFSTAT:-(unavailable)}
\`\`\`

---
_Generated autonomously by the unified agent runtime. Review before merging._"

# ---------------------------------------------------------------------------
# 4. Open MR (GitLab) or PR (GitHub) + post summary comment
# ---------------------------------------------------------------------------
case "${HUB_PLATFORM}" in
  GITLAB)
    PID="${TARGET_PROJECT_ID:-$HUB_PROJECT_ID}"
    TITLE="feat(agent): ${TASK_SLUG}"
    PAYLOAD="$(jq -n --arg s "$BRANCH" --arg t "$TARGET_BRANCH" --arg ti "$TITLE" --arg d "$DESC" \
      '{source_branch:$s, target_branch:$t, title:$ti, description:$d, remove_source_branch:true}')"
    MR_JSON="$(api POST "/projects/${PID}/merge_requests" -d "$PAYLOAD")" \
      || { warn "MR creation failed"; exit 0; }
    MR_IID="$(printf '%s' "$MR_JSON" | jq -r '.iid')"
    MR_URL="$(printf '%s' "$MR_JSON" | jq -r '.web_url')"
    ok "Merge request opened: $MR_URL"
    note_env "MR_URL" "$MR_URL"
    export AGENT_RESULT_MR_URL="$MR_URL"

    COMMENT="## Enhancement summary

${SUMMARY:-_(the agent did not leave a summary)_}

**Verification:** the task, all file changes and this summary were produced
fully autonomously by \`${AGENT_TOOL:-copilot}\` (model \`${BYOK_ACTIVE_MODEL:-}\`) in YOLO/autopilot mode. No human was in the loop."
    api POST "/projects/${PID}/merge_requests/${MR_IID}/notes" \
      -d "$(jq -n --arg b "$COMMENT" '{body:$b}')" >/dev/null || warn "comment failed"
    ok "Summary comment posted to MR !${MR_IID}"
    ;;

  GITHUB)
    REPO="${HUB_PROJECT_ID}"
    TITLE="feat(agent): ${TASK_SLUG}"
    PAYLOAD="$(jq -n --arg s "$BRANCH" --arg t "$TARGET_BRANCH" --arg ti "$TITLE" --arg d "$DESC" \
      '{head:$s, base:$t, title:$ti, body:$d}')"
    PR_JSON="$(api POST "/repos/${REPO}/pulls" -d "$PAYLOAD")" \
      || { warn "PR creation failed"; exit 0; }
    PR_NUM="$(printf '%s' "$PR_JSON" | jq -r '.number')"
    PR_URL="$(printf '%s' "$PR_JSON" | jq -r '.html_url')"
    ok "Pull request opened: $PR_URL"
    note_env "MR_URL" "$PR_URL"
    export AGENT_RESULT_MR_URL="$PR_URL"

    COMMENT="## Enhancement summary

${SUMMARY:-_(the agent did not leave a summary)_}

**Verification:** the task, all file changes and this summary were produced
fully autonomously by \`${AGENT_TOOL:-copilot}\` (model \`${BYOK_ACTIVE_MODEL:-}\`) in YOLO/autopilot mode. No human was in the loop."
    api POST "/repos/${REPO}/issues/${PR_NUM}/comments" \
      -d "$(jq -n --arg b "$COMMENT" '{body:$b}')" >/dev/null || warn "comment failed"
    ok "Summary comment posted to PR #${PR_NUM}"
    ;;
esac

notify_hub "published" "branch=${BRANCH} mr=${AGENT_RESULT_MR_URL:-none}" || true
ok "Publish complete"
