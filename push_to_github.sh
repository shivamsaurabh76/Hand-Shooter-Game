#!/bin/bash
set -e

if [ -z "$GITHUB_TOKEN" ]; then
  echo "ERROR: GITHUB_TOKEN secret not set."
  exit 1
fi

git remote set-url origin "https://shivamsaurabh76:${GITHUB_TOKEN}@github.com/shivamsaurabh76/Hand-Shooter-Game.git"

# Stage any new local changes
git add -A

# Commit only if there is something new to commit
if git diff --cached --quiet; then
  echo "No new file changes to commit."
else
  git commit -m "Fix: empty packages.txt, valid CI yaml, browser-based game"
fi

# Always push — there may be already-committed local changes not yet on GitHub
AHEAD=$(git rev-list origin/main..HEAD --count 2>/dev/null || echo "unknown")
if [ "$AHEAD" = "0" ]; then
  echo "Already up to date with GitHub — nothing to push."
  exit 0
fi

echo "Pushing $AHEAD commit(s) to GitHub..."
git push origin main

echo ""
echo "Done! Streamlit Cloud will redeploy automatically in ~1 minute."
echo "Visit: https://hand-shooter-game.streamlit.app"
