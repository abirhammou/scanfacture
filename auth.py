"""Gestion des utilisateurs et authentification — ScanFacture."""

import hashlib
import streamlit as st

# ── Utilisateurs ──────────────────────────────────────────────────────────────
# rôles : "admin" (CRUD factures) | "user" (lecture seule)

def _h(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()

USERS = {
    "sami": {
        "password": _h("sami123"),
        "role": "admin",
        "display": "Sami",
    },
    "mokhtar": {
        "password": _h("mokhtar123"),
        "role": "admin",
        "display": "Mokhtar",
    },
    "douaa": {
        "password": _h("douaa123"),
        "role": "user",
        "display": "Douaa",
    },
    "abir": {
        "password": _h("abir123"),
        "role": "user",
        "display": "Abir",
    },
    "sawsen": {
        "password": _h("sawsen123"),
        "role": "user",
        "display": "Sawsen",
    },
}


def login(username: str, password: str) -> bool:
    """Tente une connexion. Retourne True si succès."""
    u = USERS.get(username.lower().strip())
    if u and u["password"] == _h(password):
        st.session_state["auth_user"] = username.lower().strip()
        st.session_state["auth_role"] = u["role"]
        st.session_state["auth_display"] = u["display"]
        return True
    return False


def logout():
    for k in ["auth_user", "auth_role", "auth_display"]:
        st.session_state.pop(k, None)


def is_logged_in() -> bool:
    return "auth_user" in st.session_state


def is_admin() -> bool:
    return st.session_state.get("auth_role") == "admin"


def current_user() -> str:
    return st.session_state.get("auth_display", "")


def require_login():
    """Affiche la page de connexion si non authentifié. Appeler en tête de chaque page."""
    if not is_logged_in():
        _render_login()
        st.stop()


def _render_login():
    st.markdown("""
<style>
.login-wrap {
    max-width: 380px;
    margin: 6rem auto 0;
    background: #111428;
    border: 1px solid #1e2438;
    border-radius: 16px;
    padding: 2.2rem 2rem 2rem;
    text-align: center;
}
.login-icon { font-size: 2.8rem; margin-bottom: .4rem; display:block; }
.login-title {
    font-size: 1.6rem; font-weight: 800;
    background: linear-gradient(135deg, #6c63ff, #a78bfa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: .2rem;
}
.login-sub { font-size: .85rem; color: #555d7c; margin-bottom: 1.4rem; }
</style>
<div class="login-wrap">
  <span class="login-icon">🔐</span>
  <div class="login-title">ScanFacture</div>
  <div class="login-sub">Connectez-vous pour continuer</div>
</div>
""", unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submitted = st.form_submit_button("Se connecter", type="primary", use_container_width=True)

    if submitted:
        if login(username, password):
            st.rerun()
        else:
            st.error("Nom d'utilisateur ou mot de passe incorrect.")


def sidebar_user_widget():
    """Affiche l'utilisateur connecté + bouton déconnexion dans la sidebar."""
    with st.sidebar:
        role_badge = "🔑 Admin" if is_admin() else "👤 Utilisateur"
        st.markdown(f"""
<div style="background:#0d1025;border:1px solid #1e2438;border-radius:10px;
     padding:.8rem 1rem;margin-bottom:1rem;text-align:center;">
  <div style="font-size:.75rem;color:#555d7c;margin-bottom:.2rem;">{role_badge}</div>
  <div style="font-weight:700;color:#a78bfa;font-size:.95rem;">{current_user()}</div>
</div>
""", unsafe_allow_html=True)
        if st.button("🚪 Déconnexion", use_container_width=True):
            logout()
            st.rerun()
