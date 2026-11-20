import base64
import json
import math
import random
import re
import time
from pathlib import Path

import numpy as np
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Per Anna e Misha",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Un ID video YouTube e' sempre di 11 caratteri
DEFAULT_YT = ("video", "jfKfPfyJRdk")
DEFAULT_YT_URL = "https://www.youtube.com/playlist?list=PLYM6wKmvHYxY"

QUOTES_FILE = Path(__file__).with_name("citazioni.json")
QUOTE_SECONDS = 8


def load_quotes():
    try:
        data = json.loads(QUOTES_FILE.read_text(encoding="utf-8"))
        return [str(q).strip() for q in data if str(q).strip()]
    except Exception:
        return []


def save_quotes_callback():
    lines = [ln.strip() for ln in st.session_state.quotes_text.splitlines() if ln.strip()]
    try:
        QUOTES_FILE.write_text(json.dumps(lines, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass  # filesystem in sola lettura: le citazioni restano valide per la sessione


AUDIO_DIR = Path(__file__).with_name("audio")
AUDIO_TYPES = {
    ".opus": "audio/ogg",  # i vocali WhatsApp sono Ogg/Opus
    ".ogg": "audio/ogg",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".aac": "audio/aac",
    ".wav": "audio/wav",
}
_RE_WA_PTT = re.compile(r"^(?:PTT|AUD)-(\d{4})(\d{2})(\d{2})-WA(\d+)", re.I)
_RE_WA_WEB = re.compile(r"^WhatsApp Audio (\d{4})-(\d{2})-(\d{2}) at (\d{2})\.(\d{2})\.(\d{2})", re.I)


def list_audio():
    try:
        return sorted(
            (p for p in AUDIO_DIR.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_TYPES),
            key=lambda p: p.name.lower(),
        )
    except Exception:
        return []


def audio_title(path):
    """Titolo leggibile: i nomi automatici di WhatsApp diventano 'Vocale del gg/mm/aaaa'."""
    stem = path.stem
    m = _RE_WA_PTT.match(stem)
    if m:
        y, mo, d, n = m.groups()
        return f"Vocale del {d}/{mo}/{y} ({int(n)})"
    m = _RE_WA_WEB.match(stem)
    if m:
        y, mo, d, h, mi, _ = m.groups()
        return f"Vocale del {d}/{mo}/{y}, {h}:{mi}"
    return re.sub(r"_+", " ", stem).strip()


@st.cache_data(show_spinner=False, max_entries=32)
def audio_data_uri(path_str: str, mtime: float) -> str:
    p = Path(path_str)
    mime = AUDIO_TYPES.get(p.suffix.lower(), "audio/mpeg")
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode("ascii")


def save_audio(uploaded):
    name = re.sub(r"[^\w.\- ()]", "_", Path(uploaded.name).name)
    try:
        AUDIO_DIR.mkdir(exist_ok=True)
        (AUDIO_DIR / name).write_bytes(uploaded.getbuffer())
    except Exception:
        pass


if "audio_up_key" not in st.session_state:
    st.session_state.audio_up_key = 0

for k, v in {
    "mode": "mixed",
    "seed_mixed": random.randint(1, 10**7),
    "seed_tulips": random.randint(1, 10**7),
    "sim_t": 0.0,
    "yt_url": DEFAULT_YT_URL,
    "quotes_text": "\n".join(load_quotes()),
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


def cambia_fiori_callback():
    if st.session_state.mode == "mixed":
        st.session_state.mode = "tulips"
        st.session_state.seed_tulips = random.randint(1, 10**7)
    else:
        st.session_state.mode = "mixed"
        st.session_state.seed_mixed = random.randint(1, 10**7)


_RE_LIST = re.compile(r"[?&]list=([A-Za-z0-9_-]+)")
_RE_VID = re.compile(
    r"(?:youtu\.be/|youtube(?:-nocookie)?\.com/(?:watch\?(?:.*&)?v=|embed/|shorts/|live/|v/))([A-Za-z0-9_-]{11})"
)


def parse_youtube_resource(raw_url: str):
    val = (raw_url or "").strip()
    if not val:
        return DEFAULT_YT, False
    m_vid = _RE_VID.search(val)
    m_list = _RE_LIST.search(val)
    if m_vid:
        return ("video", m_vid.group(1)), True
    if m_list:
        return ("playlist", m_list.group(1)), True
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", val):
        return ("video", val), True
    return DEFAULT_YT, False


def to_youtube_embed_url(raw_url: str):
    (kind, yt_id), recognized = parse_youtube_resource(raw_url)
    if kind == "playlist":
        url = f"https://www.youtube.com/embed/videoseries?list={yt_id}&rel=0&playsinline=1&enablejsapi=1"
    else:
        url = f"https://www.youtube.com/embed/{yt_id}?rel=0&playsinline=1&enablejsapi=1"
    return url, recognized


def escape_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


MONO = "ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace"
BOX = (
    "z-index:9500;background:#17121b;border:none;border-radius:10px;padding:14px;max-width:90vw;"
)
st.html(
    "<style>"
    "#MainMenu,footer,header,[data-testid='stToolbar'],[data-testid='stDecoration']{display:none!important;}"
    "html,body,.stApp{width:100vw;height:100vh;overflow:hidden;"
    "background:radial-gradient(circle at 50% 45%,#140d18 0%,#040305 100%);color:#f4eef2;}"
    ".block-container{padding:0!important;margin:0!important;max-width:100%!important;}"
    ".anna-header{position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:20;"
    "text-align:center;width:92%;max-width:920px;pointer-events:none;}"
    f".anna-title{{font-family:{MONO};font-size:clamp(0.9rem,1.9vw,1.32rem);color:#ffd6e0;letter-spacing:0.1em;}}"
    f".anna-dedica{{margin-top:3px;font-family:{MONO};font-size:clamp(0.8rem,1.4vw,0.95rem);color:#cbb8c4;}}"
    ".anna-stage{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;"
    "padding:8px;z-index:10;pointer-events:none;}"
    f"pre.anna-3d{{margin:0;font-family:{MONO};font-size:clamp(8px,1.15vw,13px);line-height:1.0;"
    "letter-spacing:0.01em;white-space:pre;text-align:center;}"
    # box player (destra)
    ".st-key-player_box{position:fixed!important;right:24px;top:50%;transform:translateY(-50%);"
    f"width:332px!important;gap:0.5rem!important;{BOX}}}"
    # dimensioni bloccate SOLO per l'iframe di YouTube (non per i componenti di controllo)
    ".st-key-player_box iframe[src*='youtube']{width:304px!important;max-width:100%!important;"
    "height:172px!important;border:none!important;border-radius:8px!important;display:block!important;}"
    # box citazioni (sinistra)
    ".st-key-quotes_box{position:fixed!important;left:24px;top:50%;transform:translateY(-50%);"
    f"width:290px!important;gap:0.7rem!important;{BOX}}}"
    f".anna-sp-head{{font-family:{MONO};font-size:0.78rem;color:#ffd6e0;letter-spacing:0.04em;}}"
    f".anna-sp-note{{font-family:{MONO};font-size:0.71rem;color:#b9a8b5;line-height:1.35;}}"
    ".anna-sp-warn{color:#f5c28b;}"
    ".q-wrap{display:grid;min-height:64px;align-items:center;}"
    f".q-item{{grid-area:1/1;font-family:{MONO};font-size:0.86rem;line-height:1.55;color:#e9e0e6;opacity:0;}}"
    f".q-empty{{font-family:{MONO};font-size:0.76rem;line-height:1.45;color:#a99aa4;}}"
    f".anna-foot{{position:fixed;left:24px;bottom:22px;z-index:20;max-width:60vw;pointer-events:none;"
    f"font-family:{MONO};font-size:clamp(0.7rem,1.1vw,0.82rem);color:#a99aa4;line-height:1.4;}}"
    # input / textarea
    ".st-key-player_box [data-baseweb='input'],.st-key-player_box [data-baseweb='base-input'],"
    ".st-key-quotes_box [data-baseweb='textarea'],.st-key-quotes_box [data-baseweb='base-input']{"
    "background-color:#251e2a!important;border:none!important;border-radius:6px!important;box-shadow:none!important;}"
    ".st-key-player_box input,.st-key-quotes_box textarea{background:#251e2a!important;color:#e9e0e6!important;"
    "font-size:0.78rem!important;padding:7px 10px!important;}"
    ".st-key-player_box label,.st-key-quotes_box label{color:#a99aa4!important;font-size:0.72rem!important;}"
    ".st-key-quotes_box [data-testid='stExpander'] details{border:none!important;background:transparent!important;}"
    ".st-key-quotes_box [data-testid='stExpander'] summary{color:#a99aa4!important;font-size:0.74rem!important;"
    "padding:0!important;}"
    ".st-key-quotes_box [data-testid='stExpanderDetails']{padding:8px 0 0 0!important;}"
    # bottone
    ".st-key-cambia_fiori_btn{position:fixed!important;right:24px;bottom:24px;z-index:9999;width:auto!important;}"
    ".st-key-cambia_fiori_btn button,.st-key-quotes_box button{border:none!important;border-radius:8px!important;"
    "background:#251e2a!important;color:#d9ccd4!important;font-weight:500!important;padding:8px 14px!important;"
    "box-shadow:none!important;outline:none!important;}"
    ".st-key-cambia_fiori_btn button{background:#17121b!important;padding:9px 16px!important;}"
    ".st-key-cambia_fiori_btn button p,.st-key-quotes_box button p{color:#d9ccd4!important;}"
    ".st-key-cambia_fiori_btn button:hover,.st-key-quotes_box button:hover,"
    ".st-key-cambia_fiori_btn button:focus,.st-key-quotes_box button:focus,"
    ".st-key-cambia_fiori_btn button:active,.st-key-quotes_box button:active{"
    "background:#31283a!important;border:none!important;outline:none!important;box-shadow:none!important;}"
    # uploader audio
    ".st-key-quotes_box [data-testid='stFileUploaderDropzone']{background:#251e2a!important;border:none!important;"
    "border-radius:6px!important;}"
    ".st-key-quotes_box [data-testid='stFileUploaderDropzone'] small,"
    ".st-key-quotes_box [data-testid='stFileUploaderDropzone'] span,"
    ".st-key-quotes_box [data-testid='stFileUploaderFile'] *{color:#a99aa4!important;font-size:0.72rem!important;}"
    "@media (max-width: 980px){.st-key-player_box,.st-key-quotes_box{display:none!important;}}"
    "</style>"
)

# ----------------------------------------------------------------------------
# Parametri scena
# ----------------------------------------------------------------------------
SPIN_SPEED = 0.90
TIME_STEP = 0.035
FRAME_SLEEP = 0.09

TILT = 0.28
CAM_DIST = 3.85
PIVOT_Y = 0.20
COLS = 124
ROWS = 52

# costanti di proiezione (calcolate una volta sola)
SCALE = max(1.0, min((ROWS - 2) / 1.42, (COLS - 2) / 2.65))
SX_SCALE = SCALE * 2.05
CX = COLS / 2
CY = 1 + 0.80 * SCALE
CT, SN = math.cos(TILT), math.sin(TILT)

WHITE = ["#f4f8fb", "#eef3f7", "#e6edf3", "#dce5ed", "#d2dde7", "#ffffff"]
PINK = ["#7d2e56", "#9e4770", "#bd5f8a", "#d97aa6", "#f097c0", "#ffb8d9", "#ffd6e8"]
RED = ["#591423", "#7d1c31", "#a3243f", "#c92c4e", "#e83b60", "#ff5c7e", "#ff9eb3"]
PURPLE = ["#3b1d5e", "#542a82", "#6d39a6", "#874cc7", "#a46be0", "#c699f5", "#e2c7ff"]
YELLOW = ["#8a6d1b", "#ad8a24", "#cf9e2b", "#ebb834", "#ffd147", "#fff08a", "#fff9c4"]
ORANGE = ["#853b16", "#a84c1d", "#cc5d24", "#eb6f2d", "#ff8a47", "#ffb07a", "#ffd4b5"]
GOLD_CENTER = ["#6e5314", "#94701c", "#ba8d24", "#deb034", "#ffd447"]
DARK_CENTER = ["#381018", "#541824", "#732232", "#942d41", "#b53a52"]

TULIP_CRIMSON = ["#590d22", "#800f2f", "#a4133c", "#c9184a", "#ff4d6d", "#ff758f", "#ffb3c1"]
TULIP_ROSE = ["#691e46", "#8c285d", "#b03376", "#d44291", "#f263b0", "#ff8ec9", "#ffc2e2"]
TULIP_SUNSET = ["#7a2812", "#a33516", "#cc441b", "#eb5821", "#ff7733", "#ff9e5e", "#ffc494"]
TULIP_GOLD = ["#7a5c0f", "#9e7814", "#c4961a", "#e6b322", "#ffd230", "#ffe46b", "#fff3b0"]
TULIP_LILAC = ["#3c1663", "#56208c", "#722cb5", "#8e3cdb", "#ac5ef7", "#c98cff", "#e5c2ff"]
TULIP_CORAL = ["#7a1c2e", "#a1243c", "#c72e4b", "#eb3d5e", "#ff5c7a", "#ff8a9e", "#ffc2cc"]
TULIP_PALETTES = [TULIP_CRIMSON, TULIP_ROSE, TULIP_SUNSET, TULIP_GOLD, TULIP_LILAC, TULIP_CORAL]

DISC_TYPES = [
    (WHITE, GOLD_CENTER, 13),
    (PINK, GOLD_CENTER, 8),
    (RED, DARK_CENTER, 6),
    (PURPLE, GOLD_CENTER, 7),
    (YELLOW, DARK_CENTER, 12),
    (ORANGE, DARK_CENTER, 9),
]
MIXED_TULIP_COLORS = [RED, PINK, YELLOW]

PISTIL_PALETTE = ["#5c3a00", "#8a5a00", "#bd7e00", "#e8a817", "#ffd038", "#fff08a"]
GREENS = ["#15381c", "#1d4d26", "#256130", "#2f783c", "#3c914a", "#4fad5d", "#6bc777", "#8ee098"]
PAPER = ["#66523c", "#82684d", "#a18261", "#bf9c77", "#dbb78f", "#f2d5b1", "#fff0db"]
RIBBON = ["#611329", "#871b39", "#ad244b", "#d1305e", "#f24979", "#ff759c", "#ffa8c2"]
SPARK_COLORS = ["#b84d78", "#d66592", "#eb82ab", "#f7a3c4", "#ffd1e3", "#fff0f6"]

SHADE = ".:-=+*%@"
SHADE_ARR = np.array(list(SHADE))
PETAL_SHADE = "+*#%@"

_L = (-0.45, 0.62, 0.64)
_n = math.sqrt(sum(v * v for v in _L))
LX, LY, LZ = (v / _n for v in _L)


# ----------------------------------------------------------------------------
# Geometria
# ----------------------------------------------------------------------------
def norm(v):
    m = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2) or 1.0
    return (v[0] / m, v[1] / m, v[2] / m)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def add(p, d, k):
    return (p[0] + d[0] * k, p[1] + d[1] * k, p[2] + d[2] * k)


def build_common_structure(rnd, num_heads, spread_r, leaf_count):
    pts = []
    neck = (0.0, -0.14, 0.0)
    center_pt = (0.0, 0.14, 0.0)

    golden = math.pi * (3 - math.sqrt(5))
    az_offset = rnd.uniform(0.0, math.pi * 2)
    heads = []
    for i in range(num_heads):
        el = math.radians(87 - 60 * math.sqrt(i / max(1, num_heads - 1)))
        az = az_offset + i * golden + rnd.uniform(-0.24, 0.24)
        d = norm((math.cos(el) * math.cos(az), math.sin(el), math.cos(el) * math.sin(az)))
        pos = add(center_pt, d, spread_r * rnd.uniform(0.90, 1.12))
        heads.append((pos, d))

    # steli
    for pos, axis in heads:
        base = add(pos, axis, -0.04)
        ctrl = (
            (base[0] + neck[0]) * 0.5 + axis[0] * 0.06,
            (base[1] + neck[1]) * 0.5,
            (base[2] + neck[2]) * 0.5 + axis[2] * 0.06,
        )
        for j in range(56):
            u = j / 55
            inv = 1.0 - u
            px = inv * inv * base[0] + 2 * inv * u * ctrl[0] + u * u * neck[0]
            py = inv * inv * base[1] + 2 * inv * u * ctrl[1] + u * u * neck[1]
            pz = inv * inv * base[2] + 2 * inv * u * ctrl[2] + u * u * neck[2]
            pts.append((px, py, pz, axis[0], 0.0, axis[2], GREENS, -0.14, True, "|"))

    # foglie
    for i in range(leaf_count):
        a = i / leaf_count * 2 * math.pi + rnd.uniform(-0.16, 0.16)
        c, s = math.cos(a), math.sin(a)
        base = (0.24 * c, 0.24, 0.24 * s)
        d = norm((c, 0.20, s))
        side = (-s, 0.0, c)
        n = norm(cross(side, d))
        leaf_len = rnd.uniform(0.33, 0.44)
        leaf_w = 0.075
        for ti in range(26):
            u = ti / 25
            arch_drop = 0.13 * (u ** 1.7)
            for wi in range(-4, 5):
                w = wi / 4
                curl = 0.03 * (w * w) * math.sin(math.pi * u)
                px = base[0] + d[0] * leaf_len * u + side[0] * leaf_w * math.sin(math.pi * u) * w + n[0] * curl
                py = base[1] + d[1] * leaf_len * u - arch_drop + n[1] * curl
                pz = base[2] + d[2] * leaf_len * u + side[2] * leaf_w * math.sin(math.pi * u) * w + n[2] * curl
                rib = -0.25 if wi == 0 else (0.08 * abs(w))
                ch_leaf = "/" if wi == 0 and c >= 0 else ("\\" if wi == 0 else None)
                pts.append((px, py, pz, n[0], n[1], n[2], GREENS, rib, True, ch_leaf))

    # carta
    y0, y1, r0, r1 = -0.22, 0.30, 0.065, 0.40
    slope = (r1 - r0) / (y1 - y0)
    rings = 40
    for i in range(rings):
        u = i / (rings - 1)
        r = r0 + (r1 - r0) * u
        count = max(10, int(130 * r))
        for j in range(count):
            ph = (j + rnd.random()) / count * 2 * math.pi
            c, s = math.cos(ph), math.sin(ph)
            y = y0 + (y1 - y0) * u
            if u > 0.88:
                y += 0.035 * math.sin(11 * ph)
            fold = 0.32 * (abs(math.sin(6 * ph)) - 0.55)
            nn = norm((c, -slope, s))
            pts.append((r * c, y, r * s, nn[0], nn[1], nn[2], PAPER, fold, False, None))

    # steli sotto la carta
    for i in range(8):
        a = i / 8 * 2 * math.pi
        sx, sz = 0.028 * math.cos(a), 0.028 * math.sin(a)
        for j in range(28):
            u = j / 27
            pts.append((
                sx * (1 + 1.25 * u), -0.22 - 0.32 * u, sz * (1 + 1.25 * u),
                math.cos(a), 0.0, math.sin(a), GREENS, -0.1, True, None,
            ))

    # nastro
    by = -0.14
    br = r0 + slope * (by - y0) + 0.012
    for j in range(68):
        ph = j / 68 * 2 * math.pi
        for dy in (-0.014, 0.0, 0.014):
            pts.append((
                br * math.cos(ph), by + dy, br * math.sin(ph),
                math.cos(ph), 0.0, math.sin(ph), RIBBON, 0.05, False, "=",
            ))

    knot = (0.0, by, br + 0.012)
    for side in (-1, 1):
        for j in range(52):
            a = j / 52 * 2 * math.pi
            lx = side * (0.08 + 0.08 * math.cos(a))
            ly = 0.048 * math.sin(a) + 0.022 * (0.08 + 0.08 * math.cos(a)) / 0.16
            for fill in (1.0, 0.72, 0.42):
                pts.append((
                    knot[0] + lx * fill, knot[1] + ly * fill, knot[2] + 0.012,
                    side * 0.3, 0.2, 0.93, RIBBON, 0.12, True, None,
                ))
        for j in range(24):
            u = j / 23
            pts.append((
                knot[0] + side * 0.07 * u, knot[1] - 0.17 * u, knot[2] + 0.016,
                side * 0.2, 0.0, 0.98, RIBBON, -0.05 + 0.06 * math.sin(u * 10), True, None,
            ))

    for dx in (-0.012, 0.0, 0.012):
        pts.append((dx, by, knot[2] + 0.022, 0, 0, 1, RIBBON, 0.25, True, "@"))

    babies = []
    for _ in range(75):
        a = rnd.random() * 2 * math.pi
        el = rnd.uniform(0.25, 1.35)
        rr = rnd.uniform(0.42, 0.62)
        babies.append((
            rr * math.cos(a) * math.cos(el),
            center_pt[1] + rr * math.sin(el),
            rr * math.sin(a) * math.cos(el),
            rnd.uniform(0, 6.28),
        ))

    sparkles = []
    for _ in range(32):
        a = rnd.random() * 2 * math.pi
        rr = rnd.uniform(0.78, 1.04)
        sparkles.append((
            rr * math.cos(a), rnd.uniform(-0.32, 1.05), rr * math.sin(a),
            rnd.uniform(0, 6.28), rnd.uniform(1.5, 4.2),
        ))

    motes = []
    for _ in range(20):
        motes.append((
            rnd.random(), rnd.uniform(0.05, 0.98), rnd.uniform(0.025, 0.065),
            rnd.uniform(0, 6.28), rnd.choice(SPARK_COLORS),
        ))

    return pts, heads, babies, sparkles, motes


def prepare_scene(pts, flowers, babies, sparkles, motes):
    """Converte i punti statici in array numpy una volta sola (rendering vettoriale)."""
    n = len(pts)
    pos = np.empty((n, 3))
    nrm = np.empty((n, 3))
    tone = np.empty(n)
    two = np.empty(n, dtype=bool)
    ov = np.empty(n, dtype="<U1")
    off = np.empty(n, dtype=np.int64)
    plen = np.empty(n, dtype=np.int64)

    table, index = [], {}
    for i, (x, y, z, nx, ny, nz, pal, tn, ts, o) in enumerate(pts):
        key = tuple(pal)
        if key not in index:
            index[key] = (len(table), len(pal))
            table.extend(pal)
        pos[i] = (x, y, z)
        nrm[i] = (nx, ny, nz)
        tone[i] = tn
        two[i] = ts
        ov[i] = o or ""
        off[i], plen[i] = index[key]

    return {
        "pos": pos, "nrm": nrm, "tone": tone, "two": two, "ov": ov,
        "has_ov": ov != "", "off": off, "plen": plen, "table": table,
        "flowers": flowers, "babies": babies, "sparkles": sparkles, "motes": motes,
    }


@st.cache_resource(show_spinner=False, max_entries=8)
def build_mixed_bouquet(seed: int):
    rnd = random.Random(seed)
    pts, heads, babies, sparkles, motes = build_common_structure(
        rnd, num_heads=12, spread_r=0.68, leaf_count=10
    )
    tulip_slots = set(rnd.sample(range(len(heads)), k=3))
    flowers = []
    disc_pool = DISC_TYPES[:]
    rnd.shuffle(disc_pool)
    disc_i = 0

    for idx, (pos, _) in enumerate(heads):
        if idx in tulip_slots:
            t_pal = MIXED_TULIP_COLORS[idx % len(MIXED_TULIP_COLORS)]
            flowers.append((pos, "tulip", t_pal, None, 0,
                            rnd.uniform(0.13, 0.16), rnd.uniform(0.85, 1.18), rnd.uniform(0, 6.28)))
        else:
            petals, center_pal, n_pet = disc_pool[disc_i % len(disc_pool)]
            disc_i += 1
            flowers.append((pos, "disc", petals, center_pal, n_pet,
                            rnd.uniform(0.14, 0.175), 1.0, rnd.uniform(0, 6.28)))

    return prepare_scene(pts, flowers, babies, sparkles, motes)


@st.cache_resource(show_spinner=False, max_entries=8)
def build_tulip_bouquet(seed: int):
    rnd = random.Random(seed)
    pts, heads, babies, sparkles, motes = build_common_structure(
        rnd, num_heads=14, spread_r=0.69, leaf_count=12
    )
    pal_pool = TULIP_PALETTES[:]
    rnd.shuffle(pal_pool)
    flowers = []
    for idx, (pos, _) in enumerate(heads):
        t_pal = pal_pool[idx % len(pal_pool)]
        flowers.append((pos, "tulip", t_pal, None, 0,
                        rnd.uniform(0.14, 0.18), rnd.uniform(0.80, 1.25), rnd.uniform(0, 6.28)))

    return prepare_scene(pts, flowers, babies, sparkles, motes)


# ----------------------------------------------------------------------------
# Rendering
# ----------------------------------------------------------------------------
def render_scene_html(scene, t: float) -> str:
    N = ROWS * COLS
    ang = t * SPIN_SPEED
    ca, sa = math.cos(ang), math.sin(ang)

    # --- punti statici: tutto vettoriale -----------------------------------
    P, Nr = scene["pos"], scene["nrm"]
    xr = P[:, 0] * ca - P[:, 2] * sa
    zr = P[:, 0] * sa + P[:, 2] * ca
    yp = P[:, 1] - PIVOT_Y
    yt = yp * CT - zr * SN
    zt = yp * SN + zr * CT
    f = CAM_DIST / (CAM_DIST - zt)
    col = (CX + xr * f * SX_SCALE).astype(np.int64)
    row = (CY - yt * f * SCALE).astype(np.int64)

    nzr = Nr[:, 0] * sa + Nr[:, 2] * ca
    nxr = Nr[:, 0] * ca - Nr[:, 2] * sa
    nyt = Nr[:, 1] * CT - nzr * SN
    nzt = Nr[:, 1] * SN + nzr * CT
    dot = nxr * LX + nyt * LY + nzt * LZ
    dot = np.where(scene["two"] & (dot < 0), -dot * 0.58, dot)
    b = np.clip(0.26 + 0.74 * np.maximum(dot, 0.0) + scene["tone"], 0.0, 0.999)

    ch = np.where(scene["has_ov"], scene["ov"], SHADE_ARR[(b * len(SHADE)).astype(np.int64)])
    cidx = scene["off"] + (b * scene["plen"]).astype(np.int64)

    ok = (row >= 0) & (row < ROWS) & (col >= 0) & (col < COLS)
    flat = (row * COLS + col)[ok]
    zt, ch, cidx = zt[ok], ch[ok], cidx[ok]

    # z-buffer: per ogni cella vince il punto con z maggiore
    order = np.lexsort((zt, flat))
    fs = flat[order]
    last = np.empty(len(fs), dtype=bool)
    last[:-1] = fs[1:] != fs[:-1]
    last[-1] = True
    sel = order[last]

    zb = np.full(N, -1e9)
    cb = np.full(N, " ", dtype="<U1")
    kb = np.full(N, -1, dtype=np.int64)
    zb[flat[sel]] = zt[sel]
    cb[flat[sel]] = ch[sel]
    kb[flat[sel]] = cidx[sel]

    table = scene["table"]
    zbuf = zb.tolist()
    chars = cb.tolist()
    colors = [table[k] if k >= 0 else "#ffffff" for k in kb.tolist()]

    def plot(c, r, z, chr_, color):
        if 0 <= r < ROWS and 0 <= c < COLS:
            i = r * COLS + c
            if z > zbuf[i]:
                zbuf[i] = z
                chars[i] = chr_
                colors[i] = color

    def project(x, y, z):
        xr_ = x * ca - z * sa
        zr_ = x * sa + z * ca
        yp_ = y - PIVOT_Y
        yt_ = yp_ * CT - zr_ * SN
        zt_ = yp_ * SN + zr_ * CT
        f_ = CAM_DIST / (CAM_DIST - zt_)
        return CX + xr_ * f_ * SX_SCALE, CY - yt_ * f_ * SCALE, zt_, f_

    # --- polvere (solo dove non c'e' altro) ---------------------------------
    for mx, my, speed, phase, mcol in scene["motes"]:
        y_pos = (my - t * speed) % 0.96 + 0.02
        c = int((mx + 0.015 * math.sin(t * 1.2 + phase)) * COLS) % COLS
        r = int(y_pos * (ROWS - 1))
        plot(c, r, -50, "+" if int(phase * 10) % 2 == 0 else ".", mcol)

    # --- fiori ----------------------------------------------------------------
    for (x, y, z), kind, pal, cpal, n_pet, rad, openness, fseed in scene["flowers"]:
        fx, fy, zf, fp = project(x, y, z)
        dim = -0.35 * (1 - min(1.0, max(0.0, (zf + 0.65) / 1.3)))
        rot = fseed + ang * 0.35
        lp = len(pal)

        if kind == "disc":
            rx = rad * fp * SX_SCALE
            ry = rad * fp * SCALE
            lc = len(cpal)
            for r in range(int(fy - ry) - 2, int(fy + ry) + 3):
                if not 0 <= r < ROWS:
                    continue
                dy = (r + 0.5 - fy) / max(0.01, ry)
                for c in range(int(fx - rx) - 2, int(fx + rx) + 3):
                    dx = (c + 0.5 - fx) / max(0.01, rx)
                    s = math.sqrt(dx * dx + dy * dy)
                    if s > 1.0:
                        continue
                    if s < 0.30:
                        bb = min(0.999, max(0.0, 0.58 - 0.32 * dx - 0.32 * dy + dim))
                        plot(c, r, zf + 0.06, "@" if s < 0.16 else "o", cpal[int(bb * lc)])
                        continue
                    ph = math.atan2(dy, dx)
                    reach = 0.32 + 0.68 * abs(math.cos(n_pet * (ph + rot) / 2)) ** 0.7
                    if s > reach:
                        continue
                    edge = -0.22 if s > reach - 0.14 else 0.0
                    bb = min(0.999, max(0.0, 0.64 - 0.22 * dx - 0.28 * dy + 0.12 * s + edge + dim))
                    plot(c, r, zf + 0.04 * (1 - s), PETAL_SHADE[int(bb * len(PETAL_SHADE))], pal[int(bb * lp)])
        else:
            rx = rad * fp * SX_SCALE * openness
            ry = rad * fp * SCALE * 1.15
            sin_rot = math.sin(rot) * 0.35
            for r in range(int(fy - ry) - 2, int(fy + ry) + 3):
                if not 0 <= r < ROWS:
                    continue
                dy = (r + 0.5 - fy) / max(0.01, ry)
                v = (1.0 - dy) * 0.5
                if v < -0.05 or v > 1.05:
                    continue
                base_hw = 0.68 * math.sin(math.pi * 0.55 * min(1.0, max(0.0, v * 1.35 + 0.08)))
                if base_hw <= 0.01:
                    continue
                for c in range(int(fx - rx) - 2, int(fx + rx) + 3):
                    dx = (c + 0.5 - fx) / max(0.01, rx)
                    xn = dx / base_hw
                    axn = abs(xn)
                    if axn > 1.04:
                        continue
                    crown_limit = 0.68 + 0.32 * math.cos(1.5 * math.pi * xn + sin_rot) ** 2
                    if v > crown_limit:
                        continue
                    if axn < 0.34 and 0.48 < v < crown_limit - 0.04:
                        pistil_d = math.sqrt((xn / 0.34) ** 2 + ((v - 0.62) / 0.18) ** 2)
                        if pistil_d < 0.45:
                            b_p = min(0.999, max(0.0, 0.72 - 0.3 * pistil_d + dim))
                            plot(c, r, zf + 0.06, "@" if pistil_d < 0.22 else "*",
                                 PISTIL_PALETTE[int(b_p * len(PISTIL_PALETTE))])
                            continue
                    seam_dist = min(abs(axn - 0.35), abs(axn - 0.72))
                    on_seam = seam_dist < 0.075 and v > 0.22
                    seam = -0.24 if on_seam else 0.0
                    edge_shade = -0.18 if (axn > 0.90 or v > crown_limit - 0.07) else 0.0
                    vein = 0.08 if abs(math.sin(6.0 * xn)) > 0.94 else 0.0
                    bb = min(0.999, max(0.0, 0.58 - 0.28 * xn + 0.12 * v + seam + edge_shade + vein + dim))
                    if on_seam:
                        ch_pet = "|"
                    elif axn > 0.90:
                        ch_pet = ")" if xn > 0 else "("
                    else:
                        ch_pet = PETAL_SHADE[int(bb * len(PETAL_SHADE))]
                    plot(c, r, zf + 0.04 * (1.0 - 0.3 * axn), ch_pet, pal[int(bb * lp)])

    # --- stelline ---------------------------------------------------------------
    for x, y, z, phase in scene["babies"]:
        fx, fy, zz, _ = project(x, y, z)
        star = math.sin(t * 2.1 + phase) > 0.55
        plot(int(fx), int(fy), zz + 0.02, "*" if star else ".", "#fff5f9" if star else "#e0d4dc")

    for x, y, z, phase, speed in scene["sparkles"]:
        fx, fy, zz, _ = project(x, y, z)
        tw = math.sin(t * speed + phase)
        if tw > 0.85:
            plot(int(fx), int(fy), zz, "*", "#ffffff")
        elif tw > 0.42:
            plot(int(fx), int(fy), zz, "+", "#ffbfd9")
        elif tw > 0.05:
            plot(int(fx), int(fy), zz, ".", "#e08eb0")

    # --- output HTML (i caratteri usati non richiedono escape) ------------------
    lines = []
    for r in range(ROWS):
        base = r * COLS
        parts = []
        last_col = None
        for c in range(COLS):
            chr_ = chars[base + c]
            if chr_ != " ":
                cc = colors[base + c]
                if cc != last_col:
                    if last_col is not None:
                        parts.append("</span>")
                    parts.append(f'<span style="color:{cc}">')
                    last_col = cc
            parts.append(chr_)
        if last_col is not None:
            parts.append("</span>")
        lines.append("".join(parts))

    return "\n".join(lines)


# ----------------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------------
# Controlli volume/muto: girano interamente nel browser (nessun rerun di Streamlit)
# e parlano con l'iframe di YouTube via postMessage. Il componente e' same-origin
# con la pagina, quindi puo' trovare l'iframe del player con window.parent.
CONTROLS_HTML = """
<style>
html,body{margin:0;background:transparent;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;
font-size:12px;color:#a99aa4}
.row{display:flex;align-items:center;gap:10px;height:36px}
button{background:#251e2a;color:#d9ccd4;border:none;border-radius:6px;padding:7px 12px;font:inherit;
cursor:pointer;min-width:58px}
button:hover{background:#31283a;color:#f4eef2}
input[type=range]{flex:1;min-width:0;accent-color:#bfa6b4;cursor:pointer}
#n{width:26px;text-align:right}
</style>
<div class="row">
  <button id="m" type="button">Muto</button>
  <input id="v" type="range" min="0" max="100" value="60" aria-label="Volume">
  <span id="n">60</span>
</div>
<script>
(function () {
  var vol = 60, muted = false, lastEl = null;
  var v = document.getElementById("v"), n = document.getElementById("n"), m = document.getElementById("m");

  function findPlayer() {
    try { return window.parent.document.querySelector(".st-key-player_box iframe[src*='youtube']"); }
    catch (e) { return null; }
  }
  function send(ifr, obj) {
    try { ifr.contentWindow.postMessage(JSON.stringify(obj), "*"); } catch (e) {}
  }
  function apply() {
    var ifr = findPlayer();
    if (!ifr) return;
    send(ifr, {event: "listening", id: 1, channel: "widget"});
    send(ifr, {event: "command", func: muted ? "mute" : "unMute", args: []});
    send(ifr, {event: "command", func: "setVolume", args: [vol]});
  }
  // il player ci mette un attimo a essere pronto dopo il caricamento
  function burst() { [0, 500, 1500, 3000].forEach(function (d) { setTimeout(apply, d); }); }

  v.addEventListener("input", function () {
    vol = +v.value; n.textContent = vol;
    if (vol > 0 && muted) { muted = false; m.textContent = "Muto"; }
    apply();
  });
  m.addEventListener("click", function () {
    muted = !muted; m.textContent = muted ? "Audio" : "Muto";
    apply();
  });

  // se l'iframe viene ricreato o cambia link, riapplica volume e muto
  setInterval(function () {
    var ifr = findPlayer();
    if (ifr && ifr !== lastEl) { lastEl = ifr; ifr.addEventListener("load", burst); burst(); }
  }, 700);
})();
</script>
"""


CAROUSEL_TEMPLATE = """
<style>
html,body{margin:0;background:transparent;font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace;
font-size:12px;color:#a99aa4;overflow:hidden}
.stage{display:grid;cursor:pointer;user-select:none;-webkit-user-select:none}
.slide{grid-area:1/1;opacity:0;pointer-events:none;transition:opacity .35s ease;display:flex;
flex-direction:column;justify-content:center}
.slide.on{opacity:1;pointer-events:auto}
.q{font-size:13.8px;line-height:1.55;color:#e9e0e6}
.at{color:#e9e0e6;margin-bottom:8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.row{display:flex;align-items:center;gap:10px}
.pp{background:#251e2a;color:#d9ccd4;border:none;border-radius:6px;padding:6px 0;width:56px;font:inherit;
cursor:pointer;flex:none}
.pp:hover{background:#31283a;color:#f4eef2}
.seek{flex:1;min-width:0;margin:0;accent-color:#bfa6b4;cursor:pointer;height:12px}
.time{width:34px;text-align:right;flex:none}
.foot{display:flex;justify-content:space-between;margin-top:10px;color:#7f7280;font-size:11px}
</style>
<div class="stage" id="stage">__SLIDES__</div>
<div class="foot"><span id="cnt"></span><span>clicca per andare avanti</span></div>
<script>
(function () {
  var INTERVAL = __INTERVAL__;
  var stage = document.getElementById("stage"), cnt = document.getElementById("cnt");
  var slides = [].slice.call(document.querySelectorAll(".slide"));
  var i = 0, timer = null, hover = false;

  function fmt(s) {
    if (!isFinite(s)) return "0:00";
    var m = Math.floor(s / 60), r = Math.floor(s % 60);
    return m + ":" + (r < 10 ? "0" : "") + r;
  }
  function audios() { return slides.map(function (s) { return s.querySelector("audio"); }).filter(Boolean); }
  function anyPlaying() { return audios().some(function (a) { return !a.paused; }); }
  function stopAudio(except) { audios().forEach(function (a) { if (a !== except && !a.paused) a.pause(); }); }
  // mentre parte un vocale, mette in pausa la musica di YouTube
  function pauseMusic() {
    try {
      var ifr = window.parent.document.querySelector(".st-key-player_box iframe[src*='youtube']");
      if (ifr) ifr.contentWindow.postMessage(JSON.stringify({event: "command", func: "pauseVideo", args: []}), "*");
    } catch (e) {}
  }
  function restart() {
    clearInterval(timer);
    if (slides.length < 2) return;
    timer = setInterval(function () { if (!hover && !anyPlaying()) show(i + 1); }, INTERVAL);
  }
  function show(n) {
    i = (n + slides.length) % slides.length;
    slides.forEach(function (s, k) { s.classList.toggle("on", k === i); });
    cnt.textContent = (i + 1) + " / " + slides.length;
    restart();
  }

  slides.forEach(function (sl) {
    var a = sl.querySelector("audio");
    if (!a) return;
    var b = sl.querySelector(".pp"), sk = sl.querySelector(".seek"), t = sl.querySelector(".time");
    b.addEventListener("click", function () {
      if (a.paused) { stopAudio(a); pauseMusic(); a.play(); } else { a.pause(); }
    });
    a.addEventListener("play", function () { b.textContent = "Pausa"; });
    a.addEventListener("pause", function () { b.textContent = "Play"; });
    a.addEventListener("ended", function () { b.textContent = "Play"; sk.value = 0; t.textContent = fmt(a.duration); });
    a.addEventListener("loadedmetadata", function () { t.textContent = fmt(a.duration); });
    a.addEventListener("timeupdate", function () {
      if (a.duration) { sk.value = Math.round(a.currentTime / a.duration * 1000); t.textContent = fmt(a.currentTime); }
    });
    sk.addEventListener("input", function () { if (a.duration) a.currentTime = sk.value / 1000 * a.duration; });
  });

  stage.addEventListener("click", function (e) {
    if (e.target.closest && e.target.closest(".pp, .seek")) return;
    stopAudio(null);
    show(i + 1);
  });
  stage.addEventListener("mouseenter", function () { hover = true; });
  stage.addEventListener("mouseleave", function () { hover = false; restart(); });

  show(0);
})();
</script>
"""


def carousel_slides(quotes, audios):
    """Alterna citazioni scritte e vocali, cosi' non finiscono tutti insieme."""
    out = []
    for k in range(max(len(quotes), len(audios))):
        if k < len(quotes):
            out.append(("q", quotes[k]))
        if k < len(audios):
            out.append(("a", audios[k]))
    return out


def carousel_html(quotes, audios):
    parts = []
    for kind, item in carousel_slides(quotes, audios):
        if kind == "q":
            parts.append(f'<div class="slide"><div class="q">“{escape_html(item)}”</div></div>')
        else:
            uri = audio_data_uri(str(item), item.stat().st_mtime)
            parts.append(
                f'<div class="slide"><div class="at">{escape_html(audio_title(item))}</div>'
                '<div class="row"><button class="pp" type="button">Play</button>'
                '<input class="seek" type="range" min="0" max="1000" value="0" aria-label="Posizione">'
                '<span class="time">0:00</span></div>'
                f'<audio preload="metadata" src="{uri}"></audio></div>'
            )
    return (
        CAROUSEL_TEMPLATE.replace("__SLIDES__", "".join(parts))
        .replace("__INTERVAL__", str(QUOTE_SECONDS * 1000))
    )


def carousel_height(quotes, audios):
    lines = max((math.ceil(len(q) / 27) for q in quotes), default=0)
    body = max(lines * 22, 62 if audios else 0, 60)
    return min(body, 300) + 32


if st.session_state.mode == "mixed":
    etichetta = "Bouquet al Volo"
    scene = build_mixed_bouquet(st.session_state.seed_mixed)
else:
    etichetta = "Bouquet di Tulipani"
    scene = build_tulip_bouquet(st.session_state.seed_tulips)

titolo_alto = "Per Anna e Misha - Supporto morale - Forza Giugliano"
st.html(
    f'<div class="anna-header"><div class="anna-title">{escape_html(titolo_alto)}</div>'
    f'<div class="anna-dedica">{escape_html(etichetta)}</div></div>'
)

with st.container(key="player_box"):
    st.html('<div class="anna-sp-head">Annateca</div>')
    st.text_input(
        "Incolla qua il link, spremi Invio e schiacc Play.",
        key="yt_url",
        placeholder="https://www.youtube.com/watch?v=...",
    )
    embed_url, recognized = to_youtube_embed_url(st.session_state.yt_url)

    # iframe con src diretto: YouTube vuole un referrer valido
    components.iframe(embed_url, width=304, height=172)
    components.html(CONTROLS_HTML, height=40)

    if recognized:
        st.html('<div class="anna-sp-note">Playlist caricata pare</div>')
    else:
        st.html(
            '<div class="anna-sp-note anna-sp-warn">Anna stu link nun funzion: metto il video predefinito ja lasc sta. '
            "Metti il link qua <code>youtube.com/watch?v=...</code> o <code>youtu.be/...</code> e premi Invio.</div>"
        )

quotes = [ln.strip() for ln in st.session_state.quotes_text.splitlines() if ln.strip()]
audios = list_audio()
with st.container(key="quotes_box"):
    st.html('<div class="anna-sp-head">Perle dette dalla signorina</div>')
    if quotes or audios:
        components.html(carousel_html(quotes, audios), height=carousel_height(quotes, audios))
    else:
        st.html('<div class="q-empty">Ancor nient.</div>')
    with st.expander("Modifica citazioni e audio"):
        st.text_area(
            "Una citazione per riga (clicca fuori dal campo per salvare)",
            key="quotes_text",
            height=150,
            on_change=save_quotes_callback,
        )
        uploaded = st.file_uploader(
            "Aggiungi audio (WhatsApp .opus, .mp3, .m4a, .ogg, .wav, .aac)",
            type=[ext.lstrip(".") for ext in AUDIO_TYPES],
            accept_multiple_files=True,
            key=f"audio_up_{st.session_state.audio_up_key}",
        )
        if uploaded:
            for f in uploaded:
                save_audio(f)
            st.session_state.audio_up_key += 1
            st.rerun()
        for p in audios:
            if st.button(f"Elimina: {audio_title(p)}", key=f"del_{p.name}"):
                try:
                    p.unlink()
                except Exception:
                    pass
                st.rerun()

st.html(
    '<div class="anna-foot">Fatto in una serata uggiosa mentre giocavo a Zelda, '
    "forza Giugliano. Misha ti mangio</div>"
)

st.button("Cambia bouquet", key="cambia_fiori_btn", on_click=cambia_fiori_callback)

stage = st.empty()

while True:
    t0 = time.perf_counter()
    frame_html = render_scene_html(scene, st.session_state.sim_t)
    stage.html(f'<div class="anna-stage"><pre class="anna-3d">{frame_html}</pre></div>')
    st.session_state.sim_t += TIME_STEP
    time.sleep(max(0.0, FRAME_SLEEP - (time.perf_counter() - t0)))