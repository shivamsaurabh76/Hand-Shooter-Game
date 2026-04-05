#!/bin/bash
set -e

if [ -z "$GITHUB_TOKEN" ]; then
  echo "ERROR: GITHUB_TOKEN secret not set."
  exit 1
fi

git remote set-url origin "https://shivamsaurabh76:${GITHUB_TOKEN}@github.com/shivamsaurabh76/Hand-Shooter-Game.git"

git add -A
git diff --cached --quiet && echo "Nothing to commit — already up to date." && exit 0

git commit -m "Fix: empty packages.txt, valid CI yaml, browser-based game"
git push origin main

echo ""
echo "Pushed successfully! Streamlit Cloud will redeploy in ~1 minute."
echo "Visit: https://hand-shooter-game.streamlit.app"
