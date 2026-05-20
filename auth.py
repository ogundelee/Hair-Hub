"""
auth.py — Authentication, Fisk email validation, and role selection for Hair Hub.

Flow:
  1. render_auth_gate()     → Login / Sign-Up tabs
  2. render_role_selection() → Stylist vs Client picker (new users only)
  3. _finalize_role()       → saves users/{uid} doc and promotes the session
"""

import streamlit as st
import requests
from datetime import datetime, timezone

from firebase_config import get_db

FISK_DOMAIN = "@my.fisk.edu"

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def is_fisk_email(email: str) -> bool:
    return email.strip().lower().endswith(FISK_DOMAIN)


def _api_key() -> str:
    try:
        return st.secrets["firebase_api_key"]
    except KeyError:
        st.error(
            "Firebase API key missing. "
            "Add `firebase_api_key = '...'` to `.streamlit/secrets.toml`."
        )
        st.stop()


def _auth_post(endpoint: str, email: str, password: str) -> dict:
    """POST to a Firebase Auth REST endpoint and return the parsed response."""
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:{endpoint}?key={_api_key()}"
    resp = requests.post(
        url,
        json={"email": email, "password": password, "returnSecureToken": True},
        timeout=10,
    )
    data = resp.json()
    if "error" in data:
        raise ValueError(data["error"]["message"])
    return data  # keys: idToken, localId (uid), email, refreshToken


def sign_in(email: str, password: str) -> dict:
    return _auth_post("signInWithPassword", email, password)


def sign_up(email: str, password: str) -> dict:
    return _auth_post("signUp", email, password)


# ─────────────────────────────────────────────────────────────────────────────
# Firestore user document
# ─────────────────────────────────────────────────────────────────────────────

def get_user_doc(uid: str) -> dict | None:
    """Return the users/{uid} document as a dict, or None if it doesn't exist."""
    doc = get_db().collection("users").document(uid).get()
    return doc.to_dict() if doc.exists else None


def save_user_doc(uid: str, email: str, display_name: str, role: str) -> None:
    get_db().collection("users").document(uid).set({
        "uid": uid,
        "displayName": display_name,
        "email": email,
        "role": role,
        "createdAt": datetime.now(timezone.utc),
    })


# ─────────────────────────────────────────────────────────────────────────────
# Session helpers
# ─────────────────────────────────────────────────────────────────────────────

def _set_session(uid: str, email: str, display_name: str, role: str, id_token: str) -> None:
    st.session_state.update({
        "user_uid": uid,
        "user_email": email,
        "user_display_name": display_name,
        "user_role": role,
        "id_token": id_token,
    })


def logout() -> None:
    for key in ("user_uid", "user_email", "user_display_name", "user_role", "id_token"):
        st.session_state.pop(key, None)
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# UI — Auth gate (login / sign-up)
# ─────────────────────────────────────────────────────────────────────────────

def render_auth_gate() -> None:
    """
    Renders Login / Sign-Up toggle.
    Uses st.radio instead of st.tabs so every switch triggers a Python rerun,
    which clears stale error messages before rendering the new mode.
    """
    mode = st.radio(
        "mode",
        ["Login", "Sign Up"],
        horizontal=True,
        label_visibility="collapsed",
    )
    st.divider()
    if mode == "Login":
        _render_login()
    else:
        _render_signup()


def _render_login() -> None:
    if "login_error" in st.session_state:
        st.error(st.session_state.pop("login_error"))
    if "login_info" in st.session_state:
        st.info(st.session_state.pop("login_info"))

    # Email is outside the form so it validates immediately on blur
    email = st.text_input("Fisk Email", placeholder="you@my.fisk.edu", key="login_email")
    if email and not is_fisk_email(email):
        st.error(f"Only {FISK_DOMAIN} email addresses are allowed.")

    with st.form("login_form", clear_on_submit=True, border=False):
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True)

    if not submitted:
        return
    if not email or not password:
        st.session_state["login_error"] = "Please enter your email and password."
        st.rerun()
        return
    if not is_fisk_email(email):
        st.session_state["login_error"] = f"Only {FISK_DOMAIN} email addresses are allowed."
        st.rerun()
        return

    try:
        user_data = sign_in(email.strip().lower(), password)
        uid = user_data["localId"]
        user_doc = get_user_doc(uid)

        if user_doc:
            # Returning user — restore full session
            _set_session(
                uid,
                user_doc["email"],
                user_doc.get("displayName", ""),
                user_doc["role"],
                user_data["idToken"],
            )
        else:
            # Auth account exists but Firestore doc is missing (incomplete sign-up)
            if not is_fisk_email(email):
                st.session_state["login_error"] = "Only @my.fisk.edu addresses may access Hair Hub."
                st.rerun()
                return
            st.session_state.update({
                "pending_uid": uid,
                "pending_email": email.strip().lower(),
                "pending_display_name": email.split("@")[0],
                "id_token": user_data["idToken"],
            })

        st.rerun()

    except ValueError as exc:
        msg = str(exc)
        st.session_state["login_error"] = _ERROR_MAP.get(msg, f"Authentication error: {msg}")
        if msg in ("INVALID_LOGIN_CREDENTIALS", "EMAIL_NOT_FOUND", "INVALID_PASSWORD"):
            st.session_state["login_info"] = "New to Hair Hub? Switch to the **Sign Up** tab to create an account."
        st.rerun()


