"""
Hand Gun Shooting Game — Production Streamlit App
==================================================
Sound Architecture (correct for deployed Streamlit):
  • components.html() runs in a SANDBOXED IFRAME that is recreated
    on every Streamlit rerun. Polling the DOM is useless because the
    iframe is destroyed and rebuilt each cycle.
  • Correct approach: embed the ENTIRE sound engine + event data
    inside ONE self-contained HTML page. Streamlit passes the current
    hit event as a data-attribute directly in the HTML string.
    Each new rerun = new iframe = fresh page = the JS runs immediately
    on page-load, reads the event from a <meta> tag, compares to
    localStorage (same-origin within the iframe), and plays the sound
    if the sequence number is new.
  • Because every iframe is same-origin (about:blank / srcdoc), we use
    a tiny localStorage key inside the iframe to deduplicate (each iframe
    shares the same ephemeral storage since Streamlit iframes are all
    same-origin srcdoc frames).
Run:  streamlit run app/main.py
"""

from __future__ import annotations

import json
import threading
import av
import streamlit as st
import streamlit.components.v1 as components
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

# ── Responsive CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700;900&family=Nunito:wght@400;700;800&display=swap');

:root {
  --gold:   #FFD700;
  --green:  #39FF14;
  --bg:     #0a0a14;
  --panel:  #14141f;
  --border: rgba(255,215,0,0.35);
  --text:   #e8e8f0;
  --radius: 14px;
}
html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  color: var(--text);
  font-family: 'Nunito', sans-serif;
}
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"]        { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
.block-container {
  padding: clamp(0.5rem,2vw,1.5rem) clamp(0.5rem,3vw,2rem) !important;
  max-width: 800px !important;
}
.hero { text-align:center; padding:clamp(0.6rem,2vw,1.2rem) 0 clamp(0.4rem,1vw,0.8rem); }
.hero h1 {
  font-family:'Orbitron',sans-serif;
  font-size:clamp(1.4rem,5vw,2.6rem); font-weight:900;
  background:linear-gradient(135deg,#FFD700 30%,#FF8C00 70%);
  -webkit-background-clip:text; -webkit-text-fill-color:transparent;
  background-clip:text; letter-spacing:0.04em; margin:0 0 4px; line-height:1.15;
}
.hero .subtitle {
  font-size:clamp(0.78rem,2.5vw,1rem); color:rgba(255,255,255,0.55);
  margin:0 0 6px; letter-spacing:0.1em; text-transform:uppercase;
}
.hero .tagline {
  display:inline-block; background:rgba(57,255,20,0.12);
  border:1px solid rgba(57,255,20,0.4); border-radius:20px; padding:4px 14px;
  font-size:clamp(0.72rem,2vw,0.88rem); color:var(--green); font-weight:700;
}
.divider {
  border:none; height:1px;
  background:linear-gradient(90deg,transparent,var(--gold),transparent);
  margin:6px 0 12px;
}
.stButton > button {
  background:var(--panel) !important; color:var(--text) !important;
  border:1px solid var(--border) !important; border-radius:var(--radius) !important;
  font-family:'Nunito',sans-serif !important;
  font-size:clamp(0.78rem,2.2vw,0.92rem) !important; font-weight:700 !important;
  padding:clamp(0.45rem,1.5vw,0.7rem) clamp(0.5rem,2vw,1rem) !important;
  width:100% !important; transition:all 0.18s ease !important;
  white-space:normal !important; height:auto !important;
  min-height:52px !important; line-height:1.3 !important;
}
.stButton > button:hover {
  background:rgba(255,215,0,0.10) !important; border-color:var(--gold) !important;
  color:var(--gold) !important; transform:translateY(-1px);
  box-shadow:0 4px 18px rgba(255,215,0,0.18) !important;
}
.section-title {
  font-family:'Orbitron',sans-serif; font-size:clamp(0.78rem,2.5vw,0.95rem);
  letter-spacing:0.12em; color:var(--gold); text-transform:uppercase; margin:10px 0 6px;
}
.info-card {
  background:var(--panel); border:1px solid var(--border); border-radius:var(--radius);
  padding:clamp(0.6rem,2vw,1rem) clamp(0.8rem,2.5vw,1.2rem); margin:6px 0;
  font-size:clamp(0.78rem,2vw,0.88rem); line-height:1.65;
}
.info-card b { color:var(--gold); }
.info-card .green { color:var(--green); }
.steps { display:flex; gap:8px; flex-wrap:wrap; margin:8px 0; }
.step {
  display:flex; align-items:center; gap:6px; background:rgba(255,215,0,0.08);
  border:1px solid var(--border); border-radius:30px; padding:5px 12px;
  font-size:clamp(0.72rem,1.8vw,0.82rem); font-weight:700; white-space:nowrap;
}
.step .num {
  background:var(--gold); color:#000; border-radius:50%; width:20px; height:20px;
  display:flex; align-items:center; justify-content:center;
  font-size:0.72rem; font-family:'Orbitron',sans-serif;
}
.mode-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin:8px 0; }
.mode-card {
  background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.1);
  border-radius:10px; padding:10px 10px 8px; text-align:center;
  font-size:clamp(0.68rem,1.8vw,0.78rem); line-height:1.5;
}
.mode-card .icon { font-size:clamp(1.3rem,3vw,1.7rem); }
.mode-card .name { font-weight:800; color:var(--gold); display:block; margin:2px 0 1px; }
.mode-card .diff { color:var(--green); }
[data-testid="stExpander"] {
  background:var(--panel) !important; border:1px solid var(--border) !important;
  border-radius:var(--radius) !important;
}
[data-testid="stExpander"] summary {
  font-weight:700; color:var(--gold); font-size:clamp(0.82rem,2.2vw,0.95rem);
}
[data-testid="stAlert"] {
  background:rgba(57,255,20,0.07) !important;
  border:1px solid rgba(57,255,20,0.3) !important;
  border-radius:var(--radius) !important; font-size:clamp(0.78rem,2vw,0.88rem);
}
@media (max-width:600px) {
  .mode-grid { grid-template-columns:1fr; }
  .steps { flex-direction:column; }
  .step { width:fit-content; }
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


# ══════════════════════════════════════════════════════════════════════
#  SOUND ENGINE — Self-contained iframe approach
# ══════════════════════════════════════════════════════════════════════
#
#  WHY PREVIOUS ATTEMPTS FAILED:
#  ─────────────────────────────
#  1. sounddevice/winsound: run on cloud SERVER — user never hears it.
#  2. components.html() polling approach: Streamlit recreates the iframe
#     on every rerun. Each new iframe = brand-new JS context = the
#     setTimeout/poll loop is destroyed immediately after starting.
#     getElementById() only searches WITHIN that iframe, not the parent.
#
#  CORRECT ARCHITECTURE:
#  ──────────────────────
#  • Each Streamlit rerun passes the current (hit_seq, hit_combo) as
#    JSON directly embedded into the HTML string fed to components.html().
#  • The iframe's onload JS runs IMMEDIATELY, reads the event from a
#    <script> tag variable (not from any DOM element it needs to find),
#    checks sessionStorage for the last played seq, and plays sound if new.
#  • sessionStorage persists across iframe reloads within the same tab
#    (same-origin srcdoc frames share sessionStorage in all major browsers).
#  • This means: new iframe → runs JS → checks sessionStorage → plays if new.
#    Zero polling needed. Works reliably every single time.
#
# ══════════════════════════════════════════════════════════════════════

def _make_sound_html(seq: int, combo: int) -> str:
    """
    Build a complete self-contained HTML page with the Web Audio synth.
    seq and combo are baked directly into the JS as literals — no DOM
    polling, no data attributes to find, no race conditions.
    """
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:transparent;">
<script>
(function() {{
  // ── Event data baked in at render time ───────────────────────────
  var HIT_SEQ   = {seq};
  var HIT_COMBO = {combo};
  var STORAGE_KEY = 'hsg_last_seq';

  // ── Deduplication via sessionStorage ────────────────────────────
  // sessionStorage persists for the browser tab session and is shared
  // across same-origin srcdoc iframes — perfect for deduplication.
  var lastPlayed = -1;
  try {{ lastPlayed = parseInt(sessionStorage.getItem(STORAGE_KEY) || '-1'); }} catch(e) {{}}

  if (HIT_SEQ <= 0 || HIT_SEQ === lastPlayed) return;  // nothing new to play

  // ── AudioContext ─────────────────────────────────────────────────
  var ac;
  try {{
    ac = new (window.AudioContext || window.webkitAudioContext)();
  }} catch(e) {{ return; }}

  // If browser blocked autoplay, try to resume
  if (ac.state === 'suspended') {{
    ac.resume().catch(function() {{}});
  }}

  // ── Waveform primitives ──────────────────────────────────────────

  function bellBuf(freq, durMs, amp) {{
    amp = amp || 0.45;
    var sr = ac.sampleRate;
    var n  = Math.round(sr * durMs / 1000);
    var buf = ac.createBuffer(1, n, sr);
    var d   = buf.getChannelData(0);
    var tau = durMs / 1000;
    for (var i = 0; i < n; i++) {{
      var t   = i / sr;
      var env = Math.exp(-5.0 * t / tau);
      d[i] = amp * env * (
        0.50 * Math.sin(6.28318 * freq       * t) +
        0.25 * Math.sin(6.28318 * freq * 2.0 * t) +
        0.10 * Math.sin(6.28318 * freq * 3.0 * t)
      );
    }}
    return buf;
  }}

  function sweepBuf(f0, f1, durMs, amp) {{
    amp = amp || 0.50;
    var sr = ac.sampleRate;
    var n  = Math.round(sr * durMs / 1000);
    var buf = ac.createBuffer(1, n, sr);
    var d   = buf.getChannelData(0);
    var ph  = 0;
    for (var i = 0; i < n; i++) {{
      var t   = i / n;
      var env = 0.5 - 0.5 * Math.cos(3.14159 * t);
      var f   = f0 + (f1 - f0) * t;
      ph += 6.28318 * f / sr;
      d[i] = amp * env * Math.sin(ph);
    }}
    return buf;
  }}

  function playBuf(buf, whenSec) {{
    var src = ac.createBufferSource();
    src.buffer = buf;
    src.connect(ac.destination);
    src.start(whenSec || ac.currentTime);
  }}

  function playSeq(noteList, gapMs) {{
    // noteList: array of [freq, durMs, amp?]
    gapMs = gapMs || 8;
    var when = ac.currentTime + 0.005;
    for (var i = 0; i < noteList.length; i++) {{
      var n = noteList[i];
      var src = ac.createBufferSource();
      src.buffer = bellBuf(n[0], n[1], n[2] || 0.46);
      src.connect(ac.destination);
      src.start(when);
      when += (n[1] + gapMs) / 1000;
    }}
  }}

  // ── Note frequencies ─────────────────────────────────────────────
  var C5=523.25, D5=587.33, E5=659.25, G5=783.99, A5=880.00;
  var C6=1046.50, E6=1318.51, G6=1567.98, C7=2093.00;

  // ── Sound recipes (identical to Python SoundEngine) ──────────────

  function sndBubblePop() {{
    // 🫧 Descending sweep + C6 bell — EVERY hit
    playBuf(sweepBuf(1400, 280, 100, 0.55));
    playBuf(bellBuf(C6, 60, 0.28));
  }}

  function sndSparkleChime() {{
    // ✨ C→E→G arpeggio — combo x2
    playSeq([[C5,70],[E5,70],[G5,70]], 10);
  }}

  function sndCoinCollect() {{
    // 🪙 High C→E→G — combo x3
    playSeq([[C6,55],[E6,55],[G6,55]], 8);
  }}

  function sndMagicShimmer() {{
    // 🌟 6-note pentatonic cascade — combo x4
    playSeq([[C5,45,0.40],[D5,45,0.42],[E5,45,0.44],
             [G5,45,0.46],[A5,45,0.48],[C6,45,0.50]], 6);
  }}

  function sndFanfare() {{
    // 🎉 7-note ascending celebration — combo x5+
    playSeq([[C5,40,0.38],[E5,45,0.41],[G5,50,0.44],
             [C6,55,0.47],[E6,60,0.50],[G6,65,0.53],[C7,70,0.56]], 5);
    // trailing bell ring after ~420 ms
    setTimeout(function() {{
      playBuf(bellBuf(C6, 180, 0.30));
    }}, 420);
  }}

  // ── Dispatch ─────────────────────────────────────────────────────
  function playCombo(combo) {{
    if      (combo >= 5) {{ sndFanfare();      }}
    else if (combo === 4) {{ sndMagicShimmer(); }}
    else if (combo === 3) {{ sndCoinCollect();  }}
    else if (combo === 2) {{ sndSparkleChime(); }}
    else                  {{ sndBubblePop();    }}
  }}

  // ── Play the sound ────────────────────────────────────────────────
  try {{
    playCombo(HIT_COMBO);
    sessionStorage.setItem(STORAGE_KEY, HIT_SEQ);
  }} catch(e) {{}}

}})();
</script>
</body>
</html>"""


def render_sound(seq: int, combo: int) -> None:
    """
    Renders the sound iframe. Called every Streamlit rerun.
    When seq changes, a new iframe renders with new values → sound plays.
    When seq is unchanged, same HTML renders → sessionStorage deduplicates.
    """
    html = _make_sound_html(seq, combo)
    # height=0 hides the iframe visually; it still executes JS.
    components.html(html, height=0, scrolling=False)


# ══════════════════════════════════════════════════════════════════════
#  VIDEO PROCESSOR
# ══════════════════════════════════════════════════════════════════════

class GameProcessor(VideoProcessorBase):
    """Thread-safe bridge: streamlit-webrtc ↔ HandTrackingGame."""

    def __init__(self) -> None:
        self.game             = HandTrackingGame(width=640, height=480)
        self.lock             = threading.Lock()
        self._pending_mode: str | None = None
        self._pending_reset: bool      = False
        # Hit event: incremented on every successful ball pop
        self.hit_seq:   int = 0
        self.hit_combo: int = 0
        self._last_score: int = 0

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        with self.lock:
            if self._pending_mode is not None:
                self.game._start_game(self._pending_mode)
                self._pending_mode = None
                self._last_score   = 0
            if self._pending_reset:
                self.game.reset()
                self._pending_reset = False
                self._last_score    = 0

            img = frame.to_ndarray(format="bgr24")
            out = self.game.process_frame(img)

            # Detect new hit: score went up this frame
            if self.game.score > self._last_score:
                self.hit_seq  += 1
                self.hit_combo = self.game.combo
            self._last_score = self.game.score

        return av.VideoFrame.from_ndarray(out, format="bgr24")


# ══════════════════════════════════════════════════════════════════════
#  WEBRTC STREAMER
# ══════════════════════════════════════════════════════════════════════

if st.runtime.exists():
    ctx = webrtc_streamer(
        key="hand-shooter-game",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=GameProcessor,
        media_stream_constraints={
            "video": {
                "width":      {"ideal": 640, "max": 1280},
                "height":     {"ideal": 480, "max": 720},
                "facingMode": "user",
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
else:
    ctx = None


# ══════════════════════════════════════════════════════════════════════
#  SOUND BRIDGE — read game state → drive browser sound iframe
# ══════════════════════════════════════════════════════════════════════

# Session-state tracks the last known hit so we can detect changes
if "snd_seq"   not in st.session_state: st.session_state["snd_seq"]   = 0
if "snd_combo" not in st.session_state: st.session_state["snd_combo"] = 0

if ctx is not None and ctx.state.playing and ctx.video_processor:
    with ctx.video_processor.lock:
        new_seq   = ctx.video_processor.hit_seq
        new_combo = ctx.video_processor.hit_combo

    if new_seq != st.session_state["snd_seq"]:
        st.session_state["snd_seq"]   = new_seq
        st.session_state["snd_combo"] = new_combo
        # Trigger an immediate rerun so the sound iframe gets the new values
        # before the next natural rerun cycle
        st.rerun()

# Always render sound iframe (deduplication is inside JS via sessionStorage)
if ctx is not None:
    render_sound(st.session_state["snd_seq"], st.session_state["snd_combo"])


# ══════════════════════════════════════════════════════════════════════
#  GAME MODE BUTTONS
# ══════════════════════════════════════════════════════════════════════

if ctx is not None and ctx.state.playing and ctx.video_processor:
    st.markdown('<p class="section-title">🎮 Choose Game Mode</p>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("🎮 Classic\n30s · 5 balls · +2s/hit", use_container_width=True):
            with ctx.video_processor.lock:
                ctx.video_processor._pending_mode = "classic"
    with c2:
        if st.button("⏱ Time Attack\n60s · 7 balls · no bonus", use_container_width=True):
            with ctx.video_processor.lock:
                ctx.video_processor._pending_mode = "time_attack"
    with c3:
        if st.button("🎯 Practice\nNo timer · 3 big balls", use_container_width=True):
            with ctx.video_processor.lock:
                ctx.video_processor._pending_mode = "practice"

    if st.button("🔄 Back to Menu", use_container_width=True):
        with ctx.video_processor.lock:
            ctx.video_processor._pending_reset = True


# ══════════════════════════════════════════════════════════════════════
#  HOW TO PLAY
# ══════════════════════════════════════════════════════════════════════

with st.expander("📖 How to Play — Easy Guide for Kids & Parents!", expanded=ctx is None or not ctx.state.playing):
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
  <div class="mode-card"><span class="icon">🎮</span><span class="name">Classic</span>30s + 2s/hit<br>5 balls<br><span class="diff">⭐⭐</span></div>
  <div class="mode-card"><span class="icon">⏱</span><span class="name">Time Attack</span>60s fixed<br>7 fast balls<br><span class="diff">⭐⭐⭐</span></div>
  <div class="mode-card"><span class="icon">🎯</span><span class="name">Practice</span>No timer<br>3 big slow balls<br><span class="diff">⭐</span></div>
</div>
<br>
<div class="info-card">
  <b>🏆 Scoring:</b><br>
  • Smaller balls → more points (1–4 pts)<br>
  • Hit multiple in a row → <span class="green"><b>Combo multiplier up to ×5!</b></span><br>
  • Miss a shot → combo resets to zero
</div>
""", unsafe_allow_html=True)

st.info(
    "💡 **Best played** with good lighting. "
    "Start with **🎯 Practice** mode! "
    "On phone/tablet rotate to **landscape** for best experience. "
    "🔊 Sound plays in your browser — make sure your **volume is on**!"
)

st.markdown(
    '<p style="text-align:center;font-size:0.72rem;color:rgba(255,255,255,0.25);margin-top:8px;">'
    "⚙️ AI via MediaPipe HandLandmarker · 🔊 Sound via Web Audio API (browser-side) · No data stored"
    "</p>",
    unsafe_allow_html=True,
)