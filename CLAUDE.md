# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
pip install -r requirements.txt
streamlit run main.py
```

## Architecture

Hair-Hub is a multi-page Streamlit application for a hair services marketplace at Fisk Campus. The entry point is `main.py`, which renders a horizontal nav menu (via `streamlit-option-menu`) and conditionally imports and calls the `app()` function from each page module:

- `About.py` — mission/vision content
- `Stylists.py` — stylist showcase with images from `Hairhub_Images/`
- `Book.py` — appointment booking form
- `Contact.py` — contact form

Each page module exports a single `app()` function. CSS is loaded from `hairhub.css` at runtime using `st.markdown` with `unsafe_allow_html=True`.

## Deployment

The app is deployed on Streamlit Cloud from the `main` branch. Image and CSS paths must be relative to the repo root (not the module file) since Streamlit Cloud runs `main.py` from the repo root.
