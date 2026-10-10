"""Page 3 — Validation manuelle des données JSON extraites par Gemini."""

import csv
import io
import json
import subprocess
import sys
import os

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import validation
from validation import ErreurValidation
import auth
from style import inject

st.set_page_config(page_title="Validation — ScanFacture", page_icon="✅", layout="wide")
inject()
auth.require_login()
auth.sidebar_user_widget()

if not auth.is_admin():
    st.warning("⛔ Accès réservé aux administrateurs.")
    st.stop()

st.header("🔍 Validation des données")
st.caption("Valide manuellement un JSON issu de Gemini : format, doublons, champs requis.")

if "historique" not in st.session_state:
    st.session_state.historique = []

col_input, col_status = st.columns([3, 2], gap="large")

with col_input:
    st.subheader("📥 JSON Gemini")
    json_brut = st.text_area(
        "Colle ici le résultat de `extraire_facture()`",
        height=160,
        placeholder='{\n  "fournisseur": "ACME Sarl",\n  "date": "2024-03-15",\n  "total": 150.0,\n  "devise": "TND"\n}',
    )
    btn1, btn2 = st.columns(2)
    valider_btn = btn1.button("✅ Valider", type="primary", use_container_width=True)
    reset_btn = btn2.button("🔄 Réinitialiser doublons", use_container_width=True)

with col_status:
    st.subheader("📊 Session")
    c1, c2 = st.columns(2)
    c1.metric("Factures validées", len(st.session_state.historique))
    c2.metric("Total cumulé", f"{sum(f.get('total',0) for f in st.session_state.historique):.2f}")
    st.caption("Règles : date AAAA-MM-JJ · total ≥ 0 · 4 champs requis · anti-doublon")

if reset_btn:
    validation.reinitialiser_doublons()
    st.toast("Historique des doublons effacé.", icon="🔄")

if valider_btn:
    if not json_brut.strip():
        st.warning("Colle un JSON avant de valider.")
        st.stop()
    try:
        data_brute = json.loads(json_brut)
    except json.JSONDecodeError as exc:
        st.error(f"JSON invalide : {exc}")
        st.stop()

    manquants = validation.champs_manquants(data_brute)
    if manquants:
        st.warning(f"Champs null ou absents : {', '.join(manquants)}")

    try:
        data_valide = validation.valider_json(data_brute)
    except ErreurValidation as exc:
        st.error(f"Validation échouée : {exc}")
        st.stop()

    if validation.est_doublon(data_valide):
        st.warning("⚠️ Doublon détecté — cette facture existe déjà dans la session.")
    else:
        st.success("✅ Facture valide et enregistrée.")
        st.session_state.historique.append(data_valide)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Fournisseur", data_valide.get("fournisseur") or "—")
    col2.metric("Date", data_valide.get("date") or "—")
    col3.metric("Total", f"{data_valide.get('total', 0):.2f}")
    col4.metric("Devise", data_valide.get("devise") or "—")

st.divider()
st.subheader(f"📋 Historique — {len(st.session_state.historique)} facture(s)")

if st.session_state.historique:
    st.dataframe(st.session_state.historique, use_container_width=True, hide_index=True)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["fournisseur", "date", "total", "devise"])
    writer.writeheader()
    writer.writerows(st.session_state.historique)
    exp_col, clear_col = st.columns([2, 1])
    exp_col.download_button("⬇️ Exporter en CSV", data=buf.getvalue().encode("utf-8"),
        file_name="factures_validees.csv", mime="text/csv", use_container_width=True, type="primary")
    if clear_col.button("🗑️ Vider l'historique", use_container_width=True):
        st.session_state.historique = []
        validation.reinitialiser_doublons()
        st.rerun()
else:
    st.info("Aucune facture validée pour l'instant.")

st.divider()
st.subheader("🧪 Tests Pytest")
if st.button("▶️ Lancer les tests", type="primary"):
    test_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_api_client.py")
    with st.spinner("Exécution des tests..."):
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short", "--no-header"],
            capture_output=True, text=True,
        )
    lines = (result.stdout + result.stderr).splitlines()
    passed = sum(1 for l in lines if "PASSED" in l)
    failed = sum(1 for l in lines if "FAILED" in l or "ERROR" in l)
    c1, c2, c3 = st.columns(3)
    c1.metric("Total", passed + failed)
    c2.metric("✅ Passés", passed)
    c3.metric("❌ Échoués", failed)
    with st.expander("📄 Log complet"):
        st.code(result.stdout + result.stderr, language="bash")
