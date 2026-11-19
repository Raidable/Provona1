import random
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Per Anna 🌸", page_icon="💐", layout="centered")

st.markdown(
    """
    <style>
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 1.5rem; padding-bottom: 1.5rem; max-width: 560px;}
    </style>
    """,
    unsafe_allow_html=True,
)

if "seed" not in st.session_state:
    st.session_state.seed = random.randint(1, 10**7)

dediche = [
    "Un bouquet digitale che sboccia diverso ogni volta che lo guardi.",
    "Per Anna: un po' di colore e leggerezza, ovunque tu sia.",
    "Fiori che non appassiscono mai. ✨",
]
dedica = dediche[st.session_state.seed % len(dediche)]

html_bouquet = f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body {{
    margin: 0;
    background: transparent;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
    color: #4a3f42;
  }}
  canvas {{
    width: 100%;
    max-width: 440px;
    height: auto;
    border-radius: 24px;
    background: #faf6f0;
    box-shadow: 0 12px 30px rgba(74, 63, 66, 0.08);
    cursor: pointer;
    touch-action: manipulation;
  }}
  .dedica {{
    margin-top: 14px;
    font-style: italic;
    font-size: 0.98rem;
    text-align: center;
    color: #6b585d;
    padding: 0 12px;
  }}
  .hint {{
    margin-top: 6px;
    font-size: 0.78rem;
    color: #9c888d;
  }}
</style>
</head>
<body>
  <canvas id="c" width="440" height="540"></canvas>
  <div class="dedica">«{dedica}»</div>
  <div class="hint">Tocca il bouquet per farlo sbocciare di nuovo</div>

<script>
const canvas = document.getElementById("c");
const ctx = canvas.getContext("2d");

let seed = {st.session_state.seed};
function mulberry32(a) {{
  return function() {{
    let t = a += 0x6D2B79F5;
    t = Math.imul(t ^ t >>> 15, t | 1);
    t ^= t + Math.imul(t ^ t >>> 7, t | 61);
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  }}
}}

const palettes = [
  {{ stem: "#587452", ribbon: "#d49a6a", petals: ["#e07a5f", "#f2a65a", "#e5989b", "#f4d35e"] }},
  {{ stem: "#4c6b5c", ribbon: "#b5838d", petals: ["#c97b84", "#e5989b", "#ffb4a2", "#9d8189"] }},
  {{ stem: "#5b6d3f", ribbon: "#c88a5b", petals: ["#d95d39", "#f0a202", "#f46036", "#fce181"] }},
  {{ stem: "#52796f", ribbon: "#9d4edd", petals: ["#9d4edd", "#c77dff", "#e0aaff", "#ff9ebb"] }},
];

let bouquet = [];
let palette = palettes[0];
let startTime = performance.now();

function buildBouquet(s) {{
  const rand = mulberry32(s);
  palette = palettes[Math.floor(rand() * palettes.length)];
  const count = 8 + Math.floor(rand() * 5); // 8-12 fiori
  const baseX = 220;
  const baseY = 475;
  const tieY = 365;

  bouquet = [];
  for (let i = 0; i < count; i++) {{
    const tNorm = count === 1 ? 0.5 : i / (count - 1);
    const spread = (tNorm - 0.5) * 260 + (rand() - 0.5) * 35;
    const topX = baseX + spread;
    const topY = 120 + Math.abs(tNorm - 0.5) * 110 + (rand() - 0.5) * 55;
    const ctrlX = baseX + spread * 0.45 + (rand() - 0.5) * 25;
    const ctrlY = (tieY + topY) * 0.52;

    bouquet.push({{
      baseX, baseY, tieY, ctrlX, ctrlY, topX, topY,
      radius: 26 + rand() * 18,
      petals: 5 + Math.floor(rand() * 4), // 5-8 petali
      color: palette.petals[Math.floor(rand() * palette.petals.length)],
      delay: i * 0.07 + rand() * 0.08,
      swayPhase: rand() * Math.PI * 2,
      swaySpeed: 1.2 + rand() * 0.8,
      rot: rand() * Math.PI * 2
    }});
  }}
  startTime = performance.now();
}}

function easeOutCubic(x) {{
  return 1 - Math.pow(1 - Math.min(Math.max(x, 0), 1), 3);
}}

function drawFlower(f, bloomProgress, sway) {{
  if (bloomProgress <= 0.01) return;
  const rMax = f.radius * bloomProgress;
  const fx = f.topX + sway;
  const fy = f.topY;

  ctx.save();
  ctx.translate(fx, fy);
  ctx.rotate(f.rot + sway * 0.015);

  for (let layer = 0; layer < 2; layer++) {{
    const scale = layer === 0 ? 1.0 : 0.68;
    const n = f.petals + layer;
    ctx.fillStyle = f.color;
    ctx.globalAlpha = layer === 0 ? 0.85 : 0.95;

    for (let p = 0; p < n; p++) {{
      const angle = (p / n) * Math.PI * 2 + layer * 0.35;
      ctx.save();
      ctx.rotate(angle);
      ctx.beginPath();
      ctx.ellipse(0, -rMax * 0.55 * scale, rMax * 0.34 * scale, rMax * 0.62 * scale, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }}
  }}

  // Centro del fiore
  ctx.globalAlpha = 1;
  ctx.fillStyle = "#fff3b0";
  ctx.beginPath();
  ctx.arc(0, 0, rMax * 0.2, 0, Math.PI * 2);
  ctx.fill();

  ctx.restore();
}}

function render(now) {{
  const elapsed = (now - startTime) / 1000;
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Steli
  for (const f of bouquet) {{
    const stemProg = easeOutCubic((elapsed - f.delay * 0.5) / 0.55);
    if (stemProg <= 0) continue;
    const sway = Math.sin(elapsed * f.swaySpeed + f.swayPhase) * 4.5 * bloomEase(elapsed, f.delay);

    ctx.save();
    ctx.strokeStyle = palette.stem;
    ctx.lineWidth = 3;
    ctx.lineCap = "round";
    ctx.globalAlpha = 0.88;
    ctx.beginPath();
    ctx.moveTo(f.baseX, f.baseY);
    const curCtrlX = f.ctrlX + sway * 0.4;
    const curTopX = f.topX + sway;
    const endX = f.baseX + (curTopX - f.baseX) * stemProg;
    const endY = f.baseY + (f.topY - f.baseY) * stemProg;
    ctx.quadraticCurveTo(curCtrlX, f.ctrlY, endX, endY);
    ctx.stroke();
    ctx.restore();
  }}

  // Nastro del bouquet
  const ribbonProg = easeOutCubic(elapsed / 0.5);
  if (ribbonProg > 0) {{
    ctx.save();
    ctx.strokeStyle = palette.ribbon;
    ctx.lineWidth = 7;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(220 - 38 * ribbonProg, 365);
    ctx.lineTo(220 + 38 * ribbonProg, 365);
    ctx.stroke();
    ctx.restore();
  }}

  // Fiori che sbocciano
  for (const f of bouquet) {{
    const bloomProg = easeOutCubic((elapsed - f.delay - 0.25) / 0.75);
    const sway = Math.sin(elapsed * f.swaySpeed + f.swayPhase) * 4.5 * bloomProg;
    drawFlower(f, bloomProg, sway);
  }}

  requestAnimationFrame(render);