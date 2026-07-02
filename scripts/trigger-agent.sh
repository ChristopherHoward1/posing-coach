#!/usr/bin/env bash
# Usage: bash scripts/trigger-agent.sh [--dry-run] <handoff-file> (run from repository root)
set -euo pipefail

DRY_RUN=false
HANDOFF=""

usage_error() {
  local message="$1"

  echo "Error: $message" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    -*)
      usage_error "unrecognized argument: $1"
      ;;
    *)
      if [[ -n "$HANDOFF" ]]; then
        usage_error "only one handoff file may be provided."
      fi
      HANDOFF="$1"
      shift
      ;;
  esac
done

[[ -n "$HANDOFF" ]] || usage_error "handoff file path is required."

if [[ ! -f "CLAUDE.md" || ! -f "AGENTS.md" || ! -d ".git" ]]; then
  echo "Error: run this script from the repository root." >&2
  exit 1
fi

REPO_ROOT=$(cd "$(git rev-parse --show-toplevel)" && pwd -P)
CURRENT_DIR=$(pwd -P)
if [[ "$REPO_ROOT" != "$CURRENT_DIR" ]]; then
  echo "Error: run this script from the repository root." >&2
  exit 1
fi

[[ -s "$HANDOFF" ]] || usage_error "handoff file does not exist or is empty: $HANDOFF"

if ! command -v codex &>/dev/null; then
  echo "Error: codex CLI is not installed." >&2
  exit 1
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Error: working tree is dirty. Commit, stash, or discard changes before triggering an agent run." >&2
  exit 1
fi

if [[ "$DRY_RUN" == true ]]; then
  echo "codex exec --sandbox workspace-write - < \"$HANDOFF\""
  exit 0
fi

codex exec --sandbox workspace-write - < "$HANDOFF"
