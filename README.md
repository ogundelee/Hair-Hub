# Hair Hub

A Streamlit-powered hair services marketplace for Fisk University students — connecting student stylists with clients on campus.

## What It Does

**For clients:** Browse stylist profiles, view services and pricing, and book appointments directly through the app. Track booking status (Pending → Confirmed → Completed) from a personal dashboard.

**For stylists:** Build a public profile with a bio, service menu, portfolio photos, and available appointment slots. Manage incoming bookings and update their status from an Appointments dashboard.

## Stack

- **Frontend/Backend:** Python + Streamlit
- **Auth:** Firebase Authentication (email/password, restricted to `@my.fisk.edu` addresses)
- **Database:** Firestore (via `firebase-admin`)
- **Image hosting:** Cloudinary

## Running Locally

```bash
pip install -r requirements.txt
streamlit run main.py
```

> Requires a `.streamlit/secrets.toml` file with Firebase and Cloudinary credentials (not committed — see `.streamlit/secrets.toml.example` if available).

## Deployment

Deployed on Streamlit Cloud from the `main` branch.
Live app: https://hair-recs.streamlit.app