def _render_signup() -> None:
    if "signup_error" in st.session_state:
        st.error(st.session_state.pop("signup_error"))

    # Email is outside the form so it validates immediately on blur
    email = st.text_input("Fisk Email", placeholder="you@my.fisk.edu", key="signup_email")
    if email and not is_fisk_email(email):
        st.error(
            f"Only Fisk University email addresses ({FISK_DOMAIN}) are allowed. "
            "Please use your Fisk student or staff email."
        )

    with st.form("signup_form", clear_on_submit=True, border=False):
        display_name = st.text_input("Full Name")
        password = st.text_input("Password (min 6 characters)", type="password")
        confirm = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Create Account", use_container_width=True)

    if not submitted:
        return

    if not all([display_name, email, password, confirm]):
        st.session_state["signup_error"] = "Please fill in all fields."
        st.rerun()
        return
    if not is_fisk_email(email):
        st.session_state["signup_error"] = (
            f"Only Fisk University email addresses ({FISK_DOMAIN}) are allowed."
        )
        st.rerun()
        return
    if password != confirm:
        st.session_state["signup_error"] = "Passwords do not match."
        st.rerun()
        return
    if len(password) < 6:
        st.session_state["signup_error"] = "Password must be at least 6 characters."
        st.rerun()
        return

    try:
        user_data = sign_up(email.strip().lower(), password)
        st.session_state.update({
            "pending_uid": user_data["localId"],
            "pending_email": email.strip().lower(),
            "pending_display_name": display_name.strip(),
            "id_token": user_data["idToken"],
        })
        st.rerun()
    except ValueError as exc:
        st.session_state["signup_error"] = _ERROR_MAP.get(str(exc), f"Error: {exc}")
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# UI — Role selection (new users)
# ─────────────────────────────────────────────────────────────────────────────

def render_role_selection() -> None:
    """
    Role picker shown once to new users after sign-up or first login.
    Saves the users/{uid} document and promotes pending_* to a full session.
    """
    display_name = st.session_state.get("pending_display_name", "")

    st.title("Welcome to Hair Hub!")
    st.write(f"Almost there, **{display_name}** — choose how you'll use the app:")
    st.divider()

    col_stylist, col_client = st.columns(2)

    with col_stylist:
        with st.container(border=True):
            st.markdown("### ✂️ Stylist")
            st.write(
                "Create a portfolio, list your services, "
                "and accept bookings from Fisk students."
            )
            if st.button("I'm a Stylist", use_container_width=True, key="pick_stylist"):
                _finalize_role("stylist")

    with col_client:
        with st.container(border=True):
            st.markdown("### 💇 Client")
            st.write(
                "Browse stylists on campus, book appointments, "
                "and manage your schedule."
            )
            if st.button("I'm a Client", use_container_width=True, key="pick_client"):
                _finalize_role("client")


def _finalize_role(role: str) -> None:
    """Save the user doc and promote pending session to a full authenticated session."""
    uid = st.session_state["pending_uid"]
    email = st.session_state["pending_email"]
    display_name = st.session_state.get("pending_display_name", email.split("@")[0])

    save_user_doc(uid, email, display_name, role)
    _set_session(uid, email, display_name, role, st.session_state.get("id_token", ""))

    for key in ("pending_uid", "pending_email", "pending_display_name"):
        st.session_state.pop(key, None)

    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Error display
# ─────────────────────────────────────────────────────────────────────────────

_ERROR_MAP = {
    "EMAIL_NOT_FOUND": "No account found with that email.",
    "INVALID_PASSWORD": "Incorrect password.",
    "INVALID_LOGIN_CREDENTIALS": "Incorrect email or password.",
    "USER_DISABLED": "This account has been disabled. Contact support.",
    "EMAIL_EXISTS": "An account with this email already exists — try logging in.",
    "INVALID_EMAIL": "Please enter a valid email address.",
    "WEAK_PASSWORD : Password should be at least 6 characters": (
        "Password must be at least 6 characters."
    ),
    "TOO_MANY_ATTEMPTS_TRY_LATER": (
        "Too many failed attempts. Please wait a moment and try again."
    ),
}


def _show_error(message: str) -> None:
    st.error(_ERROR_MAP.get(message, f"Authentication error: {message}"))
