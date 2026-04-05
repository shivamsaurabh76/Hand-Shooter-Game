"""
Hand Gun Shooting Game — AI + Computer Vision  (Children Edition)
=================================================================
Sound update:
  Every ball pop triggers an immediate melodious child-friendly sound.
  Combo level escalates to richer reward sounds:
    hit x1  → 🫧 Bubble pop / water-drop  (every hit, always)
    hit x2  → ✨ Sparkle chime  (C→E→G arpeggio)
    hit x3  → 🪙 Coin collect   (bright high arpeggio)
    hit x4  → 🌟 Magic shimmer  (6-note pentatonic + shimmer)
    hit x5+ → 🎉 Fanfare cascade (8-note ascending celebration)
"""

from __future__ import annotations

import math
import os
import random
import threading
import time
import urllib.request
from enum import Enum, auto
from typing import List, Optional, Tuple

try:
    import cv2
    import mediapipe as mp
    import numpy as np
    from mediapipe.tasks import python as mp_tasks
    from mediapipe.tasks.python import vision as mp_vision
    _DEPS_OK = True
except ImportError:
    _DEPS_OK = False


# ══════════════════════════════════════════════════════════════════════
#  SOUND ENGINE
# ══════════════════════════════════════════════════════════════════════

class SoundEngine:
    """
    Child-friendly synthesised sounds — no audio files needed.
    Plays on EVERY ball pop (not just combos).
    Combo level selects progressively richer melodious reward.
    """

    SR = 44100

    _NOTES = {
        "C5":  523.25, "D5":  587.33, "E5":  659.25,
        "G5":  783.99, "A5":  880.00,
        "C6": 1046.50, "D6": 1174.66, "E6": 1318.51,
        "G6": 1567.98, "A6": 1760.00,
        "C7": 2093.00,
    }

    def __init__(self) -> None:
        self._sd   = None
        self._mode = "silent"
        self._lock = threading.Lock()
        self._init_backend()

    def _init_backend(self) -> None:
        try:
            import sounddevice as sd
            sd.query_devices()
            self._sd   = sd
            self._mode = "sounddevice"
            return
        except Exception:
            pass
        try:
            import winsound         # noqa: F401
            self._mode = "winsound"
            return
        except Exception:
            pass
        self._mode = "silent"
        print("[SoundEngine] No audio backend found — running silent.")

    # ── public ────────────────────────────────────────────────────

    def pop(self, combo: int = 1) -> None:
        """Call on EVERY successful ball hit. combo drives sound choice."""
        if self._mode == "silent":
            return
        threading.Thread(target=self._play_sound,
                         args=(combo,), daemon=True).start()

    # ── waveform primitives ───────────────────────────────────────

    def _sine(self, freq: float, dur_ms: int,
              amp: float = 0.45) -> np.ndarray:
        n = int(self.SR * dur_ms / 1000)
        t = np.linspace(0, dur_ms / 1000, n, dtype=np.float64)
        return (amp * np.sin(2 * math.pi * freq * t)).astype(np.float32)

    def _bell_tone(self, freq: float, dur_ms: int,
                   amp: float = 0.50) -> np.ndarray:
        """
        Bell timbre = fundamental + 2nd + 3rd harmonic
        with exponential decay. Warm, glittery, children love it.
        """
        n     = int(self.SR * dur_ms / 1000)
        t     = np.linspace(0, dur_ms / 1000, n, dtype=np.float64)
        wave  = 0.50 * np.sin(2 * math.pi * freq       * t)
        wave += 0.25 * np.sin(2 * math.pi * freq * 2.0 * t)
        wave += 0.10 * np.sin(2 * math.pi * freq * 3.0 * t)
        decay = np.exp(-5.0 * t / (dur_ms / 1000))
        return (wave * decay * amp).astype(np.float32)

    def _sweep(self, f_start: float, f_end: float,
               dur_ms: int, amp: float = 0.50) -> np.ndarray:
        """
        Frequency glide (sweep). Descending = bubble pop / water drop.
        Hanning envelope removes all clicks.
        """
        n     = int(self.SR * dur_ms / 1000)
        t     = np.linspace(0, dur_ms / 1000, n, dtype=np.float64)
        freq  = np.linspace(f_start, f_end, n, dtype=np.float64)
        phase = 2 * math.pi * np.cumsum(freq) / self.SR
        env   = np.hanning(n)
        return (amp * np.sin(phase) * env).astype(np.float32)

    def _silence(self, dur_ms: int) -> np.ndarray:
        return np.zeros(int(self.SR * dur_ms / 1000), dtype=np.float32)

    def _normalise(self, wave: np.ndarray,
                   peak: float = 0.80) -> np.ndarray:
        mx = np.max(np.abs(wave))
        if mx > 1e-6:
            wave = wave * (peak / mx)
        return wave.astype(np.float32)

    # ── sound recipes ─────────────────────────────────────────────

    def _sound_bubble_pop(self) -> np.ndarray:
        """
        🫧 Bubble pop / water-drop — plays on EVERY hit.
        1400 Hz → 280 Hz descending glide (100 ms)
        + C6 bell overtone (60 ms) layered in.
        Feels like popping bubble wrap. Kids go crazy for this.
        """
        drop  = self._sweep(1400, 280, 100, amp=0.55)
        bell  = self._bell_tone(self._NOTES["C6"], 60, amp=0.28)
        # Align lengths
        ln    = len(drop)
        if len(bell) < ln:
            bell = np.concatenate([bell,
                   np.zeros(ln - len(bell), dtype=np.float32)])
        wave = drop + bell[:ln]
        return self._normalise(wave)

    def _sound_sparkle_chime(self) -> np.ndarray:
        """
        ✨ Sparkle chime — combo x2.
        Rising C5 → E5 → G5 bell arpegio, 70 ms each.
        Classic "ding-ding-ding" reward feel.
        """
        parts = []
        for note in ["C5", "E5", "G5"]:
            parts.append(self._bell_tone(self._NOTES[note], 70, amp=0.48))
            parts.append(self._silence(10))
        return self._normalise(np.concatenate(parts))

    def _sound_coin_collect(self) -> np.ndarray:
        """
        🪙 Coin collect — combo x3.
        Bright high-octave C6 → E6 → G6. Punchy and exciting.
        """
        parts = []
        for note in ["C6", "E6", "G6"]:
            parts.append(self._bell_tone(self._NOTES[note], 55, amp=0.50))
            parts.append(self._silence(8))
        return self._normalise(np.concatenate(parts))

    def _sound_magic_shimmer(self) -> np.ndarray:
        """
        🌟 Magic shimmer — combo x4.
        6-note C major pentatonic cascade C5→D5→E5→G5→A5→C6
        + high-freq shimmer sweep underneath.
        Sounds like fairy dust / glitter sprinkle.
        """
        note_seq = ["C5", "D5", "E5", "G5", "A5", "C6"]
        parts    = []
        for i, note in enumerate(note_seq):
            parts.append(self._bell_tone(
                self._NOTES[note], 45, amp=0.40 + i * 0.02))
            parts.append(self._silence(6))
        base    = np.concatenate(parts)
        # Shimmer layer
        shimmer = self._sweep(1800, 900, int(len(base) * 1000 / self.SR),
                              amp=0.12)
        mn      = min(len(base), len(shimmer))
        base[:mn] += shimmer[:mn]
        return self._normalise(base)

    def _sound_fanfare(self) -> np.ndarray:
        """
        🎉 Fanfare cascade — combo x5+.
        7-note ascending sparkle C5→E5→G5→C6→E6→G6→C7
        + long trailing C6 bell ring.
        Big celebration sound — kids cheer!
        """
        note_seq = ["C5", "E5", "G5", "C6", "E6", "G6", "C7"]
        parts    = []
        for i, note in enumerate(note_seq):
            dur = 40 + i * 5
            parts.append(self._bell_tone(
                self._NOTES[note], dur, amp=0.38 + i * 0.03))
            parts.append(self._silence(5))
        # Trailing ring
        parts.append(self._bell_tone(self._NOTES["C6"], 180, amp=0.30))
        return self._normalise(np.concatenate(parts))

    # ── dispatch ──────────────────────────────────────────────────

    def _play_sound(self, combo: int) -> None:
        """Daemon thread: pick sound by combo, play it, done."""
        with self._lock:
            try:
                if   combo >= 5: wave = self._sound_fanfare()
                elif combo == 4: wave = self._sound_magic_shimmer()
                elif combo == 3: wave = self._sound_coin_collect()
                elif combo == 2: wave = self._sound_sparkle_chime()
                else:            wave = self._sound_bubble_pop()

                if self._mode == "sounddevice":
                    self._sd.play(wave, self.SR)
                    self._sd.wait()

                elif self._mode == "winsound":
                    import winsound
                    sequences = {
                        1: [(1400,40),(800,30),(400,55)],
                        2: [(523,55),(659,55),(784,65)],
                        3: [(1047,45),(1319,45),(1568,55)],
                        4: [(523,35),(587,35),(659,35),
                            (784,35),(880,35),(1047,55)],
                        5: [(523,30),(659,30),(784,30),(1047,30),
                            (1319,30),(1568,30),(2093,70)],
                    }
                    for freq, dur in sequences.get(min(combo,5),
                                                   sequences[1]):
                        winsound.Beep(int(freq), int(dur))

            except Exception:
                pass


