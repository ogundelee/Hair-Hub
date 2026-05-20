import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st

_db = None


# ─────────────────────────────────────────────────────────────────────────────
# Public client
# ─────────────────────────────────────────────────────────────────────────────

def get_db():
    """Return a shared Firestore client, initialising the app on first call."""
    global _db
    if _db is not None:
        return _db
    if not firebase_admin._apps:
        _init_app()
    _db = firestore.client()
    return _db


# ─────────────────────────────────────────────────────────────────────────────
# Internal initialisation
# ─────────────────────────────────────────────────────────────────────────────

def _init_app() -> None:
    """
    Initialise Firebase Admin SDK (Firestore only).

    Credential priority:
      1. Streamlit secrets → st.secrets["firebase_service_account"]  (Streamlit Cloud)
      2. Local file        → service-account.json in project root     (local dev)
    """
    try:
        cred_info = dict(st.secrets["firebase_service_account"])
        cred      = credentials.Certificate(cred_info)
    except (KeyError, Exception):
        try:
            import json
            with open("service-account.json") as f:
                cred_info = json.load(f)
            cred = credentials.Certificate(cred_info)
        except Exception:
            st.error(
                "Firebase credentials not found. "
                "Add `[firebase_service_account]` to `.streamlit/secrets.toml` "
                "or place `service-account.json` in the project root."
            )
            st.stop()

    firebase_admin.initialize_app(cred)
