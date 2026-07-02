#!/usr/bin/env bash
# Usage: bash scripts/new-handoff.sh [--dry-run] [flags] (run from repository root)
set -euo pipefail

DRY_RUN=false
NON_INTERACTIVE=false
PUSH_BRANCH=""
ISSUE_NUMBER=""
BRANCH=""
FILES_TO_MODIFY=()
FILES_NOT_TO_MODIFY=()
KEY_CONSTRAINTS=()
VERIFICATION=()
PR_EXPECTATIONS=()

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
    --issue)
      require_flag_value "$1" "${2:-}"
      NON_INTERACTIVE=true
      ISSUE_NUMBER="$2"
      shift 2
      ;;
    --branch)
      require_flag_value "$1" "${2:-}"
      NON_INTERACTIVE=true
      BRANCH="$2"
      shift 2
      ;;
    --file-to-modify)
      require_flag_value "$1" "${2:-}"
      NON_INTERACTIVE=true
      FILES_TO_MODIFY+=("$2")
      shift 2
      ;;
    --file-not-to-modify)
      require_flag_value "$1" "${2:-}"
      NON_INTERACTIVE=true
      FILES_NOT_TO_MODIFY+=("$2")
      shift 2
      ;;
    --constraint)
      require_flag_value "$1" "${2:-}"
      NON_INTERACTIVE=true
      KEY_CONSTRAINTS+=("$2")
      shift 2
      ;;
    --verify)
      require_flag_value "$1" "${2:-}"
      NON_INTERACTIVE=true
      VERIFICATION+=("$2")
      shift 2
      ;;
    --pr-expectation)
      require_flag_value "$1" "${2:-}"
      NON_INTERACTIVE=true
      PR_EXPECTATIONS+=("$2")
      shift 2
      ;;
    --push)
      NON_INTERACTIVE=true
      if [[ "$PUSH_BRANCH" == "false" ]]; then
        usage_error "--push and --no-push cannot both be supplied."
      fi
      PUSH_BRANCH=true
      shift
      ;;
    --no-push)
      NON_INTERACTIVE=true
      if [[ "$PUSH_BRANCH" == "true" ]]; then
        usage_error "--push and --no-push cannot both be supplied."
      fi
      PUSH_BRANCH=false
      shift
      ;;
    *)
      usage_error "unrecognized argument: $1"
      ;;
  esac
done

