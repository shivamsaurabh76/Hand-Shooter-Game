# Hand Gun Shooting Game — Children Edition

An AI-powered computer vision shooting game for kids using hand gestures.

## Overview

Players aim by moving their open hand and "shoot" by clenching their fist. The game uses MediaPipe for real-time hand tracking via the browser's webcam.

## Tech Stack

- **Framework:** Streamlit (Python)
- **Computer Vision:** MediaPipe HandLandmarker + OpenCV (headless)
- **Video Streaming:** streamlit-webrtc (WebRTC)
- **Audio:** Web Audio API (browser-side synthesis)
- **Numerics:** NumPy

## Project Structure

```
app/
  main.py              # Streamlit entry point, UI, WebRTC bridge, sound engine
  game.py              # Core game logic: HandTrackingGame, GestureDetector, physics
  hand_landmarker.task # MediaPipe AI model weights
assets/
  hand_landmarker.task # Backup model asset
.streamlit/
  config.toml          # Streamlit server config (port 5000, 0.0.0.0)
config/
  streamlit.toml       # (Legacy) Streamlit config
requirements.txt       # Python dependencies
packages.txt           # System-level apt dependencies (for OpenCV/MediaPipe)
```

## Running the App

```bash
streamlit run app/main.py
```

Runs on port **5000**, bound to `0.0.0.0`.

## Game Modes

- **Classic** — 30s, 5 balls, +2s per hit
- **Time Attack** — 60s fixed, 7 fast balls
- **Practice** — No timer, 3 big slow balls

## Gestures

1. Open hand flat → aim
2. Move hand to target
3. Squeeze fist → shoot

## Deployment

- Target: **autoscale**
- Run command: `streamlit run app/main.py --server.port=5000 --server.address=0.0.0.0`
