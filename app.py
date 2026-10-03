import streamlit as st

import api_client

st.title("ScanFacture")

fichier = st.file_uploader("Photo ou PDF de la facture", type=["jpg", "jpeg", "png", "pdf"])
if fichier and st.button("Analyser"):
    try:
        texte = api_client.ocr(fichier.getvalue(), fichier.name)
        st.text_area("Texte reconnu", texte, height=150)
        st.json(api_client.extraire_facture(texte))
    except (api_client.ApiError, ValueError) as exc:
        st.error(exc)
# TODO : validation du JSON, export CSV, total des dépenses par mois...
