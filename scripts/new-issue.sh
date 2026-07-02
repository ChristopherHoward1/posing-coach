#!/usr/bin/env bash
# Usage: bash scripts/new-issue.sh [--dry-run] [flags] (run from repository root)
set -euo pipefail

DRY_RUN=false
NON_INTERACTIVE=false
TITLE=""
GOAL=""
BACKGROUND=""
IN_SCOPE=()
OUT_SCOPE=()
AC=()

usage_error() {
  local message="$1"

  echo "Error: $message" >&2
  exit 1
}

require_flag_value() {
  local flag="$1"
  local value="${2:-}"

  [[ -n "$value" ]] || usage_error "$flag requires a value."
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --title)
      require_flag_value "$1" "${2:-}"
      NON_INTERACTIVE=true
      TITLE="$2"
      shift 2
      ;;
    --goal)
      require_flag_value "$1" "${2:-}"
      NON_INTERACTIVE=true
      GOAL="$2"
      shift 2
      ;;
    --background)
      require_flag_value "$1" "${2:-}"
      NON_INTERACTIVE=true
      BACKGROUND="$2"
      shift 2
      ;;
    --in-scope)
      require_flag_value "$1" "${2:-}"
      NON_INTERACTIVE=true
      IN_SCOPE+=("$2")
      shift 2
      ;;
    --out-of-scope)
      require_flag_value "$1" "${2:-}"
      NON_INTERACTIVE=true
      OUT_SCOPE+=("$2")
      shift 2
      ;;
    --acceptance-criterion)
      require_flag_value "$1" "${2:-}"
      NON_INTERACTIVE=true
      AC+=("$2")
      shift 2
      ;;
    *)
      usage_error "unrecognized argument: $1"
      ;;
  esac
done

validate_inputs() {
  [[ -n "$TITLE" ]] || usage_error "title is required."
  [[ -n "$GOAL" ]] || usage_error "goal is required."
  [[ ${#AC[@]} -gt 0 ]] || usage_error "at least one acceptance criterion is required."
}

render_body() {
  BODY=""
  BODY+="## Goal"$'\n'
  BODY+=$'\n'
  BODY+="$GOAL"$'\n'
  BODY+=$'\n'

  if [[ -n "$BACKGROUND" ]]; then
    BODY+="## Background"$'\n'
    BODY+=$'\n'
    BODY+="$BACKGROUND"$'\n'
    BODY+=$'\n'
  fi

  BODY+="## Scope"$'\n'
  BODY+=$'\n'
  BODY+="**In scope:**"$'\n'
  BODY+=$'\n'
  if [[ ${#IN_SCOPE[@]} -gt 0 ]]; then
    for item in "${IN_SCOPE[@]}"; do
      BODY+="- $item"$'\n'
    done
  fi
  BODY+=$'\n'
  BODY+="**Out of scope:**"$'\n'
  BODY+=$'\n'
  if [[ ${#OUT_SCOPE[@]} -gt 0 ]]; then
    for item in "${OUT_SCOPE[@]}"; do
      BODY+="- $item"$'\n'
    done
  fi
  BODY+=$'\n'

  BODY+="## Acceptance Criteria"$'\n'
  BODY+=$'\n'
  for item in "${AC[@]}"; do
    BODY+="- [ ] $item"$'\n'
  done
  BODY+=$'\n'

  BODY+="## Decomposition"$'\n'
  BODY+=$'\n'
  BODY+="_Add sub-tasks or recommended sequencing, if non-trivial. Remove this section if straightforward._"$'\n'
  BODY+=$'\n'

  BODY+="## Risks"$'\n'
  BODY+=$'\n'
  BODY+="_Known risks or dependencies worth flagging before implementation. Remove this section if none._"$'\n'
}

if [[ "$NON_INTERACTIVE" == false && "$DRY_RUN" == false ]] && ! command -v gh &>/dev/null; then
  echo "Error: gh CLI is not installed. Install it from https://cli.github.com and authenticate with 'gh auth login'." >&2
  exit 1
fi

TEMPLATE=".github/ISSUE_TEMPLATE/implementation.md"

if [[ ! -f "$TEMPLATE" ]]; then
  echo "Error: run this script from the repository root." >&2
  exit 1
fi

if [[ "$NON_INTERACTIVE" == false ]]; then
  echo "New Implementation Issue"
  echo "------------------------"
  echo

  read -r -p "Title: " TITLE
  [[ -z "$TITLE" ]] && { echo "Error: title is required." >&2; exit 1; }

  read -r -p "Goal (one sentence): " GOAL
  [[ -z "$GOAL" ]] && { echo "Error: goal is required." >&2; exit 1; }

  read -r -p "Background (optional, press Enter to skip): " BACKGROUND

  echo "In scope (one item per line, blank line to finish):"
  while true; do
    read -r -p "  - " item
    [[ -z "$item" ]] && break
    IN_SCOPE+=("$item")
  done

  echo "Out of scope (one item per line, blank line to finish):"
  while true; do
    read -r -p "  - " item
    [[ -z "$item" ]] && break
    OUT_SCOPE+=("$item")
  done

  echo "Acceptance criteria (one item per line, blank line to finish):"
  while true; do
    read -r -p "  - [ ] " item
    [[ -z "$item" ]] && break
    AC+=("$item")
  done
  [[ ${#AC[@]} -eq 0 ]] && { echo "Error: at least one acceptance criterion is required." >&2; exit 1; }
else
  validate_inputs
fi

if [[ "$NON_INTERACTIVE" == true && "$DRY_RUN" == false ]] && ! command -v gh &>/dev/null; then
  echo "Error: gh CLI is not installed. Install it from https://cli.github.com and authenticate with 'gh auth login'." >&2
  exit 1
fi

render_body

if [[ "$DRY_RUN" == true ]]; then
  echo
  echo "Dry run: GitHub Issue was not created."
  echo
  echo "Title: $TITLE"
  echo
  echo "$BODY"
  exit 0
fi

echo
echo "Creating GitHub Issue..."
ISSUE_URL=$(gh issue create --title "$TITLE" --body "$BODY")
echo
echo "Issue created: $ISSUE_URL"