# ══════════════════════════════════════════════════════════════════════
#  COLOUR PALETTE  (BGR)
# ══════════════════════════════════════════════════════════════════════

class C:
    WHITE      = (255, 255, 255)
    BLACK      = (  0,   0,   0)
    RED        = (  0,   0, 255)
    GREEN      = (  0, 255,   0)
    BLUE       = (255,   0,   0)
    YELLOW     = (  0, 255, 255)
    CYAN       = (255, 255,   0)
    ORANGE     = (  0, 165, 255)
    GOLD       = (  0, 215, 255)
    DARK_GRAY  = ( 40,  40,  40)
    MID_GRAY   = ( 80,  80,  80)
    LIGHT_GRAY = (200, 200, 200)
    NEON_GREEN = ( 57, 255,  20)
    PANEL_BG   = ( 22,  22,  32)
    HOVER_BG   = ( 40,  70,  40)
    PINK       = (180,  80, 255)
    SKY        = (255, 200, 100)


# ══════════════════════════════════════════════════════════════════════
#  ENUMS & MODE CONFIG
# ══════════════════════════════════════════════════════════════════════

class GameState(Enum):
    MENU      = auto()
    PLAYING   = auto()
    GAME_OVER = auto()


MODE_CONFIGS: dict[str, dict] = {
    "classic": {
        "label":        "CLASSIC",
        "initial_time":  30.0,
        "ball_count":     5,
        "bonus_time":     2.0,
        "ball_speed":    (1.8, 4.5),
        "ball_size":     (28, 50),
        "has_timer":     True,
        "description":  "Pop balls before time runs out  •  +2s per hit",
        "icon_color":   C.GREEN,
        "key_hint":     "[1]",
    },
    "time_attack": {
        "label":        "TIME ATTACK",
        "initial_time":  60.0,
        "ball_count":     7,
        "bonus_time":     0.0,
        "ball_speed":    (2.5, 6.0),
        "ball_size":     (22, 42),
        "has_timer":     True,
        "description":  "60 seconds  •  7 balls  •  Max your score!",
        "icon_color":   C.ORANGE,
        "key_hint":     "[2]",
    },
    "practice": {
        "label":        "PRACTICE",
        "initial_time":   0.0,
        "ball_count":     3,
        "bonus_time":     0.0,
        "ball_speed":    (1.2, 3.0),
        "ball_size":     (35, 60),
        "has_timer":     False,
        "description":  "No timer  •  Big slow balls  •  Learn to squeeze!",
        "icon_color":   C.CYAN,
        "key_hint":     "[3]",
    },
}

MODE_ORDER = ["classic", "time_attack", "practice"]


