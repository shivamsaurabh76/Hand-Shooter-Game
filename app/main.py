"""
Hand Gun Shooting Game — Production Streamlit App
==================================================
Sound works via Web Audio API in the browser (server-side audio
is impossible in deployed Streamlit — we bridge combo events to JS).
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
  font-size:clamp(1.4rem,5vw,2.6rem);
  font-weight:900;
  background:linear-gradient(135deg,#FFD700 30%,#FF8C00 70%);
  -webkit-background-clip:text;
  -webkit-text-fill-color:transparent;
  background-clip:text;
  letter-spacing:0.04em;
  margin:0 0 4px;
  line-height:1.15;
}
.hero .subtitle {
  font-size:clamp(0.78rem,2.5vw,1rem);
  color:rgba(255,255,255,0.55);
  margin:0 0 6px;
  letter-spacing:0.1em;
  text-transform:uppercase;
}
.hero .tagline {
  display:inline-block;
  background:rgba(57,255,20,0.12);
  border:1px solid rgba(57,255,20,0.4);
  border-radius:20px;
  padding:4px 14px;
  font-size:clamp(0.72rem,2vw,0.88rem);
  color:var(--green);
  font-weight:700;
  letter-spacing:0.06em;
}

.divider {
  border:none; height:1px;
  background:linear-gradient(90deg,transparent,var(--gold),transparent);
  margin:6px 0 12px;
}

.stButton > button {
  background:var(--panel) !important;
  color:var(--text) !important;
  border:1px solid var(--border) !important;
  border-radius:var(--radius) !important;
  font-family:'Nunito',sans-serif !important;
  font-size:clamp(0.78rem,2.2vw,0.92rem) !important;
  font-weight:700 !important;
  padding:clamp(0.45rem,1.5vw,0.7rem) clamp(0.5rem,2vw,1rem) !important;
  width:100% !important;
  transition:all 0.18s ease !important;
  white-space:normal !important;
  height:auto !important;
  min-height:52px !important;
  line-height:1.3 !important;
}
.stButton > button:hover {
  background:rgba(255,215,0,0.10) !important;
  border-color:var(--gold) !important;
  color:var(--gold) !important;
  transform:translateY(-1px);
  box-shadow:0 4px 18px rgba(255,215,0,0.18) !important;
}

.section-title {
  font-family:'Orbitron',sans-serif;
  font-size:clamp(0.78rem,2.5vw,0.95rem);
  letter-spacing:0.12em;
  color:var(--gold);
  text-transform:uppercase;
  margin:10px 0 6px;
}

.info-card {
  background:var(--panel);
  border:1px solid var(--border);
  border-radius:var(--radius);
  padding:clamp(0.6rem,2vw,1rem) clamp(0.8rem,2.5vw,1.2rem);
  margin:6px 0;
  font-size:clamp(0.78rem,2vw,0.88rem);
  line-height:1.65;
}
.info-card b { color:var(--gold); }
.info-card .green { color:var(--green); }

.steps { display:flex; gap:8px; flex-wrap:wrap; margin:8px 0; }
.step {
  display:flex; align-items:center; gap:6px;
  background:rgba(255,215,0,0.08);
  border:1px solid var(--border);
  border-radius:30px;
  padding:5px 12px;
  font-size:clamp(0.72rem,1.8vw,0.82rem);
  font-weight:700; white-space:nowrap;
}
.step .num {
  background:var(--gold); color:#000;
  border-radius:50%; width:20px; height:20px;
  display:flex; align-items:center; justify-content:center;
  font-size:0.72rem; font-family:'Orbitron',sans-serif;
}

.mode-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin:8px 0; }
.mode-card {
  background:rgba(255,255,255,0.03);
  border:1px solid rgba(255,255,255,0.1);
  border-radius:10px; padding:10px 10px 8px;
  text-align:center;
  font-size:clamp(0.68rem,1.8vw,0.78rem); line-height:1.5;
}
.mode-card .icon { font-size:clamp(1.3rem,3vw,1.7rem); }
.mode-card .name { font-weight:800; color:var(--gold); display:block; margin:2px 0 1px; }
.mode-card .diff { color:var(--green); }

[data-testid="stExpander"] {
  background:var(--panel) !important;
  border:1px solid var(--border) !important;
  border-radius:var(--radius) !important;
}
[data-testid="stExpander"] summary {
  font-weight:700; color:var(--gold); font-size:clamp(0.82rem,2.2vw,0.95rem);
}
[data-testid="stAlert"] {
  background:rgba(57,255,20,0.07) !important;
  border:1px solid rgba(57,255,20,0.3) !important;
  border-radius:var(--radius) !important;
  font-size:clamp(0.78rem,2vw,0.88rem);
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
#  BROWSER-SIDE SOUND ENGINE (Web Audio API)
# ══════════════════════════════════════════════════════════════════════
#  Why:  sounddevice / winsound run on the cloud SERVER — the user
#        never hears them. We synthesise the exact same sounds in the
#        user's browser using the Web Audio API.
#
#  How:  GameProcessor detects a score increase each frame and writes
#        (hit_seq, hit_combo) to its own fields.  The Streamlit UI
#        thread reads those fields, stores them in session_state, and
#        injects them into the JS component via a data attribute.
#        The JS polls the data attribute every 120 ms and plays
#        the matching synthesised sound immediately.
# ══════════════════════════════════════════════════════════════════════

def _sound_component(event: dict) -> None:
    """Inject the Web Audio synth + current hit event into the page."""
    ev_json = json.dumps(event)
    html = f"""
