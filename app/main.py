"""
Hand Gun Shooting Game — Production Streamlit App
==================================================
Responsive, mobile-friendly, production-grade wrapper.
Run:  streamlit run app/main.py
"""

from __future__ import annotations

import threading
import av
import streamlit as st
from streamlit_webrtc import WebRtcMode, VideoProcessorBase, webrtc_streamer

from game import HandTrackingGame

# ── Page config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="🎯 Hand Shooter — Children Edition",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "🎯 Hand Gun Shooting Game — AI + Computer Vision, Children Edition",
    },
)

# ── Responsive CSS (mobile / tablet / desktop) ────────────────────────
st.markdown("""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Nunito:wght@400;700;800&display=swap');

/* ── Root palette ── */
:root {
  --gold:   #FFD700;
  --green:  #39FF14;
  --bg:     #0a0a14;
  --panel:  #14141f;
  --border: rgba(255,215,0,0.35);
  --text:   #e8e8f0;
  --radius: 14px;
}

/* ── Global reset ── */
html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  color: var(--text);
  font-family: 'Nunito', sans-serif;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"]   { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
.block-container {
  padding: clamp(0.5rem, 2vw, 1.5rem) clamp(0.5rem, 3vw, 2rem) !important;
  max-width: 800px !important;
}

/* ── Hero banner ── */
.hero {
  text-align: center;
  padding: clamp(0.6rem,2vw,1.2rem) 0 clamp(0.4rem,1vw,0.8rem);
}
.hero h1 {
  font-family: 'Orbitron', sans-serif;
  font-size: clamp(1.4rem, 5vw, 2.6rem);
  font-weight: 900;
  background: linear-gradient(135deg, #FFD700 30%, #FF8C00 70%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 0.04em;
  margin: 0 0 4px;
  text-shadow: none;
  line-height: 1.15;
}
.hero .subtitle {
  font-size: clamp(0.78rem, 2.5vw, 1rem);
  color: rgba(255,255,255,0.55);
  margin: 0 0 6px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.hero .tagline {
  display: inline-block;
  background: rgba(57,255,20,0.12);
  border: 1px solid rgba(57,255,20,0.4);
  border-radius: 20px;
  padding: 4px 14px;
  font-size: clamp(0.72rem, 2vw, 0.88rem);
  color: var(--green);
  font-weight: 700;
  letter-spacing: 0.06em;
}

/* ── Divider ── */
.divider {
  border: none;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--gold), transparent);
  margin: 6px 0 12px;
}

/* ── Mode buttons ── */
.stButton > button {
  background: var(--panel) !important;
  color: var(--text) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  font-family: 'Nunito', sans-serif !important;
  font-size: clamp(0.78rem, 2.2vw, 0.92rem) !important;
  font-weight: 700 !important;
  padding: clamp(0.45rem,1.5vw,0.7rem) clamp(0.5rem,2vw,1rem) !important;
  width: 100% !important;
  transition: all 0.18s ease !important;
  white-space: normal !important;
  height: auto !important;
  min-height: 52px !important;
  line-height: 1.3 !important;
}
.stButton > button:hover {
  background: rgba(255,215,0,0.10) !important;
  border-color: var(--gold) !important;
  color: var(--gold) !important;
  transform: translateY(-1px);
  box-shadow: 0 4px 18px rgba(255,215,0,0.18) !important;
}
.stButton > button:active { transform: translateY(0); }

/* ── Section heading ── */
.section-title {
  font-family: 'Orbitron', sans-serif;
  font-size: clamp(0.78rem, 2.5vw, 0.95rem);
  letter-spacing: 0.12em;
  color: var(--gold);
  text-transform: uppercase;
  margin: 10px 0 6px;
}

/* ── Info cards ── */
.info-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: clamp(0.6rem,2vw,1rem) clamp(0.8rem,2.5vw,1.2rem);
  margin: 6px 0;
  font-size: clamp(0.78rem, 2vw, 0.88rem);
  line-height: 1.65;
}
.info-card b { color: var(--gold); }
.info-card .green { color: var(--green); }

/* ── Step pills ── */
.steps {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin: 8px 0;
}
.step {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255,215,0,0.08);
  border: 1px solid var(--border);
  border-radius: 30px;
  padding: 5px 12px;
  font-size: clamp(0.72rem, 1.8vw, 0.82rem);
  font-weight: 700;
  white-space: nowrap;
}
.step .num {
  background: var(--gold);
  color: #000;
  border-radius: 50%;
  width: 20px; height: 20px;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.72rem;
  font-family: 'Orbitron', sans-serif;
}

/* ── Mode table ── */
.mode-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin: 8px 0;
}
.mode-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 10px;
  padding: 10px 10px 8px;
  text-align: center;
  font-size: clamp(0.68rem, 1.8vw, 0.78rem);
  line-height: 1.5;
}
.mode-card .icon { font-size: clamp(1.3rem, 3vw, 1.7rem); }
.mode-card .name { font-weight: 800; color: var(--gold); display: block; margin: 2px 0 1px; }
.mode-card .diff { color: var(--green); }

/* ── WebRTC container ── */
[data-testid="stVerticalBlock"] > div > div > div > video {
  border-radius: var(--radius);
  border: 2px solid var(--border);
}

/* ── Expander ── */
[data-testid="stExpander"] {
  background: var(--panel) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
}
[data-testid="stExpander"] summary {
  font-weight: 700;
  color: var(--gold);
  font-size: clamp(0.82rem, 2.2vw, 0.95rem);
}

/* ── st.info ── */
[data-testid="stAlert"] {
  background: rgba(57,255,20,0.07) !important;
  border: 1px solid rgba(57,255,20,0.3) !important;
  border-radius: var(--radius) !important;
  font-size: clamp(0.78rem, 2vw, 0.88rem);
}

/* ── Mobile: stack WebRTC full-width ── */
@media (max-width: 600px) {
  .mode-grid { grid-template-columns: 1fr; }
  .steps { flex-direction: column; }
  .step { width: fit-content; }
}
@media (max-width: 400px) {
  .hero h1 { letter-spacing: 0; }
}
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>🎯 HAND SHOOTER</h1>
  <p class="subtitle">AI · Computer Vision · Children Edition</p>
  <span class="tagline">✋ Open hand to aim &nbsp;•&nbsp; ✊ Squeeze fist to shoot!</span>
</div>
<hr class="divider">
""", unsafe_allow_html=True)


