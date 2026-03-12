#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

if [ $# -eq 0 ]; then
    echo -e "${RED}Error: Spec name required${NC}" >&2
    echo "Usage: $0 <spec-name>" >&2
    echo "Example: $0 add-auth-flow" >&2
    exit 1
fi

SPEC_NAME=$1
WORKTREE_PATH=".worktrees/${SPEC_NAME}"
BRANCH_NAME="spec/${SPEC_NAME}"

echo -e "${BLUE}Merging worktree for spec ${SPEC_NAME}...${NC}"

# Idempotency: if worktree/branch doesn't exist, warn and exit 0
if ! git branch --list "$BRANCH_NAME" | grep -q "$BRANCH_NAME"; then
    echo -e "${YELLOW}Warning: Branch ${BRANCH_NAME} does not exist. Nothing to merge.${NC}"
    exit 0
fi

# Attempt merge
if git merge "$BRANCH_NAME" --no-ff -m "Merge ${BRANCH_NAME}"; then
    echo -e "${GREEN}✓ Merge successful${NC}"

    # Remove worktree
    if [ -d "$WORKTREE_PATH" ] && git worktree list | grep -q "$WORKTREE_PATH"; then
        git worktree remove "$WORKTREE_PATH" 2>/dev/null || git worktree remove --force "$WORKTREE_PATH"
        echo -e "${GREEN}✓ Worktree removed${NC}"
    fi

    # Delete branch
    git branch -d "$BRANCH_NAME" 2>/dev/null
    echo -e "${GREEN}✓ Branch ${BRANCH_NAME} deleted${NC}"

    # Prune stale worktree entries
    git worktree prune
    echo -e "${GREEN}✓ Worktree entries pruned${NC}"
else
    # Merge failed — check for conflicts
    CONFLICTING_FILES=$(git diff --name-only --diff-filter=U 2>/dev/null)

    echo -e "${RED}✗ Merge conflict detected for spec ${SPEC_NAME}${NC}" >&2
    if [ -n "$CONFLICTING_FILES" ]; then
        echo -e "${RED}Conflicting files:${NC}" >&2
        echo "$CONFLICTING_FILES" | while read -r f; do
            echo -e "${RED}  - ${f}${NC}" >&2
        done
    fi

    # Abort the merge to restore clean state
    git merge --abort
    echo -e "${YELLOW}Merge aborted. Worktree preserved at ${WORKTREE_PATH} for manual resolution.${NC}" >&2
    exit 1
fi
