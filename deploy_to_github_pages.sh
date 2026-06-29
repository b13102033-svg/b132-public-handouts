#!/usr/bin/env bash
set -euo pipefail

REPO_NAME="${1:-b132-public-handouts}"
GH_BIN="${GH_BIN:-/tmp/b132_gh/gh_2.95.0_macOS_arm64/bin/gh}"

if [[ ! -x "$GH_BIN" ]]; then
  echo "GitHub CLI not found at $GH_BIN" >&2
  echo "Run the B132 setup step again to install gh, or set GH_BIN to another gh path." >&2
  exit 1
fi

if ! "$GH_BIN" auth status -h github.com >/dev/null 2>&1; then
  echo "GitHub CLI is not authenticated."
  echo "Run: $GH_BIN auth login --hostname github.com --git-protocol https --web --scopes repo,workflow"
  exit 2
fi

OWNER="$("$GH_BIN" api user --jq .login)"
FULL_NAME="$OWNER/$REPO_NAME"

git init -b main >/dev/null 2>&1 || true
git add index.html README.md longteng-vocab-king-unit50-54-review.html
git -c user.name='B132 Codex' -c user.email='b132-codex@example.invalid' commit -m 'Publish B132 public handouts' >/dev/null 2>&1 || true

if "$GH_BIN" repo view "$FULL_NAME" >/dev/null 2>&1; then
  echo "Using existing repository: $FULL_NAME"
  git remote remove origin >/dev/null 2>&1 || true
  git remote add origin "https://github.com/$FULL_NAME.git"
  git push -u origin main
else
  echo "Creating public repository: $FULL_NAME"
  "$GH_BIN" repo create "$FULL_NAME" --public --source=. --remote=origin --push
fi

set +e
"$GH_BIN" api "repos/$FULL_NAME/pages" \
  -X POST \
  -f source.branch=main \
  -f source.path=/ >/dev/null 2>&1
CREATE_STATUS=$?
set -e

if [[ "$CREATE_STATUS" -ne 0 ]]; then
  "$GH_BIN" api "repos/$FULL_NAME/pages" \
    -X PUT \
    -f source.branch=main \
    -f source.path=/ >/dev/null
fi

PAGES_URL="$("$GH_BIN" api "repos/$FULL_NAME/pages" --jq .html_url)"
echo "$PAGES_URL"
echo "${PAGES_URL%/}/longteng-vocab-king-unit50-54-review.html"