# ── Thread-safe processor ─────────────────────────────────────────────

class GameProcessor(VideoProcessorBase):
    """
    Bridge between streamlit-webrtc and HandTrackingGame.
    Thread-safe: all game mutations go through self.lock.
    """
    def __init__(self) -> None:
        self.game            = HandTrackingGame(width=640, height=480)
        self.lock            = threading.Lock()
        self._pending_mode: str | None = None
        self._pending_reset: bool      = False

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        with self.lock:
            if self._pending_mode is not None:
                self.game._start_game(self._pending_mode)
                self._pending_mode = None
            if self._pending_reset:
                self.game.reset()
                self._pending_reset = False
            img = frame.to_ndarray(format="bgr24")
            out = self.game.process_frame(img)
        return av.VideoFrame.from_ndarray(out, format="bgr24")


# ── WebRTC streamer ───────────────────────────────────────────────────

ctx = webrtc_streamer(
    key="hand-shooter-game",
    mode=WebRtcMode.SENDRECV,
    video_processor_factory=GameProcessor,
    media_stream_constraints={
        "video": {
            "width":     {"ideal": 640, "max": 1280},
            "height":    {"ideal": 480, "max": 720},
            "facingMode": "user",          # front camera on mobile
        },
        "audio": False,
    },
    async_processing=True,
    rtc_configuration={
        "iceServers": [
            {"urls": ["stun:stun.l.google.com:19302"]},
            {"urls": ["stun:stun1.l.google.com:19302"]},
            {"urls": ["stun:stun2.l.google.com:19302"]},
        ]
    },
)