validate_inputs() {
  [[ -n "$ISSUE_NUMBER" ]] || usage_error "issue is required."
  [[ -n "$BRANCH" ]] || usage_error "branch is required."
  [[ ${#FILES_TO_MODIFY[@]} -gt 0 ]] || usage_error "at least one file to modify is required."
  [[ ${#FILES_NOT_TO_MODIFY[@]} -gt 0 ]] || usage_error "at least one file not to modify is required."
  [[ ${#KEY_CONSTRAINTS[@]} -gt 0 ]] || usage_error "at least one key constraint is required."
  [[ ${#VERIFICATION[@]} -gt 0 ]] || usage_error "at least one verification command is required."
  [[ ${#PR_EXPECTATIONS[@]} -gt 0 ]] || usage_error "at least one PR expectation is required."
}

render_handoff() {
  local checkout_branch="$1"

  echo "## Implementation Handoff"
  echo
  echo "Issue: #$ISSUE_NUMBER - $ISSUE_TITLE"
  echo "Issue URL: $ISSUE_URL"
  echo "Branch: $BRANCH"
  echo 'Checkout confirmation: The repository is currently checked out on `'"$checkout_branch"'`.'
  echo "Files to Modify:"
  for item in "${FILES_TO_MODIFY[@]}"; do
    echo "- $item"
  done
  echo "Files Not to Modify:"
  for item in "${FILES_NOT_TO_MODIFY[@]}"; do
    echo "- $item"
  done
  echo "Key Constraints:"
  for item in "${KEY_CONSTRAINTS[@]}"; do
    echo "- $item"
  done
  echo "Acceptance Criteria:"
  echo "- See Issue #$ISSUE_NUMBER: $ISSUE_URL"
  echo "Verification:"
  for item in "${VERIFICATION[@]}"; do
    echo "- $item"
  done
  echo "PR Expectations:"
  for item in "${PR_EXPECTATIONS[@]}"; do
    echo "- $item"
  done
}

require_gh() {
  if ! command -v gh &>/dev/null; then
    echo "Error: gh CLI is not installed. Install it from https://cli.github.com and authenticate with 'gh auth login'." >&2
    exit 1
  fi
}

if [[ "$NON_INTERACTIVE" == false ]]; then
  require_gh
fi

if [[ ! -f "CLAUDE.md" || ! -f "AGENTS.md" || ! -d ".git" ]]; then
  echo "Error: run this script from the repository root." >&2
  exit 1
fi

REPO_ROOT=$(git rev-parse --show-toplevel)
CURRENT_DIR=$(pwd -P)
if [[ "$REPO_ROOT" != "$CURRENT_DIR" ]]; then
  echo "Error: run this script from the repository root." >&2
  exit 1
fi

if [[ "$NON_INTERACTIVE" == false && "$DRY_RUN" == false ]] && [[ -n "$(git status --porcelain)" ]]; then
  echo "Error: working tree is dirty. Commit, stash, or discard changes before creating a handoff branch." >&2
  exit 1
fi

if [[ "$NON_INTERACTIVE" == false ]]; then
  echo "New Implementation Handoff" >&2
  echo "--------------------------" >&2
  echo >&2

  read -r -p "Issue number: " ISSUE_NUMBER
  [[ -z "$ISSUE_NUMBER" ]] && { echo "Error: issue number is required." >&2; exit 1; }

  read -r -p "Branch: " BRANCH
  [[ -z "$BRANCH" ]] && { echo "Error: branch is required." >&2; exit 1; }

  if [[ "$DRY_RUN" == false ]] && git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    echo "Error: branch already exists: $BRANCH" >&2
    exit 1
  fi

  echo "Files to modify (one path per line, blank line to finish):" >&2
  while true; do
    read -r -p "  - " item
    [[ -z "$item" ]] && break
    FILES_TO_MODIFY+=("$item")
  done
  [[ ${#FILES_TO_MODIFY[@]} -eq 0 ]] && { echo "Error: at least one file to modify is required." >&2; exit 1; }

  echo "Files not to modify (one path per line, blank line to finish):" >&2
  while true; do
    read -r -p "  - " item
    [[ -z "$item" ]] && break
    FILES_NOT_TO_MODIFY+=("$item")
  done
  [[ ${#FILES_NOT_TO_MODIFY[@]} -eq 0 ]] && { echo "Error: at least one file not to modify is required." >&2; exit 1; }

  echo "Key constraints (one item per line, blank line to finish):" >&2
  while true; do
    read -r -p "  - " item
    [[ -z "$item" ]] && break
    KEY_CONSTRAINTS+=("$item")
  done
  [[ ${#KEY_CONSTRAINTS[@]} -eq 0 ]] && { echo "Error: at least one key constraint is required." >&2; exit 1; }

  echo "Verification commands (one command per line, blank line to finish):" >&2
  while true; do
    read -r -p "  - " item
    [[ -z "$item" ]] && break
    VERIFICATION+=("$item")
  done
  [[ ${#VERIFICATION[@]} -eq 0 ]] && { echo "Error: at least one verification command is required." >&2; exit 1; }

  echo "PR expectations (one item per line, blank line to finish):" >&2
  while true; do
    read -r -p "  - " item
    [[ -z "$item" ]] && break
    PR_EXPECTATIONS+=("$item")
  done
  [[ ${#PR_EXPECTATIONS[@]} -eq 0 ]] && { echo "Error: at least one PR expectation is required." >&2; exit 1; }
else
  validate_inputs
  require_gh

  if [[ "$DRY_RUN" == false ]] && [[ -n "$(git status --porcelain)" ]]; then
    echo "Error: working tree is dirty. Commit, stash, or discard changes before creating a handoff branch." >&2
    exit 1
  fi

  if [[ "$DRY_RUN" == false ]] && git show-ref --verify --quiet "refs/heads/$BRANCH"; then
    echo "Error: branch already exists: $BRANCH" >&2
    exit 1
  fi
fi

ISSUE_METADATA=$(gh issue view "$ISSUE_NUMBER" --json number,title,url --template '{{.number}}{{"\n"}}{{.title}}{{"\n"}}{{.url}}{{"\n"}}')
ISSUE_NUMBER=$(printf "%s" "$ISSUE_METADATA" | sed -n '1p')
ISSUE_TITLE=$(printf "%s" "$ISSUE_METADATA" | sed -n '2p')
ISSUE_URL=$(printf "%s" "$ISSUE_METADATA" | sed -n '3p')

[[ -z "$ISSUE_TITLE" ]] && { echo "Error: could not retrieve issue title from gh issue view." >&2; exit 1; }
[[ -z "$ISSUE_URL" ]] && { echo "Error: could not retrieve issue URL from gh issue view." >&2; exit 1; }

if [[ "$DRY_RUN" == false ]]; then
  git fetch origin main >&2
  git checkout main >&2
  git pull --ff-only origin main >&2
  git checkout -b "$BRANCH" >&2

  if [[ "$NON_INTERACTIVE" == true ]]; then
    [[ "$PUSH_BRANCH" == "true" ]] && git push -u origin "$BRANCH" >&2
  else
    read -r -p "Push branch to origin? [y/N]: " PUSH_BRANCH
    case "$PUSH_BRANCH" in
      y|Y|yes|YES)
      git push -u origin "$BRANCH" >&2
      ;;
    esac
  fi
fi

CHECKED_OUT_BRANCH=$(git branch --show-current)
if [[ "$DRY_RUN" == false && "$CHECKED_OUT_BRANCH" != "$BRANCH" ]]; then
  echo "Error: expected to be checked out on $BRANCH, but current branch is $CHECKED_OUT_BRANCH." >&2
  exit 1
fi

CHECKOUT_BRANCH="$BRANCH"
if [[ "$DRY_RUN" == false ]]; then
  CHECKOUT_BRANCH="$CHECKED_OUT_BRANCH"
fi

if [[ "$DRY_RUN" == true ]]; then
  echo >&2
  echo "Dry run: branch was not created and no GitHub writes were made." >&2
  echo >&2
else
  echo >&2
fi

render_handoff "$CHECKOUT_BRANCH"
