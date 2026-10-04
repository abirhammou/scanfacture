"""ScanFacture — Page d'accueil."""

import streamlit as st

st.set_page_config(
    page_title="ScanFacture",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #0a0c14 !important;
    font-family: 'Inter', sans-serif;
}
[data-testid="stHeader"] { background: transparent !important; }

/* ── Centrage visuel dans la zone principale ── */
section[data-testid="stMain"] {
    display: flex !important;
    justify-content: center !important;
}
.main .block-container {
    max-width: 820px !important;
    width: 100% !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    padding-top: 0.5rem !important;
    padding-bottom: 0.5rem !important;
    margin: 0 !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0d1025 !important;
    border-right: 1px solid #1e2438 !important;
}
[data-testid="stSidebarNav"] a {
    padding: .65rem 1rem !important;
    border-radius: 10px !important;
    font-size: .88rem !important;
    font-weight: 500 !important;
    color: #7a82a8 !important;
    transition: background .18s, color .18s !important;
    margin-bottom: .2rem !important;
    display: block !important;
}
[data-testid="stSidebarNav"] a:hover {
    background: #171c35 !important;
    color: #c4c9e8 !important;
}
[data-testid="stSidebarNav"] a[aria-current="page"] {
    background: linear-gradient(135deg, #1e1a4a, #162040) !important;
    color: #a78bfa !important;
    border: 1px solid #6c63ff44 !important;
    font-weight: 700 !important;
}

/* ── Clock ── */
.clock-bar { display: none; }

/* ── Hero ── */
.hero { text-align: center; padding: 1rem 1rem .8rem; }
.hero-icon {
    font-size: 3.2rem; display: block; margin-bottom: .4rem;
    animation: glow 3s ease-in-out infinite;
}
@keyframes glow {
    0%,100% { filter: drop-shadow(0 0 16px #6c63ff55); }
    50%      { filter: drop-shadow(0 0 32px #a78bfa99); }
}
.hero h1 {
    font-size: 2.5rem; font-weight: 800;
    background: linear-gradient(135deg, #6c63ff, #a78bfa, #38bdf8);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0 0 .4rem; line-height: 1.1;
}
.hero p { font-size: 1rem; color: #7a82a8; margin: 0 auto; max-width: 460px; line-height: 1.7; }

/* ── Stats bar ── */
.stats-bar {
    display: flex; gap: 0;
    margin: 1.2rem auto 1.6rem;
    background: #111428; border: 1px solid #1e2438;
    border-radius: 14px; overflow: hidden;
}
.stat-item { flex:1; text-align:center; padding: 1rem; border-right: 1px solid #1e2438; }
.stat-item:last-child { border-right: none; }
.stat-value {
    font-size: 1.7rem; font-weight: 800;
    background: linear-gradient(135deg, #a78bfa, #38bdf8);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    display: block; line-height: 1.1;
}
.stat-label { font-size: .62rem; color: #444c6a; text-transform: uppercase; letter-spacing: .1em; margin-top: .25rem; }

/* ── Cards ── */
.cards-grid {
    display: grid; grid-template-columns: repeat(4,1fr);
    gap: .9rem; margin: 0 auto 1.6rem;
}
.card {
    background: #111428; border: 1px solid #1e2438;
    border-radius: 12px; padding: 1.2rem .9rem; text-align: center;
    transition: transform .2s, border-color .2s, box-shadow .2s;
}
.card:hover { transform: translateY(-4px); border-color: #6c63ff55; box-shadow: 0 6px 24px #6c63ff18; }
.card-icon { font-size: 1.7rem; margin-bottom: .5rem; display: block; }
.card-title { font-size: .88rem; font-weight: 700; color: #c4c9e8; margin-bottom: .3rem; }
.card-desc { font-size: .74rem; color: #555d7c; line-height: 1.55; }

/* ── Steps ── */
.divider { height:1px; background: linear-gradient(90deg,transparent,#1e2438,transparent); margin: 0 auto 1.5rem; }
.steps { display:flex; justify-content:center; gap:0; margin: 0 auto 1.8rem; }
.step { flex:1; text-align:center; position:relative; padding: 0 .4rem; }
.step:not(:last-child)::after {
    content:''; position:absolute; top:1rem; right:-8%; width:16%; height:2px;
    background: linear-gradient(90deg, #6c63ff44, #38bdf444);
}
.step-num {
    width:2rem; height:2rem;
    background: linear-gradient(135deg,#6c63ff,#38bdf8); border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    font-weight:800; font-size:.8rem; color:#fff; margin: 0 auto .45rem;
}
.step-text { font-size: .72rem; color: #555d7c; line-height:1.4; }

/* ── Footer ── */
.footer { text-align:center; color:#272e4a; font-size:.7rem; padding-bottom:1.2rem; }
.footer span { color:#6c63ff55; }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "factures" not in st.session_state:
    st.session_state.factures = []

nb = len(st.session_state.factures)
total = sum(f.get("total", 0) for f in st.session_state.factures)
devises = {f.get("devise", "") for f in st.session_state.factures if f.get("devise")}
devise_label = list(devises)[0] if len(devises) == 1 else ("multi" if devises else "—")

# ── Rendu ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
  <span class="hero-icon">🧾</span>
  <h1>ScanFacture</h1>
  <p>Transformez vos factures papier en données structurées en quelques secondes grâce à l'OCR et à l'IA Gemini.</p>
</div>

<div class="stats-bar">
  <div class="stat-item">
    <span class="stat-value">{nb}</span>
    <div class="stat-label">Factures analysées</div>
  </div>
  <div class="stat-item">
    <span class="stat-value">{total:,.2f}</span>
    <div class="stat-label">Total · {devise_label}</div>
  </div>
  <div class="stat-item">
    <span class="stat-value">2</span>
    <div class="stat-label">APIs connectées</div>
  </div>
</div>

<div class="cards-grid">
  <div class="card">
    <span class="card-icon">📤</span>
    <div class="card-title">Importer</div>
    <div class="card-desc">Uploadez un JPG, PNG ou PDF. L'OCR extrait le texte automatiquement.</div>
  </div>
  <div class="card">
    <span class="card-icon">🤖</span>
    <div class="card-title">Extraire</div>
    <div class="card-desc">Gemini analyse le texte et retourne un JSON structuré en un instant.</div>
  </div>
  <div class="card">
    <span class="card-icon">✅</span>
    <div class="card-title">Valider</div>
    <div class="card-desc">Contrôle des dates, montants et détection des doublons automatique.</div>
  </div>
  <div class="card">
    <span class="card-icon">📊</span>
    <div class="card-title">Analyser</div>
    <div class="card-desc">Statistiques mensuelles et par fournisseur, export CSV en un clic.</div>
  </div>
</div>

<div class="divider"></div>

<div class="steps">
  <div class="step">
    <div class="step-num">1</div>
    <div class="step-text">Importez<br>votre facture</div>
  </div>
  <div class="step">
    <div class="step-num">2</div>
    <div class="step-text">L'OCR lit<br>le texte</div>
  </div>
  <div class="step">
    <div class="step-num">3</div>
    <div class="step-text">Gemini<br>structure les données</div>
  </div>
  <div class="step">
    <div class="step-num">4</div>
    <div class="step-text">Exportez<br>en CSV</div>
  </div>
</div>

<div class="footer">
  ScanFacture · Propulsé par <span>OCR.space</span> &amp; <span>Google Gemini</span>
</div>
""", unsafe_allow_html=True)
