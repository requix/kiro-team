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

# Idempotency: if worktree already exists, print path and exit 0
if [ -d "$WORKTREE_PATH" ] && git worktree list | grep -q "$WORKTREE_PATH"; then
    echo -e "${YELLOW}Worktree already exists at ${WORKTREE_PATH}${NC}" >&2
    echo "$(pwd)/${WORKTREE_PATH}"
    exit 0
fi

echo -e "${BLUE}Creating worktree for spec ${SPEC_NAME}...${NC}" >&2

# If branch already exists but worktree doesn't, remove the stale branch
if git branch --list "$BRANCH_NAME" | grep -q "$BRANCH_NAME"; then
    echo -e "${YELLOW}Removing stale branch ${BRANCH_NAME}...${NC}" >&2
    git branch -D "$BRANCH_NAME" 2>/dev/null
fi

# Create the worktree on a new branch
OUTPUT=$(git worktree add "$WORKTREE_PATH" -b "$BRANCH_NAME" 2>&1)
EXIT_CODE=$?
echo "$OUTPUT" | grep -v "^$" >&2
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Worktree created at ${WORKTREE_PATH} on branch ${BRANCH_NAME}${NC}" >&2
    echo "$(pwd)/${WORKTREE_PATH}"
else
    echo -e "${RED}Error: Failed to create worktree for spec ${SPEC_NAME}${NC}" >&2
    exit 1
fi
