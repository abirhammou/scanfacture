import streamlit as st
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="ScanFacture",
    page_icon="📄",
    layout="wide"
)


# ============================================================
# DONNÉES
# ============================================================

# Stockage temporaire des factures pendant la session
if "factures" not in st.session_state:
    st.session_state.factures = []


# ============================================================
# TITRE
# ============================================================

st.title("📄 ScanFacture")
st.write(
    "Analysez automatiquement vos factures grâce à l'intelligence artificielle."
)


# ============================================================
# MENU
# ============================================================

menu = st.sidebar.radio(
    "Menu",
    [
        "📤 Importer une facture",
        "📋 Mes factures",
        "📊 Statistiques"
    ]
)


# ============================================================
# 1. IMPORTER UNE FACTURE
# ============================================================

if menu == "📤 Importer une facture":

    st.header("📤 Importer une facture")

    fichier = st.file_uploader(
        "Choisissez votre facture",
        type=["pdf", "png", "jpg", "jpeg"]
    )

    if fichier is not None:

        st.success(
            f"Fichier sélectionné : {fichier.name}"
        )

        st.write(
            f"Taille : {fichier.size / 1024:.2f} Ko"
        )

        if st.button(
            "🔍 Analyser la facture",
            type="primary"
        ):

            with st.spinner("Analyse de la facture..."):

                # Exemple temporaire de résultat
                resultat = {
                    "numero_facture": "FAC-001",
                    "date": "2026-09-15",
                    "fournisseur": "ABC SARL",
                    "total_ht": 1000.0,
                    "tva": 190.0,
                    "total_ttc": 1190.0
                }

                # Ajouter le nom du fichier
                resultat["fichier"] = fichier.name

                # Ajouter la facture à la liste
                st.session_state.factures.append(resultat)

            st.success("✅ Facture analysée avec succès !")

            # ------------------------------------------------
            # AFFICHAGE DU RÉSULTAT
            # ------------------------------------------------

            st.subheader("📄 Informations extraites")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "N° Facture",
                    resultat["numero_facture"]
                )

            with col2:
                st.metric(
                    "Fournisseur",
                    resultat["fournisseur"]
                )

            with col3:
                st.metric(
                    "Date",
                    resultat["date"]
                )

            st.subheader("💰 Montants")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Total HT",
                    f"{resultat['total_ht']:.2f} DT"
                )

            with col2:
                st.metric(
                    "TVA",
                    f"{resultat['tva']:.2f} DT"
                )

            with col3:
                st.metric(
                    "Total TTC",
                    f"{resultat['total_ttc']:.2f} DT"
                )


# ============================================================
# 2. AFFICHER LES FACTURES
# ============================================================

elif menu == "📋 Mes factures":

    st.header("📋 Mes factures")

    factures = st.session_state.factures

    if len(factures) == 0:

        st.info(
            "Aucune facture n'a encore été analysée."
        )

    else:

        df = pd.DataFrame(factures)

        colonnes = [
            "numero_facture",
            "date",
            "fournisseur",
            "total_ht",
            "tva",
            "total_ttc"
        ]

        df = df[colonnes]

        df = df.rename(
            columns={
                "numero_facture": "N° Facture",
                "date": "Date",
                "fournisseur": "Fournisseur",
                "total_ht": "Total HT",
                "tva": "TVA",
                "total_ttc": "Total TTC"
            }
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        # ------------------------------------------------
        # EXPORT CSV
        # ------------------------------------------------

        st.subheader("📥 Export")

        csv = df.to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            "⬇️ Télécharger les factures en CSV",
            data=csv,
            file_name="factures.csv",
            mime="text/csv"
        )


# ============================================================
# 3. STATISTIQUES
# ============================================================

elif menu == "📊 Statistiques":

    st.header("📊 Statistiques")

    factures = st.session_state.factures

    if len(factures) == 0:

        st.info(
            "Ajoutez des factures pour voir les statistiques."
        )

    else:

        df = pd.DataFrame(factures)

        # Conversion des dates
        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

        # Conversion des montants
        df["total_ht"] = pd.to_numeric(
            df["total_ht"],
            errors="coerce"
        ).fillna(0)

        df["tva"] = pd.to_numeric(
            df["tva"],
            errors="coerce"
        ).fillna(0)

        df["total_ttc"] = pd.to_numeric(
            df["total_ttc"],
            errors="coerce"
        ).fillna(0)

        # ====================================================
        # STATISTIQUES GÉNÉRALES
        # ====================================================

        st.subheader("📌 Vue générale")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Nombre de factures",
                len(df)
            )

        with col2:
            st.metric(
                "Total HT",
                f"{df['total_ht'].sum():.2f} DT"
            )

        with col3:
            st.metric(
                "Total TVA",
                f"{df['tva'].sum():.2f} DT"
            )

        with col4:
            st.metric(
                "Total TTC",
                f"{df['total_ttc'].sum():.2f} DT"
            )

        # ====================================================
        # STATISTIQUES MENSUELLES
        # ====================================================

        st.subheader("📅 Statistiques mensuelles")

        df["mois"] = df["date"].dt.to_period("M").astype(str)

        statistiques_mois = (
            df.groupby("mois")
            .agg(
                nombre_factures=("numero_facture", "count"),
                total_ht=("total_ht", "sum"),
                total_ttc=("total_ttc", "sum")
            )
            .reset_index()
        )

        st.dataframe(
            statistiques_mois,
            use_container_width=True,
            hide_index=True
        )

        st.write("### 💰 Total TTC par mois")

        graphique_mois = statistiques_mois.set_index(
            "mois"
        )["total_ttc"]

        st.bar_chart(graphique_mois)

        # ====================================================
        # STATISTIQUES PAR FOURNISSEUR
        # ====================================================

        st.subheader("🏢 Statistiques par fournisseur")

        statistiques_fournisseurs = (
            df.groupby("fournisseur")
            .agg(
                nombre_factures=("numero_facture", "count"),
                total_ht=("total_ht", "sum"),
                total_ttc=("total_ttc", "sum")
            )
            .reset_index()
        )

        st.dataframe(
            statistiques_fournisseurs,
            use_container_width=True,
            hide_index=True
        )

        st.write("### 🏢 Total TTC par fournisseur")

        graphique_fournisseurs = (
            statistiques_fournisseurs
            .set_index("fournisseur")["total_ttc"]
        )

        st.bar_chart(graphique_fournisseurs)