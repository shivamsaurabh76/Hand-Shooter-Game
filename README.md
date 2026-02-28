# 🎯 Hand Gun Shooting Game
### AI + Computer Vision — Children Edition

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
[![CI](https://github.com/YOUR_USERNAME/hand-shooter-game/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/hand-shooter-game/actions)

> Point your hand at the camera, **open** your hand to aim, **squeeze** your fist to shoot!  
> Works on mobile, tablet, laptop, and desktop. No controller or joystick needed.

---

## 🎮 Game Modes

| Mode | Timer | Balls | Difficulty |
|------|-------|-------|------------|
| 🎮 Classic | 30s + 2s/hit | 5 | ⭐⭐ |
| ⏱ Time Attack | 60s fixed | 7 fast | ⭐⭐⭐ |
| 🎯 Practice | No timer | 3 big slow | ⭐ |

---

## 📁 Project Structure

```
hand-shooter-game/
│
├── app/
│   ├── main.py              ← Streamlit UI (responsive, production-ready)
│   └── game.py              ← HandTrackingGame engine (MediaPipe + OpenCV)
│
├── assets/
│   └── hand_landmarker.task ← MediaPipe model file
│
├── config/
│   └── streamlit.toml       ← Streamlit config reference copy
│
├── .streamlit/
│   ├── config.toml          ← Streamlit Cloud reads this automatically
│   └── secrets.toml.example ← Template for secrets (never commit real secrets)
│
├── .github/
│   └── workflows/
│       └── ci.yml           ← GitHub Actions CI (lint + import check)
│
├── requirements.txt         ← All Python dependencies (pinned)
├── packages.txt             ← System-level packages for Streamlit Cloud
├── .gitignore
├── .env.example             ← Environment variable template
└── README.md
```

---

## 🚀 Deploy to Streamlit Cloud (FREE — Recommended)

Streamlit Cloud is the **best and easiest** option for this project.  
It's free, supports WebRTC, and auto-redeploys on every `git push`.

### Step 1 — Push to GitHub

Open **Git Bash** on your laptop:

```bash
# 1. Navigate to your extracted project folder
cd path/to/hand-shooter-game

# 2. Initialise git
git init

# 3. Add all files
git add .

# 4. First commit
git commit -m "🎯 Initial commit — Hand Shooter Game"

# 5. Create a new repo on github.com first, then:
git remote add origin https://github.com/YOUR_USERNAME/hand-shooter-game.git
git branch -M main
git push -u origin main
```

### Step 2 — Deploy on Streamlit Cloud

1. Go to **[share.streamlit.io](https://share.streamlit.io)** and sign in with GitHub
2. Click **"New app"**
3. Select your repository: `YOUR_USERNAME/hand-shooter-game`
4. Set **Main file path**: `app/main.py`
5. Click **Deploy!**
6. Wait ~3 minutes for the first build — done! 🎉

> **Your live link** will be:  
> `https://YOUR_USERNAME-hand-shooter-game-appmain-XXXX.streamlit.app`

### Step 3 — Auto-redeploy

Every `git push` to `main` automatically triggers a redeploy on Streamlit Cloud.  
No extra steps needed.

---

## 💻 Run Locally

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/hand-shooter-game.git
cd hand-shooter-game

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run
streamlit run app/main.py
```

Open `http://localhost:8501` in your browser.

---

## 📱 Mobile / Tablet Tips

- Use **landscape orientation** for best experience
- Allow **camera permission** when prompted
- Use **front camera** (selfie camera) — the app requests it automatically
- Good lighting on your hand makes detection much more accurate
- Start with **🎯 Practice** mode to learn the gestures

---

## 🔧 Configuration

All Streamlit settings live in `.streamlit/config.toml`.  
Theme colors, server settings, and performance tuning are pre-configured for production.

For custom WebRTC TURN servers (needed for some corporate networks):
1. Copy `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml`
2. Fill in your TURN server credentials
3. Never commit `secrets.toml` to git

---

## 🛠 Tech Stack

| Component | Library |
|-----------|---------|
| Web framework | Streamlit |
| WebRTC streaming | streamlit-webrtc |
| Hand AI | MediaPipe HandLandmarker |
| Frame processing | OpenCV (headless) |
| Numerics / audio | NumPy |
| Video codec | PyAV (av) |

---

## 📄 License

MIT — free to use, modify, and share.
