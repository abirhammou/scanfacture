"""Page 1 — Importer et analyser une facture (OCR + Gemini)."""

import sys
import os

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import api_client
import auth
from style import inject

st.set_page_config(page_title="Importer — ScanFacture", page_icon="📤", layout="wide")
inject()
auth.require_login()
auth.sidebar_user_widget()

if not auth.is_admin():
    st.warning("⛔ Accès réservé aux administrateurs.")
    st.stop()

st.header("📤 Importer une facture")

if "factures" not in st.session_state:
    st.session_state.factures = []

fichier = st.file_uploader(
    "Choisissez votre facture (jpg, png, pdf)",
    type=["jpg", "jpeg", "png", "pdf"],
)

if fichier is not None:
    st.success(f"Fichier sélectionné : **{fichier.name}** — {fichier.size / 1024:.2f} Ko")

    col_opts, _ = st.columns([1, 3])
    with col_opts:
        langue = st.selectbox("Langue du document", ["fre", "eng", "ara"], index=0)

    if st.button("🔍 Analyser la facture", type="primary"):
        with st.spinner("Extraction OCR en cours..."):
            try:
                texte = api_client.ocr(fichier.getvalue(), fichier.name, langue)
            except api_client.ApiError as exc:
                st.error(f"OCR échoué : {exc}")
                st.stop()

        st.text_area("📝 Texte reconnu par l'OCR", texte, height=150)

        with st.spinner("Gemini analyse la facture..."):
            try:
                facture = api_client.extraire_facture(texte)
            except (api_client.ApiError, ValueError) as exc:
                st.error(f"Extraction échouée : {exc}")
                st.stop()

        facture["fichier"] = fichier.name
        st.session_state.factures.append(facture)

        st.success("✅ Facture analysée avec succès !")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Fournisseur", facture.get("fournisseur") or "—")
        col2.metric("Date", facture.get("date") or "—")
        col3.metric("Total", f"{facture.get('total', 0):.2f}")
        col4.metric("Devise", facture.get("devise") or "—")

        st.json(facture)