<div id="sb" data-ev='{ev_json}' style="display:none;height:0"></div>
<script>
(function(){{
  // ── AudioContext ─────────────────────────────────────────────────
  var _actx = null;
  function ctx(){{
    if(!_actx) _actx = new(window.AudioContext||window.webkitAudioContext)();
    if(_actx.state==='suspended') _actx.resume();
    return _actx;
  }}

  // ── Bell tone (fund + harmonics + exp decay) ────────────────────
  function bell(freq, durMs, amp){{
    amp = amp||0.45;
    var c=ctx(), n=Math.round(c.sampleRate*durMs/1000);
    var buf=c.createBuffer(1,n,c.sampleRate), d=buf.getChannelData(0);
    var tau=durMs/1000;
    for(var i=0;i<n;i++){{
      var t=i/c.sampleRate, dc=Math.exp(-5*t/tau);
      d[i]=amp*dc*(0.50*Math.sin(6.2832*freq*t)
                  +0.25*Math.sin(6.2832*freq*2*t)
                  +0.10*Math.sin(6.2832*freq*3*t));
    }}
    return buf;
  }}

  // ── Frequency sweep (bubble pop) ────────────────────────────────
  function sweep(f0,f1,durMs,amp){{
    amp=amp||0.50;
    var c=ctx(), n=Math.round(c.sampleRate*durMs/1000);
    var buf=c.createBuffer(1,n,c.sampleRate), d=buf.getChannelData(0);
    var ph=0;
    for(var i=0;i<n;i++){{
      var t=i/n, env=0.5-0.5*Math.cos(Math.PI*t), f=f0+(f1-f0)*t;
      ph+=6.2832*f/c.sampleRate;
      d[i]=amp*env*Math.sin(ph);
    }}
    return buf;
  }}

  // ── Play buffer now ──────────────────────────────────────────────
  function play(buf, when){{
    var c=ctx(), src=c.createBufferSource();
    src.buffer=buf; src.connect(c.destination);
    src.start(when||0);
  }}

  // ── Sequence of bell notes ───────────────────────────────────────
  function seq(notes, gapMs){{
    gapMs=gapMs||8;
    var c=ctx(), when=c.currentTime+0.01;
    for(var i=0;i<notes.length;i++){{
      var no=notes[i], src=c.createBufferSource();
      src.buffer=bell(no[0],no[1],no[2]||0.46);
      src.connect(c.destination); src.start(when);
      when+=(no[1]+gapMs)/1000;
    }}
  }}

  // ── Note table ──────────────────────────────────────────────────
  var N={{C5:523.25,D5:587.33,E5:659.25,G5:783.99,A5:880,
          C6:1046.5,E6:1318.51,G6:1567.98,C7:2093}};

  // ── Sound recipes ────────────────────────────────────────────────
  function sndPop(){{
    play(sweep(1400,280,100,0.55));
    play(bell(N.C6,60,0.28));
  }}
  function sndChime(){{  seq([[N.C5,70],[N.E5,70],[N.G5,70]],10); }}
  function sndCoin(){{   seq([[N.C6,55],[N.E6,55],[N.G6,55]],8);  }}
  function sndShimmer(){{
    seq([[N.C5,45,0.40],[N.D5,45,0.42],[N.E5,45,0.44],
         [N.G5,45,0.46],[N.A5,45,0.48],[N.C6,45,0.50]],6);
  }}
  function sndFanfare(){{
    seq([[N.C5,40,0.38],[N.E5,45,0.41],[N.G5,50,0.44],
         [N.C6,55,0.47],[N.E6,60,0.50],[N.G6,65,0.53],[N.C7,70,0.56]],5);
    setTimeout(function(){{play(bell(N.C6,180,0.30));}},420);
  }}

  function playCombo(combo){{
    if     (combo>=5) sndFanfare();
    else if(combo==4) sndShimmer();
    else if(combo==3) sndCoin();
    else if(combo==2) sndChime();
    else              sndPop();
  }}

  // ── Poll for new events ──────────────────────────────────────────
  var lastSeq=-1;
  function poll(){{
    try{{
      var el=document.getElementById('sb');
      if(el){{
        var ev=JSON.parse(el.getAttribute('data-ev')||'{{}}');
        if(ev.seq!==undefined && ev.seq!==lastSeq){{
          lastSeq=ev.seq;
          playCombo(ev.combo||1);
        }}
      }}
    }}catch(e){{}}
    setTimeout(poll,120);
  }}

  // Unlock AudioContext on first user gesture (required on mobile)
  function unlock(){{ ctx(); poll(); }}
  document.addEventListener('click',   unlock, {{once:true}});
  document.addEventListener('touchend',unlock, {{once:true}});
  setTimeout(poll, 800);   // also start on desktop without click
}})();
</script>
"""
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
        self.hit_seq:   int = 0   # increments on every successful hit
        self.hit_combo: int = 0   # combo level at time of hit
        self._last_score: int = 0

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        with self.lock:
            if self._pending_mode is not None:
                self.game._start_game(self._pending_mode)
                self._pending_mode  = None
                self._last_score    = 0
            if self._pending_reset:
                self.game.reset()
                self._pending_reset = False
                self._last_score    = 0

            img = frame.to_ndarray(format="bgr24")
            out = self.game.process_frame(img)

            # Detect hit: score increased this frame
            if self.game.score > self._last_score:
                self.hit_seq  += 1
                self.hit_combo = self.game.combo
            self._last_score = self.game.score

        return av.VideoFrame.from_ndarray(out, format="bgr24")


# ══════════════════════════════════════════════════════════════════════
#  WEBRTC STREAMER
# ══════════════════════════════════════════════════════════════════════

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


# ══════════════════════════════════════════════════════════════════════
#  SOUND BRIDGE — pull hit events → push to browser JS
# ══════════════════════════════════════════════════════════════════════

if "sound_event" not in st.session_state:
    st.session_state["sound_event"] = {"seq": -1, "combo": 0}

if ctx.state.playing and ctx.video_processor:
    with ctx.video_processor.lock:
        seq   = ctx.video_processor.hit_seq
        combo = ctx.video_processor.hit_combo
    if seq != st.session_state["sound_event"]["seq"]:
        st.session_state["sound_event"] = {"seq": seq, "combo": combo}

# Always render (keeps JS alive across reruns)
_sound_component(st.session_state["sound_event"])


# ══════════════════════════════════════════════════════════════════════
#  GAME MODE BUTTONS
# ══════════════════════════════════════════════════════════════════════

if ctx.state.playing and ctx.video_processor:
    st.markdown('<p class="section-title">🎮 Choose Game Mode</p>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("🎮 Classic\n30s · 5 balls · +2s/hit",
                     use_container_width=True):
            with ctx.video_processor.lock:
                ctx.video_processor._pending_mode = "classic"
    with c2:
        if st.button("⏱ Time Attack\n60s · 7 balls · no bonus",
                     use_container_width=True):
            with ctx.video_processor.lock:
                ctx.video_processor._pending_mode = "time_attack"
    with c3:
        if st.button("🎯 Practice\nNo timer · 3 big balls",
                     use_container_width=True):
            with ctx.video_processor.lock:
                ctx.video_processor._pending_mode = "practice"

    if st.button("🔄 Back to Menu", use_container_width=True):
        with ctx.video_processor.lock:
            ctx.video_processor._pending_reset = True


# ══════════════════════════════════════════════════════════════════════
#  HOW TO PLAY
# ══════════════════════════════════════════════════════════════════════

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
    "⚙️ AI via MediaPipe HandLandmarker · Sound via Web Audio API · No data stored"
    "</p>",
    unsafe_allow_html=True,
)