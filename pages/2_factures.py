"""Page 2 — Liste des factures et statistiques."""

import sys
import os

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import auth
from style import inject

st.set_page_config(page_title="Factures — ScanFacture", page_icon="📋", layout="wide")
inject()
auth.require_login()
auth.sidebar_user_widget()

st.header("📋 Mes factures")

if "factures" not in st.session_state:
    st.session_state.factures = []

factures = st.session_state.factures
menu = st.radio("Vue", ["📋 Liste", "📊 Statistiques"], horizontal=True)

if menu == "📋 Liste":
    if not factures:
        st.info("Aucune facture analysée. Commencez par la page « Importer ».")
    else:
        df = pd.DataFrame(factures)
        cols = [c for c in ["fichier", "fournisseur", "date", "total", "devise"] if c in df.columns]
        st.dataframe(df[cols], use_container_width=True, hide_index=True)
        csv = df[cols].to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ Exporter en CSV", data=csv, file_name="factures.csv", mime="text/csv")
        if auth.is_admin() and st.button("🗑️ Vider la liste"):
            st.session_state.factures = []
            st.rerun()

elif menu == "📊 Statistiques":
    if not factures:
        st.info("Ajoutez des factures pour voir les statistiques.")
    else:
        df = pd.DataFrame(factures)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["total"] = pd.to_numeric(df["total"], errors="coerce").fillna(0)

        col1, col2, col3 = st.columns(3)
        col1.metric("Nombre de factures", len(df))
        col2.metric("Total cumulé", f"{df['total'].sum():.2f}")
        col3.metric("Moyenne par facture", f"{df['total'].mean():.2f}")

        st.subheader("📅 Total par mois")
        df["mois"] = df["date"].dt.to_period("M").astype(str)
        st.bar_chart(df.groupby("mois")["total"].sum())

        st.subheader("🏢 Total par fournisseur")
        st.bar_chart(df.groupby("fournisseur")["total"].sum())
