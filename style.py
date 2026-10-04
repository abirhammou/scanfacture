"""CSS partagé injecté dans chaque page secondaire."""

import streamlit as st


def inject(page_title: str = "", page_icon: str = "🧾"):
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {{
    background: #0a0c14 !important;
    font-family: 'Inter', sans-serif;
}}
[data-testid="stHeader"] {{ background: transparent !important; }}

.main .block-container {{
    max-width: 960px !important;
    margin: 0 auto !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] {{
    background: #0d1025 !important;
    border-right: 1px solid #1e2438 !important;
}}

.nav-label {{
    font-size: .65rem;
    font-weight: 700;
    color: #3a4060 !important;
    text-transform: uppercase;
    letter-spacing: .12em;
    padding: 0 .5rem;
    margin-bottom: .4rem;
}}

[data-testid="stSidebarNav"] a {{
    display: flex !important;
    align-items: center !important;
    gap: .7rem !important;
    padding: .65rem 1rem !important;
    border-radius: 10px !important;
    font-size: .9rem !important;
    font-weight: 500 !important;
    color: #7a82a8 !important;
    text-decoration: none !important;
    transition: background .18s, color .18s !important;
    margin-bottom: .2rem !important;
}}
[data-testid="stSidebarNav"] a:hover {{
    background: #171c35 !important;
    color: #c4c9e8 !important;
}}
[data-testid="stSidebarNav"] a[aria-current="page"] {{
    background: linear-gradient(135deg, #1e1a4a, #162040) !important;
    color: #a78bfa !important;
    border: 1px solid #6c63ff44 !important;
    font-weight: 700 !important;
}}
[data-testid="stSidebarNav"] ul {{ padding: 0 !important; }}

/* ── Titres et textes ── */
h1, h2, h3 {{ color: #dde1f7 !important; }}
p, label, div {{ color: #9099ba; }}

/* ── Widgets Streamlit ── */
[data-testid="stFileUploader"] {{
    background: #111428 !important;
    border: 1px dashed #2a2f4a !important;
    border-radius: 12px !important;
}}
.stTextArea textarea, .stTextInput input {{
    background: #111428 !important;
    border: 1px solid #1e2438 !important;
    border-radius: 10px !important;
    color: #dde1f7 !important;
}}
.stButton button {{
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: transform .15s, box-shadow .15s !important;
}}
.stButton button:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 16px #6c63ff33 !important;
}}
[data-testid="stMetricValue"] {{
    color: #a78bfa !important;
    font-weight: 800 !important;
}}

/* ── Sidebar logo ── */
.sidebar-logo {{
    text-align: center;
    padding: 1rem 0 1.6rem;
    border-bottom: 1px solid #1e2438;
    margin-bottom: 1.2rem;
}}
.sidebar-logo-icon {{
    font-size: 2.4rem;
    display: block;
    filter: drop-shadow(0 0 10px #6c63ff88);
}}
.sidebar-logo-title {{
    font-size: 1.2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #6c63ff, #38bdf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}}

/* ── Sidebar footer ── */
.sidebar-footer {{
    margin-top: 2rem;
    text-align: center;
    font-size: .68rem;
    color: #252d45;
    border-top: 1px solid #1a2035;
    padding-top: .8rem;
}}
.sidebar-footer span {{ color: #6c63ff77; }}
</style>
""", unsafe_allow_html=True)

    with st.sidebar:
        pass
