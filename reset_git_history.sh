#!/usr/bin/env bash

set -euo pipefail

echo "Preparing to squash repository history..."

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Error: run this script inside a Git repository." >&2
    exit 1
fi

current_branch="$(git symbolic-ref --short HEAD 2>/dev/null || true)"
if [[ -z "$current_branch" ]]; then
    echo "Error: could not determine current branch. Check out a branch and retry." >&2
    exit 1
fi

# Snapshot tracked changes, keeping untracked files untouched.
# Drop tracked IntelliJ configuration from the index but leave files locally.
git rm -r --cached .idea >/dev/null 2>&1 || true

if git status --porcelain | grep -v '^??' >/dev/null 2>&1; then
    echo "Committing tracked changes..."
    git add -u
    git commit -m "chore: checkpoint before history reset"
fi

# Ensure the working tree is clean before rewriting history.
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "Error: working tree is not clean after checkpoint commit. Aborting." >&2
    exit 1
fi

tree_sha="$(git rev-parse 'HEAD^{tree}')"
reset_message="chore: reset history"
new_commit="$(git commit-tree "$tree_sha" -m "$reset_message")"
git reset --hard "$new_commit"

remote="${1:-}"
if [[ -z "$remote" ]]; then
    remote="$(git remote | head -n1 || true)"
fi

if [[ -n "$remote" ]]; then
    # Ensure any reintroduced IntelliJ files are untracked before the force push.
    git rm -r --cached .idea >/dev/null 2>&1 || true

    echo "Force pushing rewritten history to remote '$remote'..."
    git push --force "$remote" "$current_branch"
else
    echo "No remote configured. Local history rewritten only."
fi

echo "History reset complete. Untracked files were left untouched."
