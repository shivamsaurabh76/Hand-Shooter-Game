#!/bin/bash
# Run this once in the Shell tab to push code to GitHub
# The GITHUB_TOKEN secret must be set in Replit Secrets first

if [ -z "$GITHUB_TOKEN" ]; then
  echo "ERROR: GITHUB_TOKEN secret not found."
  exit 1
fi

git remote set-url origin "https://shivamsaurabh76:${GITHUB_TOKEN}@github.com/shivamsaurabh76/Hand-Shooter-Game.git"
git add -A
git commit -m "Deploy-ready: pure browser game, no WebRTC, Streamlit Cloud compatible" --allow-empty
git push origin main

echo ""
echo "Done! Now go to https://share.streamlit.io and deploy your app."