class HL:
    WRIST       =  0
    THUMB_CMC   =  1;  THUMB_MCP  =  2;  THUMB_IP   =  3;  THUMB_TIP  =  4
    INDEX_MCP   =  5;  INDEX_PIP  =  6;  INDEX_DIP  =  7;  INDEX_TIP  =  8
    MIDDLE_MCP  =  9;  MIDDLE_PIP = 10;  MIDDLE_DIP = 11;  MIDDLE_TIP = 12
    RING_MCP    = 13;  RING_PIP   = 14;  RING_DIP   = 15;  RING_TIP   = 16
    PINKY_MCP   = 17;  PINKY_PIP  = 18;  PINKY_DIP  = 19;  PINKY_TIP  = 20

HAND_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),
    (0,5),(5,6),(6,7),(7,8),
    (5,9),(9,10),(10,11),(11,12),
    (9,13),(13,14),(14,15),(15,16),
    (0,17),(13,17),(17,18),(18,19),(19,20),
]


# ══════════════════════════════════════════════════════════════════════
#  MATH UTILITIES
# ══════════════════════════════════════════════════════════════════════

class MathUtils:

    @staticmethod
    def angle_3d(p1, p2, p3) -> float:
        v1 = np.array([p1.x-p2.x, p1.y-p2.y, p1.z-p2.z])
        v2 = np.array([p3.x-p2.x, p3.y-p2.y, p3.z-p2.z])
        n1, n2 = float(np.linalg.norm(v1)), float(np.linalg.norm(v2))
        if n1 < 1e-8 or n2 < 1e-8:
            return 0.0
        return math.degrees(math.acos(max(-1.0, min(1.0,
               float(np.dot(v1, v2)) / (n1 * n2)))))

    @staticmethod
    def lerp(a: float, b: float, t: float) -> float:
        return a + t * (b - a)

    @staticmethod
    def dist(x1: float, y1: float, x2: float, y2: float) -> float:
        return math.hypot(x2-x1, y2-y1)

    @staticmethod
    def in_rect(px, py, rx, ry, rw, rh) -> bool:
        return rx <= px <= rx+rw and ry <= py <= ry+rh


# ════════════════════════════════════════════════════════════════════���═
#  PARTICLE  (keyword-only — BUG-01 fix retained)
# ══════════════════════════════════════════════════════════════════════

class Particle:
    __slots__ = ('x','y','vx','vy','life','max_life','color','radius','gravity')

    def __init__(self, *, x, y, vx, vy, life, color, radius,
                 gravity=200.0) -> None:
        self.x=x; self.y=y; self.vx=vx; self.vy=vy
        self.life=float(life); self.max_life=float(life)
        self.color=tuple(int(c) for c in color)
        self.radius=float(radius); self.gravity=float(gravity)

    def update(self, dt: float) -> bool:
        self.x+=self.vx*dt; self.y+=self.vy*dt
        self.vy+=self.gravity*dt; self.life-=dt
        return self.life > 0.0

    def draw(self, frame: np.ndarray) -> None:
        a   = max(0.0, self.life/self.max_life)
        r   = max(1, int(self.radius*a))
        col = tuple(max(0,min(255,int(c*a))) for c in self.color)
        cv2.circle(frame,(int(self.x),int(self.y)),r,col,-1,cv2.LINE_AA)


# ══════════════════════════════════════════════════════════════════════
#  PARTICLE SYSTEM
# ══════════════════════════════════════════════════════════════════════

class ParticleSystem:

    def __init__(self) -> None:
        self._pool: List[Particle] = []

    def burst(self, x, y, n, color, speed=(60.0,280.0)) -> None:
        for _ in range(n):
            a=random.uniform(0,2*math.pi); s=random.uniform(*speed)
            l=random.uniform(0.35,0.90);   r=random.uniform(2.0,7.0)
            v=tuple(max(0,min(255,int(c)+random.randint(-35,35))) for c in color)
            self._pool.append(Particle(x=x,y=y,vx=math.cos(a)*s,
                vy=math.sin(a)*s,life=l,color=v,radius=r,gravity=200.0))

    def ring(self, x, y, n, color) -> None:
        for i in range(n):
            a=(2*math.pi*i)/n
            self._pool.append(Particle(x=x,y=y,vx=math.cos(a)*220.0,
                vy=math.sin(a)*220.0,life=0.40,color=color,
                radius=3.0,gravity=0.0))

    def confetti_burst(self, x, y, n=45) -> None:
        palette=[C.RED,C.GREEN,C.BLUE,C.YELLOW,C.CYAN,C.ORANGE,C.PINK,C.GOLD]
        for _ in range(n):
            a=random.uniform(0,2*math.pi); s=random.uniform(80.0,340.0)
            l=random.uniform(0.55,1.30);   r=random.uniform(4.0,11.0)
            self._pool.append(Particle(x=x,y=y,vx=math.cos(a)*s,
                vy=math.sin(a)*s,life=l,color=random.choice(palette),
                radius=r,gravity=180.0))

    def spark(self, x, y) -> None:
        for _ in range(8):
            a=random.uniform(0,2*math.pi); s=random.uniform(30.0,100.0)
            self._pool.append(Particle(x=x,y=y,vx=math.cos(a)*s,
                vy=math.sin(a)*s,life=0.30,color=C.RED,
                radius=2.5,gravity=150.0))

    def update(self, dt: float) -> None:
        self._pool=[p for p in self._pool if p.update(dt)]

    def draw(self, frame: np.ndarray) -> None:
        for p in self._pool: p.draw(frame)

    def clear(self) -> None:
        self._pool.clear()


# ══════════════════════════════════════════════════════════════════════
#  SCORE POPUP
# ══════════════════════════════════════════════════════════════════════

class ScorePopup:
    def __init__(self,x,y,text,color,life=1.2) -> None:
        self.x=int(x); self.y=int(y); self.text=str(text)
        self.color=tuple(int(c) for c in color)
        self.life=float(life); self._max=float(life)

    def update(self,dt) -> bool:
        self.y-=int(60*dt); self.life-=dt; return self.life>0.0

    def draw(self,frame) -> None:
        a=max(0.0,self.life/self._max)
        col=tuple(max(0,min(255,int(c*a))) for c in self.color)
        cv2.putText(frame,self.text,(self.x,self.y),
                    cv2.FONT_HERSHEY_SIMPLEX,0.60+0.40*a,col,
                    max(1,int(2*a)),cv2.LINE_AA)