# ── Game Mode Controls ────────────────────────────────────────────────

if ctx.state.playing and ctx.video_processor:
    st.markdown('<p class="section-title">🎮 Choose Game Mode</p>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button(
            "🎮 Classic\n30s · 5 balls · +2s/hit",
            use_container_width=True,
            help="30 seconds  •  +2 s per hit  •  5 bouncing balls",
        ):
            with ctx.video_processor.lock:
                ctx.video_processor._pending_mode = "classic"

    with c2:
        if st.button(
            "⏱ Time Attack\n60s · 7 balls · no bonus",
            use_container_width=True,
            help="60 seconds fixed  •  7 fast balls  •  max your score!",
        ):
            with ctx.video_processor.lock:
                ctx.video_processor._pending_mode = "time_attack"

    with c3:
        if st.button(
            "🎯 Practice\nNo timer · 3 big balls",
            use_container_width=True,
            help="No timer  •  3 huge slow balls  •  perfect for beginners & tiny hands",
        ):
            with ctx.video_processor.lock:
                ctx.video_processor._pending_mode = "practice"

    if st.button("🔄 Back to Menu", use_container_width=True):
        with ctx.video_processor.lock:
            ctx.video_processor._pending_reset = True


# ── Quick-start guide ─────────────────────────────────────────────────
with st.expander("📖 How to Play — Easy Guide for Kids & Parents!", expanded=not ctx.state.playing):
    st.markdown("""
<div class="info-card">
  <b>👋 The Gesture is SUPER SIMPLE:</b><br><br>
  <div class="steps">
    <div class="step"><span class="num">1</span> 🖐 Open your hand flat</div>
    <div class="step"><span class="num">2</span> 🎯 Move hand to aim at a ball</div>
    <div class="step"><span class="num">3</span> ✊ Squeeze your fist — <span class="green">💥 BOOM!</span></div>
  </div>
  <br>
  <b>💡 Tips for best results:</b><br>
  • Good lighting on your hand is key<br>
  • Keep hand 30–60 cm from camera<br>
  • On phone/tablet: use the <b>front camera</b> in landscape mode<br>
  • Even a 3-year-old can open and close their hand!
</div>

<br>

<div class="mode-grid">
  <div class="mode-card">
    <span class="icon">🎮</span>
    <span class="name">Classic</span>
    30s + 2s/hit<br>5 balls<br><span class="diff">⭐⭐</span>
  </div>
  <div class="mode-card">
    <span class="icon">⏱</span>
    <span class="name">Time Attack</span>
    60s fixed<br>7 fast balls<br><span class="diff">⭐⭐⭐</span>
  </div>
  <div class="mode-card">
    <span class="icon">🎯</span>
    <span class="name">Practice</span>
    No timer<br>3 big slow balls<br><span class="diff">⭐</span>
  </div>
</div>

<br>

<div class="info-card">
  <b>🏆 Scoring:</b><br>
  • Smaller balls → more points (1–4 pts)<br>
  • Hit multiple in a row → <span class="green"><b>Combo multiplier up to ×5!</b></span><br>
  • Miss a shot → combo resets to zero
</div>
""", unsafe_allow_html=True)

# ── Footer tip ────────────────────────────────────────────────────────
st.info(
    "💡 **Best played** with good lighting. "
    "Start with **🎯 Practice** mode! "
    "On phone/tablet, rotate to **landscape** for the best experience."
)

st.markdown(
    '<p style="text-align:center;font-size:0.72rem;color:rgba(255,255,255,0.25);margin-top:8px;">'
    "⚙️ AI processing via MediaPipe HandLandmarker · All computation server-side · No data stored"
    "</p>",
    unsafe_allow_html=True,
)
