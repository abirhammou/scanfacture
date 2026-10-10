"""Page 4 — Test direct Gemini (sans OCR)."""

import sys
import os

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from api_client import ApiError, extraire_facture
import auth
from style import inject

st.set_page_config(page_title="Test Gemini — ScanFacture", page_icon="🧠", layout="wide")
inject()
auth.require_login()
auth.sidebar_user_widget()

if not auth.is_admin():
    st.warning("⛔ Accès réservé aux administrateurs.")
    st.stop()

st.header("🧠 Test Gemini")
st.caption("Colle directement un texte de facture pour tester l'extraction Gemini sans passer par l'OCR.")

EXEMPLE = """STE ALPHA SARL
Facture du 12/09/2026
Total TTC : 245,500 TND"""

if "historique_gemini" not in st.session_state:
    st.session_state.historique_gemini = []

texte = st.text_area("Texte de la facture", value=EXEMPLE, height=200)

if st.button("Analyser avec Gemini", type="primary"):
    if not texte.strip():
        st.warning("Colle d'abord un texte de facture.")
    else:
        with st.spinner("Gemini analyse la facture..."):
            try:
                facture = extraire_facture(texte)
            except ApiError as exc:
                st.error(f"Erreur : {exc}")
            else:
                st.success("✅ JSON extrait et validé")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Fournisseur", facture.get("fournisseur") or "—")
                col2.metric("Date", facture.get("date") or "—")
                col3.metric("Total", f"{facture.get('total', 0):.2f}")
                col4.metric("Devise", facture.get("devise") or "—")
                st.json(facture)
                st.session_state.historique_gemini.append(facture)

if st.session_state.historique_gemini:
    st.divider()
    st.subheader("Factures de la session")
    df = pd.DataFrame(st.session_state.historique_gemini)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Télécharger en CSV",
        df.to_csv(index=False).encode("utf-8"),
        file_name="factures_gemini.csv",
        mime="text/csv",
    )