# ══════════════════════════════════════════════════════════════════════
#  TARGET BALL
# ══════════════════════════════════════════════════════════════════════

class TargetBall:
    _PALETTE=[
        (80,80,255),(80,200,80),(255,80,80),
        (80,220,255),(255,160,80),(200,80,255),
        (0,220,220),(220,200,0),
    ]

    def __init__(self,W,H,min_r=28,max_r=55,
                 min_spd=1.5,max_spd=5.5) -> None:
        self.W=W; self.H=H
        self.base_r=random.randint(min_r,max_r); self.r=self.base_r
        m=self.base_r+14
        self.x=float(random.randint(m,W-m))
        self.y=float(random.randint(m,H-m))
        spd=random.uniform(min_spd,max_spd)
        ang=random.uniform(0,2*math.pi)
        self.vx=math.cos(ang)*spd; self.vy=math.sin(ang)*spd
        self.color=random.choice(self._PALETTE)
        self.hi_col=tuple(min(255,c+60) for c in self.color)
        self.phase=random.uniform(0,2*math.pi); self.alive=True

    def update(self,elapsed) -> None:
        self.x+=self.vx; self.y+=self.vy; r=self.base_r
        if self.x-r<=0:   self.vx=abs(self.vx);  self.x=float(r)
        elif self.x+r>=self.W: self.vx=-abs(self.vx); self.x=float(self.W-r)
        if self.y-r<=0:   self.vy=abs(self.vy);  self.y=float(r)
        elif self.y+r>=self.H: self.vy=-abs(self.vy); self.y=float(self.H-r)
        self.r=int(self.base_r+3*math.sin(elapsed*3.5+self.phase))

    def draw(self,frame) -> None:
        if not self.alive: return
        cx,cy=int(self.x),int(self.y); r=max(5,self.r)
        cv2.circle(frame,(cx+4,cy+4),r,C.BLACK,-1,cv2.LINE_AA)
        cv2.circle(frame,(cx,cy),r+6,self.color,2,cv2.LINE_AA)
        cv2.circle(frame,(cx,cy),r,self.color,-1,cv2.LINE_AA)
        off=max(1,r//4)
        cv2.circle(frame,(cx-off,cy-off),max(2,r//3),self.hi_col,-1,cv2.LINE_AA)
        cv2.circle(frame,(cx,cy),r,C.WHITE,2,cv2.LINE_AA)
        if r>=18:
            eo=max(2,r//5); er=max(2,r//8)
            cv2.circle(frame,(cx-eo,cy-eo//2),er,C.BLACK,-1,cv2.LINE_AA)
            cv2.circle(frame,(cx+eo,cy-eo//2),er,C.BLACK,-1,cv2.LINE_AA)
            cv2.ellipse(frame,(cx,cy+r//8),(max(2,r//3),max(2,r//5)),
                        0,0,180,C.BLACK,2,cv2.LINE_AA)
        pts=self.points(); br=max(10,r//3); bx,by=cx+r-4,cy-r+4
        cv2.circle(frame,(bx,by),br,C.GOLD,-1,cv2.LINE_AA)
        cv2.circle(frame,(bx,by),br,C.WHITE,1,cv2.LINE_AA)
        lbl=str(pts); ls=cv2.getTextSize(lbl,cv2.FONT_HERSHEY_SIMPLEX,0.38,1)[0]
        cv2.putText(frame,lbl,(bx-ls[0]//2,by+ls[1]//2),
                    cv2.FONT_HERSHEY_SIMPLEX,0.38,C.BLACK,1,cv2.LINE_AA)

    def hit_test(self,px,py) -> bool:
        return MathUtils.dist(px,py,self.x,self.y)<self.r*1.20

    def points(self) -> int:
        return max(1,4-(self.base_r-22)//10)


# ══════════════════════════════════════════════════════════════════════
#  GESTURE DETECTOR
# ══════════════════════════════════════════════════════════════════════

class GestureDetector:
    MODEL_URL=(
        "https://storage.googleapis.com/mediapipe-models/"
        "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
    )
    FOLD_MAX=110.0; FINGERS_TO_SHOOT=3

    def __init__(self,max_hands=1,det_conf=0.62,trk_conf=0.58) -> None:
        path=self._get_model()
        opts=mp_vision.HandLandmarkerOptions(
            base_options=mp_tasks.BaseOptions(model_asset_path=path),
            num_hands=max_hands,
            min_hand_detection_confidence=det_conf,
            min_hand_presence_confidence=det_conf,
            min_tracking_confidence=trk_conf,
            running_mode=mp_vision.RunningMode.VIDEO,
        )
        self._det=mp_vision.HandLandmarker.create_from_options(opts)
        self._ts=0

    @classmethod
    def _get_model(cls) -> str:
        here=os.path.dirname(os.path.abspath(__file__))
        path=os.path.join(here,"hand_landmarker.task")
        if not os.path.exists(path):
            print("[GestureDetector] Downloading hand_landmarker.task …")
            urllib.request.urlretrieve(cls.MODEL_URL,path)
            print("[GestureDetector] Model ready.")
        return path

    def detect(self,rgb):
        self._ts+=33
        img=mp.Image(image_format=mp.ImageFormat.SRGB,
                     data=np.ascontiguousarray(rgb))
        return self._det.detect_for_video(img,self._ts)

    def is_shooting(self,lms) -> bool:
        folded=0
        for mcp,pip,dip in [
            (HL.INDEX_MCP,HL.INDEX_PIP,HL.INDEX_DIP),
            (HL.MIDDLE_MCP,HL.MIDDLE_PIP,HL.MIDDLE_DIP),
            (HL.RING_MCP,HL.RING_PIP,HL.RING_DIP),
            (HL.PINKY_MCP,HL.PINKY_PIP,HL.PINKY_DIP),
        ]:
            if MathUtils.angle_3d(lms[mcp],lms[pip],lms[dip])<self.FOLD_MAX:
                folded+=1
        if lms[HL.THUMB_TIP].y>lms[HL.THUMB_MCP].y: folded+=1
        return folded>=self.FINGERS_TO_SHOOT

    def open_fingers_count(self,lms) -> int:
        return sum(1 for mcp,pip,dip in [
            (HL.INDEX_MCP,HL.INDEX_PIP,HL.INDEX_DIP),
            (HL.MIDDLE_MCP,HL.MIDDLE_PIP,HL.MIDDLE_DIP),
            (HL.RING_MCP,HL.RING_PIP,HL.RING_DIP),
            (HL.PINKY_MCP,HL.PINKY_PIP,HL.PINKY_DIP),
        ] if MathUtils.angle_3d(lms[mcp],lms[pip],lms[dip])>=self.FOLD_MAX)

    def index_tip_px(self,lms,W,H):
        t=lms[HL.INDEX_TIP]; return int(t.x*W),int(t.y*H)

    def palm_center_px(self,lms,W,H):
        pts=[lms[i] for i in (HL.WRIST,HL.INDEX_MCP,HL.MIDDLE_MCP,
                               HL.RING_MCP,HL.PINKY_MCP)]
        return (int(sum(p.x for p in pts)/len(pts)*W),
                int(sum(p.y for p in pts)/len(pts)*H))

    def draw_skeleton(self,frame,lms,W,H,shooting) -> None:
        pts=[(int(l.x*W),int(l.y*H)) for l in lms]
        bc=C.RED if shooting else (0,220,0)
        for a,b in HAND_CONNECTIONS:
            cv2.line(frame,pts[a],pts[b],bc,2,cv2.LINE_AA)
        for p in pts:
            cv2.circle(frame,p,4,(220,80,0),-1,cv2.LINE_AA)
            cv2.circle(frame,p,4,C.WHITE,1,cv2.LINE_AA)

    def close(self) -> None:
        self._det.close()


# ══════════════════════════════════════════════════════════════════════
#  HUD
# ══════════════════════════════════════════════════════════════════════

class HUD:

    @staticmethod
    def panel(frame,x,y,w,h,color=C.PANEL_BG,alpha=0.75,
              border=C.WHITE,bthick=1) -> None:
        ov=frame.copy()
        cv2.rectangle(ov,(x,y),(x+w,y+h),color,-1)
        cv2.addWeighted(ov,alpha,frame,1.0-alpha,0,frame)
        cv2.rectangle(frame,(x,y),(x+w,y+h),border,bthick)

    @staticmethod
    def ctext(frame,text,cx,y,scale,color,thick=1) -> None:
        sz=cv2.getTextSize(text,cv2.FONT_HERSHEY_SIMPLEX,scale,thick)[0]
        cv2.putText(frame,text,(cx-sz[0]//2,y),
                    cv2.FONT_HERSHEY_SIMPLEX,scale,color,thick,cv2.LINE_AA)

    @staticmethod
    def score_panel(frame,score,combo,W) -> None:
        pw=min(220,W//3)
        HUD.panel(frame,12,8,pw,72,border=C.GOLD)
        cv2.putText(frame,f"SCORE: {score}",(24,40),
                    cv2.FONT_HERSHEY_SIMPLEX,0.78,C.GOLD,2,cv2.LINE_AA)
        if combo>1:
            cv2.putText(frame,f"x{combo}  COMBO!",(24,64),
                        cv2.FONT_HERSHEY_SIMPLEX,0.46,C.NEON_GREEN,1,cv2.LINE_AA)

    @staticmethod
    def timer_panel(frame,t,W) -> None:
        pw=min(220,W//3); x=W-pw-12
        HUD.panel(frame,x,8,pw,48,border=C.GOLD)
        col=C.GREEN if t>10 else C.YELLOW if t>5 else C.RED
        cv2.putText(frame,f"TIME  {t:.1f}s",(x+14,40),
                    cv2.FONT_HERSHEY_SIMPLEX,0.78,col,2,cv2.LINE_AA)

    @staticmethod
    def elapsed_panel(frame,t,W) -> None:
        pw=min(220,W//3); x=W-pw-12
        HUD.panel(frame,x,8,pw,48,border=C.CYAN)
        cv2.putText(frame,f"TIME  {t:.1f}s",(x+14,40),
                    cv2.FONT_HERSHEY_SIMPLEX,0.78,C.CYAN,2,cv2.LINE_AA)

    @staticmethod
    def mode_label(frame,label,W) -> None:
        HUD.ctext(frame,label,W//2,26,0.50,C.LIGHT_GRAY)

    @staticmethod
    def gesture_hint(frame,open_count,W,H) -> None:
        bar_h=40
        HUD.panel(frame,0,H-bar_h,W,bar_h,C.DARK_GRAY,0.82)
        sq_w,sq_h=18,22; total_w=5*sq_w+4*4
        sx0=(W-total_w)//2; sy0=H-bar_h+8
        for i in range(5):
            col=C.NEON_GREEN if i<open_count else C.MID_GRAY
            bx=sx0+i*(sq_w+4)
            cv2.rectangle(frame,(bx,sy0),(bx+sq_w,sy0+sq_h),col,-1)
            cv2.rectangle(frame,(bx,sy0),(bx+sq_w,sy0+sq_h),C.WHITE,1)
        HUD.ctext(frame,"OPEN hand to aim   SQUEEZE fist to shoot!",
                  W//2,H-5,0.40,C.LIGHT_GRAY)

    @staticmethod
    def crosshair(frame,x,y,shooting,open_fingers=4,size=26) -> None:
        if shooting:
            col,thick=C.RED,3
            cv2.circle(frame,(x,y),size+14,C.ORANGE,2,cv2.LINE_AA)
        elif open_fingers<=1: col,thick=C.ORANGE,3
        else: col,thick=C.NEON_GREEN,2
        cv2.line(frame,(x-size,y),(x+size,y),col,thick,cv2.LINE_AA)
        cv2.line(frame,(x,y-size),(x,y+size),col,thick,cv2.LINE_AA)
        cv2.circle(frame,(x,y),size-6,col,thick,cv2.LINE_AA)
        cv2.circle(frame,(x,y),3,col,-1,cv2.LINE_AA)

    @staticmethod
    def game_over(frame,score,accuracy,best_combo,W,H) -> None:
        ov=frame.copy()
        cv2.rectangle(ov,(0,0),(W,H),C.BLACK,-1)
        cv2.addWeighted(ov,0.72,frame,0.28,0,frame)
        pw,ph=min(500,W-40),310; px,py=(W-pw)//2,(H-ph)//2
        HUD.panel(frame,px,py,pw,ph,C.DARK_GRAY,0.92,C.GOLD,2)
        HUD.ctext(frame,"GAME  OVER",W//2,py+70,1.9,C.RED,4)
        HUD.ctext(frame,f"Score:  {score}",W//2,py+122,1.0,C.GOLD,2)
        HUD.ctext(frame,
                  f"Accuracy {accuracy:.0f}%   |   Best Combo x{best_combo}",
                  W//2,py+162,0.5,C.LIGHT_GRAY,1)
        HUD.ctext(frame,"SQUEEZE to play again  or  [R]",
                  W//2,py+210,0.5,C.LIGHT_GRAY,1)
        HUD.ctext(frame,"[M] Menu     [Q] Quit",
                  W//2,py+252,0.5,C.LIGHT_GRAY,1)


# ══════════════════════════════════════════════════════════════════════
#  MENU ITEM
# ══════════════════════════════════════════════════════════════════════

class MenuItem:
    HOLD_TIME=1.2
    def __init__(self,key,rect) -> None:
        cfg=MODE_CONFIGS[key]; self.key=key; self.rect=rect
        self.name=cfg["label"]; self.desc=cfg["description"]
        self.hint=cfg["key_hint"]; self.dot_col=cfg["icon_color"]
        self.hover_t=0.0; self.hovered=False; self._flash=0.0

    def update(self,cx,cy,dt) -> bool:
        x,y,w,h=self.rect; self.hovered=MathUtils.in_rect(cx,cy,x,y,w,h)
        if self.hovered:
            self.hover_t+=dt; self._flash=max(0.0,self._flash-dt)
            return self.hover_t>=self.HOLD_TIME
        else: self.hover_t=max(0.0,self.hover_t-dt*2)
        return False

    def flash(self) -> None: self._flash=0.22

    def draw(self,frame) -> None:
        x,y,w,h=self.rect
        ov=frame.copy()
        cv2.rectangle(ov,(x,y),(x+w,y+h),
                      C.HOVER_BG if self.hovered else C.PANEL_BG,-1)
        cv2.addWeighted(ov,0.82,frame,0.18,0,frame)
        if self._flash>0:
            fl=frame.copy(); cv2.rectangle(fl,(x,y),(x+w,y+h),C.WHITE,-1)
            r=min(1.0,self._flash/0.22)
            cv2.addWeighted(fl,r*0.40,frame,1.0-r*0.40,0,frame)
        cv2.rectangle(frame,(x,y),(x+w,y+h),
                      C.NEON_GREEN if self.hovered else C.MID_GRAY,2)
        cv2.circle(frame,(x+26,y+h//2),11,self.dot_col,-1,cv2.LINE_AA)
        cv2.circle(frame,(x+26,y+h//2),11,C.WHITE,1,cv2.LINE_AA)
        kx=x+w-44
        cv2.rectangle(frame,(kx,y+8),(kx+36,y+28),C.MID_GRAY,-1)
        cv2.rectangle(frame,(kx,y+8),(kx+36,y+28),C.LIGHT_GRAY,1)
        ks=cv2.getTextSize(self.hint,cv2.FONT_HERSHEY_SIMPLEX,0.38,1)[0]
        cv2.putText(frame,self.hint,(kx+(36-ks[0])//2,y+22),
                    cv2.FONT_HERSHEY_SIMPLEX,0.38,C.LIGHT_GRAY,1,cv2.LINE_AA)
        cv2.putText(frame,self.name,(x+50,y+30),
                    cv2.FONT_HERSHEY_SIMPLEX,0.66,C.WHITE,2,cv2.LINE_AA)
        cv2.putText(frame,self.desc,(x+50,y+52),
                    cv2.FONT_HERSHEY_SIMPLEX,0.38,C.LIGHT_GRAY,1,cv2.LINE_AA)
        if self.hover_t>0:
            p=min(1.0,self.hover_t/self.HOLD_TIME)
            cv2.rectangle(frame,(x+5,y+h-7),
                          (x+5+int((w-10)*p),y+h-3),C.NEON_GREEN,-1)

    def reset(self) -> None:
        self.hover_t=0.0; self.hovered=False; self._flash=0.0


# ══════════════════════════════════════════════════════════════════════
#  MENU SCREEN
# ══════════════════════════════════════════════════════════════════════

class MenuScreen:
    def __init__(self,W,H) -> None:
        self.W=W; self.H=H; self.items: List[MenuItem]=[]
        self._elapsed=0.0; self._build()

    def _build(self) -> None:
        iw=min(440,self.W-60); ih=66; gap=14
        ox=(self.W-iw)//2; oy=int(self.H*0.37)
        self.items=[MenuItem(k,(ox,oy+i*(ih+gap),iw,ih))
                    for i,k in enumerate(MODE_ORDER)]

    def update(self,cx,cy,shooting,dt) -> Optional[str]:
        self._elapsed+=dt
        for item in self.items:
            done=item.update(cx,cy,dt)
            if done or (shooting and item.hovered):
                item.flash(); return item.key
        return None

    def draw(self,frame,cx,cy) -> None:
        W,H=self.W,self.H
        ov=frame.copy(); cv2.rectangle(ov,(0,0),(W,H),C.BLACK,-1)
        cv2.addWeighted(ov,0.62,frame,0.38,0,frame)
        for row in range(0,H,4): cv2.line(frame,(0,row),(W,row),(0,0,0),1)
        cv2.rectangle(frame,(0,0),(W,5),C.GOLD,-1)
        pulse=0.07*math.sin(self._elapsed*2.4)
        t_sc=min(1.1,W/640)+pulse; title="HAND GUN SHOOTING GAME"
        ts=cv2.getTextSize(title,cv2.FONT_HERSHEY_SIMPLEX,t_sc,3)[0]
        tx=(W-ts[0])//2; ty=int(H*0.115)
        cv2.putText(frame,title,(tx+3,ty+3),
                    cv2.FONT_HERSHEY_SIMPLEX,t_sc,C.BLACK,4,cv2.LINE_AA)
        cv2.putText(frame,title,(tx,ty),
                    cv2.FONT_HERSHEY_SIMPLEX,t_sc,C.GOLD,3,cv2.LINE_AA)
        sub="AI  +  Computer Vision   |   Children Edition"
        ss=cv2.getTextSize(sub,cv2.FONT_HERSHEY_SIMPLEX,0.52,1)[0]
        cv2.putText(frame,sub,((W-ss[0])//2,int(H*0.175)),
                    cv2.FONT_HERSHEY_SIMPLEX,0.52,C.LIGHT_GRAY,1,cv2.LINE_AA)
        dy=int(H*0.23); dw=min(320,W//2)
        cv2.line(frame,((W-dw)//2,dy),((W+dw)//2,dy),C.GOLD,1,cv2.LINE_AA)
        dot_x=int((W-dw)//2+dw*((math.sin(self._elapsed*2)+1)/2))
        cv2.circle(frame,(dot_x,dy),4,C.GOLD,-1,cv2.LINE_AA)
        sec="SELECT  GAME  MODE"
        ses=cv2.getTextSize(sec,cv2.FONT_HERSHEY_SIMPLEX,0.56,1)[0]
        cv2.putText(frame,sec,((W-ses[0])//2,int(H*0.305)),
                    cv2.FONT_HERSHEY_SIMPLEX,0.56,C.WHITE,1,cv2.LINE_AA)
        badges=[" Squeeze to Shoot "," Big Smiley Balls "," Combo Scoring "]
        bw_each=min(150,(W-40)//len(badges))
        bx0=(W-bw_each*len(badges)-8*(len(badges)-1))//2
        by0=int(H*0.305)+22
        for i,badge in enumerate(badges):
            bsx=bx0+i*(bw_each+8)
            cv2.rectangle(frame,(bsx,by0),(bsx+bw_each,by0+18),C.MID_GRAY,-1)
            bs=cv2.getTextSize(badge,cv2.FONT_HERSHEY_SIMPLEX,0.30,1)[0]
            cv2.putText(frame,badge,(bsx+(bw_each-bs[0])//2,by0+13),
                        cv2.FONT_HERSHEY_SIMPLEX,0.30,C.CYAN,1,cv2.LINE_AA)
        for item in self.items: item.draw(frame)
        cv2.rectangle(frame,(0,H-36),(W,H),C.DARK_GRAY,-1)
        ins=("Point & SQUEEZE to select    |"
             "    Keys: [1] Classic   [2] Time Attack   [3] Practice")
        iss=cv2.getTextSize(ins,cv2.FONT_HERSHEY_SIMPLEX,0.37,1)[0]
        cv2.putText(frame,ins,((W-iss[0])//2,H-12),
                    cv2.FONT_HERSHEY_SIMPLEX,0.37,C.LIGHT_GRAY,1,cv2.LINE_AA)
        HUD.crosshair(frame,cx,cy,False,5,18)

    def key_select(self,ch) -> Optional[str]:
        return {'1':'classic','2':'time_attack','3':'practice'}.get(ch)

    def reset(self) -> None:
        self._elapsed=0.0
        for item in self.items: item.reset()


# ══════════════════════════════════════════════════════════════════════
#  MAIN GAME ENGINE
# ═══════════════════════════════════════════════════════��══════════════

class HandTrackingGame:
    SHOT_COOLDOWN=12

    def __init__(self,width=1280,height=720) -> None:
        self.W=width; self.H=height
        self.gesture=GestureDetector()
        self.particles=ParticleSystem()
        self.menu=MenuScreen(width,height)
        self.sound=SoundEngine()          # ← sound engine wired in
        self.state=GameState.MENU
        self.mode_key="classic"
        self.config=MODE_CONFIGS["classic"]
        self.cx=width//2; self.cy=height//2; self._smooth=0.30
        self._shooting=False; self._shooting_now=False
        self._open_fingers=5; self._cooldown=0
        self.score=0; self.combo=0; self.best_combo=0
        self.shots_fired=0; self.shots_hit=0
        self._start_t=0.0; self._bonus_t=0.0
        self._go_time=0.0; self._last_t=time.time()
        self.popups: List[ScorePopup]=[]; self.targets: List[TargetBall]=[]

    def process_frame(self,bgr) -> np.ndarray:
        bgr=cv2.flip(bgr,1); bgr=cv2.resize(bgr,(self.W,self.H))
        now=time.time(); dt=min(now-self._last_t,0.08); self._last_t=now
        rgb=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB); result=self.gesture.detect(rgb)
        if result.hand_landmarks:
            lms=result.hand_landmarks[0]
            self._shooting_now=self.gesture.is_shooting(lms)
            self._open_fingers=self.gesture.open_fingers_count(lms)
            self.gesture.draw_skeleton(bgr,lms,self.W,self.H,self._shooting_now)
            ix,iy=self.gesture.index_tip_px(lms,self.W,self.H)
            px,py=self.gesture.palm_center_px(lms,self.W,self.H)
            tx=int(0.7*ix+0.3*px); ty=int(0.7*iy+0.3*py)
            self.cx=int(MathUtils.lerp(self.cx,tx,self._smooth))
            self.cy=int(MathUtils.lerp(self.cy,ty,self._smooth))
        else:
            self._shooting_now=False; self._open_fingers=5
        if self._shooting_now and self._cooldown<=0:
            self._shooting=True; self._cooldown=self.SHOT_COOLDOWN
        else: self._shooting=False
        if self._cooldown>0: self._cooldown-=1
        if   self.state==GameState.MENU:      self._tick_menu(bgr,dt)
        elif self.state==GameState.PLAYING:   self._tick_playing(bgr,dt)
        elif self.state==GameState.GAME_OVER: self._tick_game_over(bgr,dt)
        self.particles.update(dt); self.particles.draw(bgr)
        self.popups=[p for p in self.popups if p.update(dt)]
        for p in self.popups: p.draw(bgr)
        return bgr

    def handle_key(self,key) -> bool:
        try: ch=chr(key&0xFF)
        except (ValueError,OverflowError): ch=''
        if self.state==GameState.MENU:
            sel=self.menu.key_select(ch)
            if sel: self._start_game(sel)
            elif ch=='q': return False
        elif self.state==GameState.PLAYING:
            if ch=='q': return False
            elif ch=='m': self.reset()
        elif self.state==GameState.GAME_OVER:
            if   ch=='r': self._start_game(self.mode_key)
            elif ch=='m': self.reset()
            elif ch=='q': return False
        return True

    def reset(self) -> None:
        self.state=GameState.MENU
        self._shooting=False; self._shooting_now=False; self._cooldown=0
        self.menu.reset(); self.particles.clear(); self.popups.clear()

    def close(self) -> None:
        self.gesture.close()

    def _start_game(self,mode_key) -> None:
        self.mode_key=mode_key; self.config=MODE_CONFIGS[mode_key]
        self.state=GameState.PLAYING
        self.score=0; self.combo=0; self.best_combo=0
        self._bonus_t=0.0; self.shots_fired=0; self.shots_hit=0
        self._go_time=0.0; self._start_t=time.time()
        self._shooting=False; self._shooting_now=False
        self._cooldown=self.SHOT_COOLDOWN
        self.popups.clear(); self.particles.clear()
        cfg=self.config
        self.targets=[
            TargetBall(self.W,self.H,cfg["ball_size"][0],cfg["ball_size"][1],
                       cfg["ball_speed"][0],cfg["ball_speed"][1])
            for _ in range(cfg["ball_count"])
        ]

    def _tick_menu(self,frame,dt) -> None:
        sel=self.menu.update(self.cx,self.cy,self._shooting,dt)
        self.menu.draw(frame,self.cx,self.cy)
        if sel: self._start_game(sel)

    def _tick_playing(self,frame,dt) -> None:
        elapsed=time.time()-self._start_t; cfg=self.config
        if cfg["has_timer"]:
            time_left=max(0.0,cfg["initial_time"]-elapsed+self._bonus_t)
            if time_left<=0.0:
                self.state=GameState.GAME_OVER; self._go_time=0.0; return
        else: time_left=elapsed
        for t in self.targets: t.update(elapsed); t.draw(frame)
        HUD.crosshair(frame,self.cx,self.cy,self._shooting,self._open_fingers)
        if self._shooting:
            self.shots_fired+=1; hit=False
            for tgt in self.targets:
                if tgt.hit_test(self.cx,self.cy):
                    hit=True
                    pts=tgt.points(); mult=min(self.combo+1,5)
                    earned=pts*mult
                    self.score+=earned; self.combo+=1
                    self.best_combo=max(self.best_combo,self.combo)
                    self.shots_hit+=1; self._bonus_t+=cfg["bonus_time"]

                    # ── SOUND on EVERY pop (ADD-02) ──────────────
                    self.sound.pop(self.combo)

                    self.particles.confetti_burst(tgt.x,tgt.y,50)
                    self.particles.ring(tgt.x,tgt.y,16,C.WHITE)
                    self.popups.append(ScorePopup(int(tgt.x)-10,int(tgt.y)-25,
                                                  f"+{earned}",C.GOLD))
                    if mult>1:
                        self.popups.append(ScorePopup(int(tgt.x)-10,int(tgt.y)-52,
                                                      f"x{mult}  COMBO!",C.NEON_GREEN))
                    self.targets.remove(tgt)
                    self.targets.append(TargetBall(self.W,self.H,
                        cfg["ball_size"][0],cfg["ball_size"][1],
                        cfg["ball_speed"][0],cfg["ball_speed"][1]))
                    break
            if not hit:
                self.combo=0; self.particles.spark(self.cx,self.cy)
        HUD.score_panel(frame,self.score,self.combo,self.W)
        if cfg["has_timer"]: HUD.timer_panel(frame,time_left,self.W)
        else: HUD.elapsed_panel(frame,time_left,self.W)
        HUD.mode_label(frame,cfg["label"],self.W)
        HUD.gesture_hint(frame,self._open_fingers,self.W,self.H)

    def _tick_game_over(self,frame,dt) -> None:
        self._go_time+=dt
        acc=(self.shots_hit/max(1,self.shots_fired))*100
        for t in self.targets: t.draw(frame)
        HUD.game_over(frame,self.score,acc,self.best_combo,self.W,self.H)
        if self._go_time>1.5 and self._shooting: self.reset()


# ══════════════════════════════════════════════════════════════════════
#  STANDALONE ENTRY POINT
# ══════════════════════════════════════════════════════════════════════

if __name__=="__main__":
    cap=cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT,720)
    if not cap.isOpened():
        raise RuntimeError("Cannot open webcam.")
    game=HandTrackingGame(width=1280,height=720)
    print("╔══════════════════════════════════════════════════╗")
    print("║  HAND GUN SHOOTING GAME  •  Children Edition     ║")
    print("╠══════════════════════════════════════════════════╣")
    print("║  GESTURE : Open hand to aim, SQUEEZE to shoot   ║")
    print("║  KEYS    : [1][2][3] mode  [M] menu  [Q] quit   ║")
    print("╚══════════════════════════════════════════════════╝")
    while cap.isOpened():
        ok,frame=cap.read()
        if not ok: print("Camera read failed."); break
        out=game.process_frame(frame)
        cv2.imshow("Hand Gun Shooting Game",out)
        key=cv2.waitKey(1)&0xFF
        if key!=255 and not game.handle_key(key): break
    game.close(); cap.release(); cv2.destroyAllWindows()