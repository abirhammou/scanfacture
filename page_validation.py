"""Page Streamlit – Validation & Tests des données extraites par Gemini."""

import csv
import io
import json
import subprocess
import sys

import streamlit as st

import validation
from validation import ErreurValidation

st.set_page_config(
    page_title="Validation – ScanFacture",
    page_icon="🔍",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Custom CSS – professional dark-card design
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ── Global ── */
[data-testid="stAppViewContainer"] {
    background: #0f1117;
}
[data-testid="stHeader"] { background: transparent; }

/* ── Section cards ── */
.section-card {
    background: #1a1d27;
    border: 1px solid #2a2d3e;
    border-radius: 12px;
    padding: 1.4rem 1.8rem;
    margin-bottom: 1.2rem;
}

/* ── Badge pill ── */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.badge-success { background:#0d4f2e; color:#2ecc71; }
.badge-error   { background:#4f1a1a; color:#e74c3c; }
.badge-warning { background:#4f3d0d; color:#f39c12; }
.badge-info    { background:#0d2f4f; color:#3498db; }

/* ── Metric cards ── */
.metric-row { display:flex; gap:1rem; margin-top:.8rem; }
.metric-card {
    flex:1; background:#12151f; border:1px solid #2a2d3e;
    border-radius:10px; padding:.9rem 1rem; text-align:center;
}
.metric-label { font-size:.7rem; color:#8a8fa8; text-transform:uppercase; letter-spacing:.06em; margin-bottom:.3rem; }
.metric-value { font-size:1.25rem; font-weight:700; color:#e8eaf6; }

/* ── Checklist items ── */
.check-item {
    display:flex; align-items:center; gap:.6rem;
    padding:.45rem 0; border-bottom:1px solid #1e2130; font-size:.88rem;
}
.check-item:last-child { border-bottom:none; }
.check-icon { font-size:1rem; width:1.4rem; text-align:center; }

/* ── Divider ── */
.styled-divider { border:none; border-top:1px solid #2a2d3e; margin:1.2rem 0; }

/* ── Page header ── */
.page-header {
    border-left:4px solid #6c63ff;
    padding-left:1rem;
    margin-bottom:1.8rem;
}
.page-header h1 { font-size:1.7rem; font-weight:800; color:#e8eaf6; margin:0; }
.page-header p  { font-size:.85rem; color:#8a8fa8; margin:.3rem 0 0; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="page-header">
  <h1>🔍 Validation des données</h1>
  <p>Responsable de la fiabilité des données extraites — validation JSON, date, total, doublons.</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Responsibilities checklist
# ---------------------------------------------------------------------------
with st.expander("📋 Responsabilités de cette page", expanded=False):
    st.markdown("""
<div class="section-card">
  <div class="check-item"><span class="check-icon">✅</span> Valider le JSON généré par Gemini</div>
  <div class="check-item"><span class="check-icon">✅</span> Vérifier le format de la date (AAAA-MM-JJ)</div>
  <div class="check-item"><span class="check-icon">✅</span> Vérifier que le total est numérique</div>
  <div class="check-item"><span class="check-icon">✅</span> Gérer les champs manquants</div>
  <div class="check-item"><span class="check-icon">✅</span> Détecter les factures en double</div>
  <div class="check-item"><span class="check-icon">🧪</span> Tests écrits avec Pytest (<code>test_api_client.py</code>)</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "historique" not in st.session_state:
    st.session_state.historique = []

# ---------------------------------------------------------------------------
# Layout: input | status
# ---------------------------------------------------------------------------
col_input, col_status = st.columns([3, 2], gap="large")

with col_input:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### 📥 JSON Gemini")
    st.caption("Colle ici le résultat brut de `extraire_facture()` pour le valider.")

    json_brut = st.text_area(
        label="JSON",
        label_visibility="collapsed",
        height=155,
        placeholder='{\n  "fournisseur": "ACME Sarl",\n  "date": "2024-03-15",\n  "total": 150.0,\n  "devise": "TND"\n}',
        key="json_input",
    )

    btn_col1, btn_col2 = st.columns(2)
    valider_btn = btn_col1.button("✅ Valider", use_container_width=True, type="primary")
    reset_btn   = btn_col2.button("🔄 Réinitialiser doublons", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col_status:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### 📊 Statut de la session")
    total_factures = len(st.session_state.historique)
    total_montant  = sum(f.get("total", 0) for f in st.session_state.historique)

    st.markdown(f"""
<div class="metric-row">
  <div class="metric-card">
    <div class="metric-label">Factures validées</div>
    <div class="metric-value">{total_factures}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Total cumulé</div>
    <div class="metric-value">{total_montant:.2f}</div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("<hr class='styled-divider'>", unsafe_allow_html=True)
    st.markdown("**Règles de validation actives**")
    rules = [
        ("🗓️", "Date au format AAAA-MM-JJ"),
        ("🔢", "Total ≥ 0 et numérique"),
        ("📋", "4 champs requis présents"),
        ("🚫", "Détection des doublons"),
    ]
    for icon, rule in rules:
        st.markdown(f"`{icon}` {rule}")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Reset doublons
# ---------------------------------------------------------------------------
if reset_btn:
    validation.reinitialiser_doublons()
    st.toast("Historique des doublons effacé.", icon="🔄")

# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------
if valider_btn:
    if not json_brut.strip():
        st.warning("⚠️ Colle un JSON avant de valider.")
        st.stop()

    # Parse JSON
    try:
        data_brute = json.loads(json_brut)
    except json.JSONDecodeError as exc:
        st.markdown(f"""
<div class="section-card">
  <span class="badge badge-error">❌ JSON invalide</span>
  <p style="margin-top:.7rem;color:#e8eaf6;">{exc}</p>
</div>""", unsafe_allow_html=True)
        st.stop()

    # Champs manquants (avertissement non-bloquant)
    manquants = validation.champs_manquants(data_brute)
    if manquants:
        st.markdown(f"""
<div class="section-card">
  <span class="badge badge-warning">⚠️ Champs manquants</span>
  <p style="margin-top:.7rem;color:#e8eaf6;">
    Les champs suivants sont <code>null</code> ou absents :
    <strong>{', '.join(manquants)}</strong>
  </p>
</div>""", unsafe_allow_html=True)

    # Validate
    try:
        data_valide = validation.valider_json(data_brute)
    except ErreurValidation as exc:
        st.markdown(f"""
<div class="section-card">
  <span class="badge badge-error">❌ Validation échouée</span>
  <p style="margin-top:.7rem;color:#e8eaf6;">{exc}</p>
</div>""", unsafe_allow_html=True)
        st.stop()

    # Doublon check
    doublon = validation.est_doublon(data_valide)
    if doublon:
        st.markdown("""
<div class="section-card">
  <span class="badge badge-warning">⚠️ Doublon détecté</span>
  <p style="margin-top:.7rem;color:#e8eaf6;">
    Cette facture a déjà été enregistrée dans cette session.
  </p>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
<div class="section-card">
  <span class="badge badge-success">✅ Facture valide</span>
  <p style="margin-top:.7rem;color:#e8eaf6;">Toutes les vérifications sont passées avec succès.</p>
</div>""", unsafe_allow_html=True)
        st.session_state.historique.append(data_valide)

    # Validated data metrics
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("#### 🧾 Données validées")
    st.markdown(f"""
<div class="metric-row">
  <div class="metric-card">
    <div class="metric-label">Fournisseur</div>
    <div class="metric-value" style="font-size:1rem">{data_valide.get('fournisseur','—')}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Date</div>
    <div class="metric-value" style="font-size:1rem">{data_valide.get('date','—')}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Total</div>
    <div class="metric-value">{data_valide.get('total', 0):.2f}</div>
  </div>
  <div class="metric-card">
    <div class="metric-label">Devise</div>
    <div class="metric-value">{data_valide.get('devise','—')}</div>
  </div>
</div>
""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# History table + CSV export
# ---------------------------------------------------------------------------
st.markdown("<hr class='styled-divider'>", unsafe_allow_html=True)
st.markdown(f"#### 📋 Historique — {len(st.session_state.historique)} facture(s) validée(s)")

if st.session_state.historique:
    st.dataframe(
        st.session_state.historique,
        use_container_width=True,
        hide_index=True,
        column_config={
            "fournisseur": st.column_config.TextColumn("Fournisseur"),
            "date":        st.column_config.TextColumn("Date"),
            "total":       st.column_config.NumberColumn("Total", format="%.2f"),
            "devise":      st.column_config.TextColumn("Devise"),
        },
    )

    export_col, clear_col = st.columns([2, 1])

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["fournisseur", "date", "total", "devise"])
    writer.writeheader()
    writer.writerows(st.session_state.historique)

    export_col.download_button(
        label="⬇️ Exporter en CSV",
        data=buf.getvalue().encode("utf-8"),
        file_name="factures_validees.csv",
        mime="text/csv",
        use_container_width=True,
        type="primary",
    )

    if clear_col.button("🗑️ Vider l'historique", use_container_width=True):
        st.session_state.historique = []
        validation.reinitialiser_doublons()
        st.rerun()

else:
    st.markdown("""
<div class="section-card" style="text-align:center;color:#8a8fa8;padding:2rem;">
  Aucune facture validée pour l'instant.<br>
  <small>Colle un JSON ci-dessus pour commencer.</small>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Pytest section
# ---------------------------------------------------------------------------
st.markdown("<hr class='styled-divider'>", unsafe_allow_html=True)
st.markdown("#### 🧪 Tests Pytest")

run_tests_btn = st.button("▶️ Lancer les tests", type="primary", use_container_width=False)

if run_tests_btn:
    with st.spinner("Exécution des tests en cours..."):
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "test_api_client.py", "-v", "--tb=short", "--no-header"],
            capture_output=True,
            text=True,
        )

    output_lines = (result.stdout + result.stderr).splitlines()

    passed = sum(1 for l in output_lines if "PASSED" in l)
    failed = sum(1 for l in output_lines if "FAILED" in l)
    errors = sum(1 for l in output_lines if "ERROR" in l)
    total  = passed + failed + errors

    # Summary badges
    badge_color = "badge-success" if failed == 0 and errors == 0 else "badge-error"
    status_text = "Tous les tests passent ✅" if failed == 0 and errors == 0 else f"{failed + errors} test(s) échoué(s) ❌"

    st.markdown(f"""
<div class="section-card">
  <span class="badge {badge_color}">{status_text}</span>
  <div class="metric-row" style="margin-top:.9rem">
    <div class="metric-card">
      <div class="metric-label">Total</div>
      <div class="metric-value">{total}</div>
    </div>
    <div class="metric-card">
      <div class="metric-label" style="color:#2ecc71">Passed</div>
      <div class="metric-value" style="color:#2ecc71">{passed}</div>
    </div>
    <div class="metric-card">
      <div class="metric-label" style="color:#e74c3c">Failed</div>
      <div class="metric-value" style="color:#e74c3c">{failed + errors}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # Detailed results per test
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("**Détail des tests**")
    for line in output_lines:
        if "PASSED" in line:
            name = line.split("PASSED")[0].strip()
            st.markdown(f'<div class="check-item"><span class="check-icon">✅</span><code>{name}</code></div>', unsafe_allow_html=True)
        elif "FAILED" in line:
            name = line.split("FAILED")[0].strip()
            st.markdown(f'<div class="check-item"><span class="check-icon">❌</span><code>{name}</code></div>', unsafe_allow_html=True)
        elif "ERROR" in line and "::" in line:
            name = line.strip()
            st.markdown(f'<div class="check-item"><span class="check-icon">⚠️</span><code>{name}</code></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Full log (collapsible)
    with st.expander("📄 Log complet"):
        st.code(result.stdout + result.stderr, language="bash")
