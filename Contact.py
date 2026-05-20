import streamlit as st
from datetime import datetime, timezone

from firebase_config import get_db


def app():
    st.title("Contact Us")

    st.write(
        "Have questions or feedback? We'd love to hear from you! "
        "Please fill out the form below:"
    )

    name    = st.text_input("Your Name",  key="contact_name")
    email   = st.text_input("Your Email", key="contact_email")
    message = st.text_area("Message", height=150, key="contact_message")

    if st.button("Submit", type="primary"):
        if not name:
            st.error("Please enter your name.")
        elif not email:
            st.error("Please enter your email.")
        elif not message:
            st.error("Please enter a message.")
        else:
            _save_message(name=name, email=email, message=message)


def _save_message(name: str, email: str, message: str):
    try:
        db = get_db()
        db.collection("contact_messages").document().set({
            "name":      name,
            "email":     email,
            "message":   message,
            "createdAt": datetime.now(timezone.utc),
        })
        st.success("Message submitted successfully! We'll get back to you soon.")
        # Clear fields
        for key in ("contact_name", "contact_email", "contact_message"):
            st.session_state.pop(key, None)
        st.rerun()
    except Exception as e:
        st.error(f"Failed to send message: {e}")
