"""Interface de test pour la partie Gemini de ScanFacture.

Lancer : python -m streamlit run app_gemini.py
"""

import pandas as pd
import streamlit as st

from api_client import ApiError, extraire_facture

st.set_page_config(page_title="ScanFacture - Test Gemini", page_icon="🧾")
st.title("🧾 ScanFacture - Test Gemini")
st.caption("Colle le texte d'une facture : Gemini extrait un JSON, puis il est validé.")

EXEMPLE = """STE ALPHA SARL
Facture du 12/09/2026
Total TTC : 245,500 TND"""

if "historique" not in st.session_state:
    st.session_state.historique = []

texte = st.text_area("Texte de la facture (sortie de l'OCR)", value=EXEMPLE, height=200)

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
                st.success("JSON extrait et validé")
                st.json(facture)

                col1, col2, col3 = st.columns(3)
                col1.metric("Fournisseur", facture.get("fournisseur") or "-")
                col2.metric("Date", facture.get("date") or "-")
                col3.metric("Total", f"{facture['total']} {facture.get('devise') or ''}")

                st.session_state.historique.append(facture)

if st.session_state.historique:
    st.subheader("Factures de la session")
    df = pd.DataFrame(st.session_state.historique)
st.dataframe(df, width="stretch")    st.download_button(
        "Télécharger en CSV",
        df.to_csv(index=False).encode("utf-8"),
        file_name="factures.csv",
        mime="text/csv",
    )
    