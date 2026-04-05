"""
Hand Gun Shooting Game - Streamlit Host
Camera + AI hand-tracking run entirely in the user's browser via MediaPipe JS.
No server-side WebRTC or camera processing required.
"""

import os
import streamlit as st

st.set_page_config(
    page_title="Hand Shooter - Children Edition",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "Hand Gun Shooting Game - AI + Computer Vision, Children Edition",
    },
)

try:
    # ── CSS ─────────────────────────────────────────────────────────────
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
</style>
""", unsafe_allow_html=True)

    # ── Hero ─────────────────────────────────────────────────────────────
    st.markdown("""
<div class="hero">
  <h1>&#127919; HAND SHOOTER</h1>
  <p class="subtitle">AI &middot; Computer Vision &middot; Children Edition</p>
  <span class="tagline">&#9995; Open hand to aim &nbsp;&bull;&nbsp; &#9994; Squeeze fist to shoot!</span>
</div>
<hr class="divider">
""", unsafe_allow_html=True)

    # ── Resolve game URL ─────────────────────────────────────────────────
    # Priority: st.context.headers Host → REPLIT_DEV_DOMAIN → relative path
    _game_url = "/app/static/game.html?v=11"
    try:
        _host = ""
        _headers = getattr(st.context, "headers", None)
        if _headers is not None:
            _host = _headers.get("Host", "") or _headers.get("host", "")
        if _host:
            _proto = "http" if _host.startswith("localhost") else "https"
            _game_url = f"{_proto}://{_host}/app/static/game.html?v=11"
        else:
            _dev = os.environ.get("REPLIT_DEV_DOMAIN", "")
            if _dev:
                _game_url = f"https://{_dev}/app/static/game.html?v=11"
    except Exception:
        pass

    # ── Game iframe ──────────────────────────────────────────────────────
    st.markdown(
        f"""
        <iframe
          src="{_game_url}"
          width="100%"
          height="600"
          allow="camera; microphone; autoplay"
          style="border:none; border-radius:14px; display:block;"
        ></iframe>
        """,
        unsafe_allow_html=True,
    )

    # ── How to Play ──────────────────────────────────────────────────────
    with st.expander("📖 How to Play — Easy Guide for Kids & Parents!", expanded=False):
        st.markdown("""
<div class="info-card">
  <b>&#128075; The Gesture is SUPER SIMPLE:</b><br><br>
  <div class="steps">
    <div class="step"><span class="num">1</span> Open your hand flat</div>
    <div class="step"><span class="num">2</span> Move hand to aim at a ball</div>
    <div class="step"><span class="num">3</span> Squeeze your fist &mdash; <span class="green">BOOM!</span></div>
  </div>
  <br>
  <b>&#128161; Tips for best results:</b><br>
  &bull; Good lighting on your hand is key<br>
  &bull; Keep hand 30&ndash;60 cm from camera<br>
  &bull; On phone/tablet: use the <b>front camera</b> in landscape mode<br>
  &bull; Even a 3-year-old can open and close their hand!
</div>
<br>
<div class="mode-grid">
  <div class="mode-card"><span class="icon">&#127918;</span><span class="name">Classic</span>30s + 2s/hit<br>5 balls<br><span class="diff">&#11088;&#11088;</span></div>
  <div class="mode-card"><span class="icon">&#9201;</span><span class="name">Time Attack</span>60s fixed<br>7 fast balls<br><span class="diff">&#11088;&#11088;&#11088;</span></div>
  <div class="mode-card"><span class="icon">&#127919;</span><span class="name">Practice</span>No timer<br>3 big slow balls<br><span class="diff">&#11088;</span></div>
</div>
<br>
<div class="info-card">
  <b>&#127942; Scoring:</b><br>
  &bull; Smaller balls &rarr; more points (1&ndash;4 pts)<br>
  &bull; Hit multiple in a row &rarr; <span class="green"><b>Combo multiplier up to &times;5!</b></span><br>
  &bull; Miss a shot &rarr; combo resets to zero
</div>
""", unsafe_allow_html=True)

    st.info(
        "Best played with good lighting. "
        "Start with Practice mode! "
        "On phone/tablet rotate to landscape for best experience. "
        "Sound plays in your browser — make sure your volume is on!"
    )

    st.markdown(
        '<p style="text-align:center;font-size:0.72rem;color:rgba(255,255,255,0.25);margin-top:8px;">'
        "AI via MediaPipe HandLandmarker JS &middot; Sound via Web Audio API &middot; No data stored or transmitted"
        "</p>",
        unsafe_allow_html=True,
    )

except Exception as _err:
    import traceback
    st.error(
        f"The app encountered a startup error — please report this:\n\n"
        f"```\n{traceback.format_exc()}\n```"
    )
