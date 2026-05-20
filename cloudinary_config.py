"""
cloudinary_config.py — Cloudinary image upload helper for Hair Hub.

Credentials are read from Streamlit secrets (Streamlit Cloud) or from
environment variables / a local .env file (local dev).

Required secrets:
    cloudinary_cloud_name  — e.g. "my-cloud"
    cloudinary_api_key     — numeric string from Cloudinary dashboard
    cloudinary_api_secret  — secret string from Cloudinary dashboard
"""

import streamlit as st
import cloudinary
import cloudinary.uploader

_configured = False


def _configure():
    global _configured
    if _configured:
        return
    try:
        cloud_name = st.secrets["cloudinary_cloud_name"]
        api_key    = st.secrets["cloudinary_api_key"]
        api_secret = st.secrets["cloudinary_api_secret"]
    except KeyError as e:
        st.error(
            f"Cloudinary secret missing: {e}. "
            "Add `cloudinary_cloud_name`, `cloudinary_api_key`, and "
            "`cloudinary_api_secret` to `.streamlit/secrets.toml`."
        )
        st.stop()

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True,
    )
    _configured = True


def upload_image(file_bytes: bytes, folder: str, public_id: str) -> str:
    """
    Upload raw image bytes to Cloudinary and return the secure URL.

    Args:
        file_bytes: Raw file content (call file.getvalue() or file.read()).
        folder:     Cloudinary folder, e.g. "stylists/uid123" or "bookings".
        public_id:  Filename without extension, e.g. "profile" or "cover".
                    Use a unique value (timestamp + name) for portfolio images.

    Returns:
        A permanent https://res.cloudinary.com/... URL.
    """
    _configure()
    result = cloudinary.uploader.upload(
        file_bytes,
        folder=folder,
        public_id=public_id,
        overwrite=True,
        resource_type="image",
    )
    return result["secure_url"]
