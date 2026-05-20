import base64
import streamlit as st
import streamlit.components.v1 as components
from streamlit_option_menu import option_menu
from datetime import datetime, timezone
import Book, Stylists
import auth
from firebase_config import get_db

st.set_page_config(page_title="Hair Hub", layout="wide")


# ─────────────────────────────────────────────────────────────────────────────
# Auth dialog
# ─────────────────────────────────────────────────────────────────────────────

@st.dialog("Sign in to Hair Hub")
def _auth_dialog():
    auth.render_auth_gate()


@st.dialog("Get Help")
def _get_help_dialog():
    st.write("Have a question or feedback? We'd love to hear from you.")
    name    = st.text_input("Your Name",  key="help_name")
    email   = st.text_input("Your Email", key="help_email")
    message = st.text_area("Message", height=120, key="help_message")
    if st.button("Send Message", type="primary", use_container_width=True, key="help_submit"):
        if not name:
            st.error("Please enter your name.")
        elif not email:
            st.error("Please enter your email.")
        elif not message:
            st.error("Please enter a message.")
        else:
            try:
                get_db().collection("contact_messages").document().set({
                    "name": name, "email": email, "message": message,
                    "createdAt": datetime.now(timezone.utc),
                })
                st.success("Message sent! We'll get back to you soon.")
                for k in ("help_name", "help_email", "help_message"):
                    st.session_state.pop(k, None)
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to send: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _img_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _render_sidebar_notifications():
    user_uid = st.session_state.get("user_uid", "")
    role     = st.session_state.get("user_role")
    if not user_uid:
        return
    try:
        db = get_db()
        if role == "client":
            docs = db.collection("bookings").where("clientUid", "==", user_uid).stream()
        else:
            docs = db.collection("bookings").where("stylistId", "==", user_uid).stream()
        bookings = [d.to_dict() for d in docs]
    except Exception:
        return

    notifications = []
    if role == "client":
        for b in bookings:
            status  = b.get("status", "pending")
            stylist = b.get("stylistName", "Your stylist")
            service = b.get("service", "")
            if status == "confirmed":
                notifications.append(f"✅ **{stylist}** confirmed your **{service}** appointment.")
            elif status == "completed":
                notifications.append(f"🎉 Your appointment with **{stylist}** is complete.")
            elif status == "cancelled":
                notifications.append(f"❌ Your **{service}** booking was cancelled.")
    else:
        for b in [b for b in bookings if b.get("status") == "pending"]:
            notifications.append(
                f"📅 **{b.get('clientName', 'A client')}** booked **{b.get('service', '')}**."
            )

    with st.sidebar:
        st.markdown("### Notifications")
        if notifications:
            for note in notifications[-5:]:
                st.info(note)
        else:
            st.caption("No new notifications.")
        st.divider()


def _render_landing():
    """Full-width unauthenticated marketing landing page."""

    # Footer links use query params to trigger dialogs (HTML can't call st functions directly)
    action = st.query_params.get("action")
    if action == "get_started":
        st.query_params.clear()
        _auth_dialog()
    elif action == "get_help":
        st.query_params.clear()
        _get_help_dialog()

    # ── Hero ─────────────────────────────────────────────────────────────────
    try:
        b64 = _img_b64("Hairhub_Images/Fisk University .jpg")
        bg  = (
            f"linear-gradient(rgba(0,0,0,0.60),rgba(0,0,0,0.60)),"
            f"url('data:image/jpeg;base64,{b64}')"
        )
    except Exception:
        bg = "linear-gradient(135deg,#1a1a2e,#2d3748)"

    # The CSS here uses #hero-marker as an anchor to target the Streamlit columns
    # row that immediately follows this markdown block, pulling it up into the
    # hero image frame with a negative margin.
    st.markdown(f"""
    <style>
    /* Scope strictly to stMain so the white styling never leaks into the dialog overlay */
    section[data-testid="stMain"] div:has(#hero-marker) + div {{
        margin-top: -80px !important;
        position: relative !important;
        z-index: 10 !important;
    }}
    section[data-testid="stMain"] div:has(#hero-marker) + div button {{
        background: transparent !important;
        border: 2px solid #ffffff !important;
        color: #ffffff !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        border-radius: 8px !important;
        padding: 14px 0 !important;
    }}
    section[data-testid="stMain"] div:has(#hero-marker) + div button:hover {{
        background: rgba(255,255,255,0.15) !important;
        border-color: #ffffff !important;
        color: #ffffff !important;
    }}
    /* Position dialog near the top so Sign Up form is fully visible without scrolling */
    div[data-testid="stDialog"] > div {{
        margin-top: 20px !important;
    }}
    </style>
    <div id="hero-marker" style="
        background: {bg};
        background-size: cover;
        background-position: center;
        border-radius: 20px;
        padding: 140px 24px 120px;
        text-align: center;
    ">
        <h1 style="color:#ffffff; font-size:72px; font-weight:900;
                   letter-spacing:-2px; margin:0 0 16px; line-height:1.1;">
            Hair Hub
        </h1>
        <p style="color:#e2e8f0; font-size:24px; font-style:italic;
                  margin:0 0 20px; font-weight:300; letter-spacing:0.5px;">
            Your Campus. Your Style. Your Way.
        </p>
        <p style="color:rgba(255,255,255,0.60); font-size:14px; margin:0; letter-spacing:0.5px;">
            Open to all Fisk students &mdash; clients &amp; stylists welcome
        </p>
    </div>
    """, unsafe_allow_html=True)

    # CTA button — real Streamlit widget so clicking opens the dialog directly
    # with no URL change or page-navigation flash. CSS above positions it inside
    # the hero frame via negative margin on this column row.
    _, col_cta, _ = st.columns([3, 2, 3])
    with col_cta:
        if st.button("Get Started  →", use_container_width=True, type="primary", key="hero_cta"):
            _auth_dialog()

    st.markdown("<div style='height:72px'></div>", unsafe_allow_html=True)

    # ── How It Works ─────────────────────────────────────────────────────────
    st.markdown(
        "<div id='how-it-works'></div>"
        "<h2 style='text-align:center; font-size:32px; font-weight:800; margin-bottom:8px;'>"
        "How It Works</h2>"
        "<p style='text-align:center; color:#6b7280; font-size:16px; margin-bottom:40px;'>"
        "Get connected with a campus stylist in three easy steps.</p>",
        unsafe_allow_html=True,
    )

    step1, step2, step3 = st.columns(3, gap="large")
    for col, icon, title, desc in [
        (step1, "✍️", "1. Sign Up",
         "Create your free Fisk account in seconds using your @my.fisk.edu email."),
        (step2, "👩‍🎨", "2. Browse Stylists",
         "Explore talented campus stylists, view their portfolios, and compare services."),
        (step3, "📅", "3. Book",
         "Pick a time that works for you and confirm your appointment instantly."),
    ]:
        with col:
            st.markdown(f"""
            <div style="text-align:center; padding:32px 24px; border:1px solid #e5e7eb;
                        border-radius:16px; background:#ffffff;
                        box-shadow:0 2px 12px rgba(0,0,0,0.05); height:100%;">
                <div style="font-size:40px; margin-bottom:16px;">{icon}</div>
                <h3 style="font-size:18px; font-weight:700; margin:0 0 10px; color:#1a1a2e;">
                    {title}</h3>
                <p style="font-size:14px; color:#6b7280; margin:0; line-height:1.6;">
                    {desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:72px'></div>", unsafe_allow_html=True)

    # ── Scrolling testimonial ribbon (components.html bypasses markdown parser) ─
    st.markdown(
        "<h2 style='text-align:center; margin-bottom:28px; font-size:28px;'>"
        "💬 What Students Are Saying</h2>",
        unsafe_allow_html=True,
    )

    testimonials = [
        ("Life saver for my graduation photos!",           "Fisk Senior, Class of '25"),
        ("Found an amazing braider on campus in minutes.", "Freshman, Music Dept."),
        ("Finally a platform made for us, by us.",         "Sophomore, Biology"),
        ("Booked a barber between classes — so easy!",     "Junior, Business Admin."),
        ("My loctician is right here on campus. Love it!", "Senior, Psychology"),
        ("Hair Hub changed how I prep for events.",        "Freshman, Pre-Med"),
        ("No more off-campus trips. 10/10 recommend.",     "Sophomore, Engineering"),
    ]

    all_cards = testimonials * 2   # duplicate for seamless loop
    card_html = ""
    for quote, author in all_cards:
        card_html += f"""
        <div style="display:inline-block; min-width:280px; max-width:280px;
                    border:1px solid #e5e7eb; border-radius:12px;
                    padding:24px 20px; margin:0 12px;
                    background:#ffffff; vertical-align:top;
                    box-shadow:0 2px 10px rgba(0,0,0,0.06);">
            <div style="font-size:17px; margin-bottom:10px;">&#11088;&#11088;&#11088;&#11088;&#11088;</div>
            <p style="font-size:14px; font-style:italic; color:#374151;
                      margin:0 0 12px; line-height:1.5;">&#8220;{quote}&#8221;</p>
            <span style="font-size:12px; color:#9ca3af; font-weight:600;">&#8212; {author}</span>
        </div>"""

    ribbon_html = f"""
    <!DOCTYPE html><html><head><style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ overflow: hidden; background: transparent; font-family: sans-serif; }}
    @keyframes scroll-ribbon {{
        0%   {{ transform: translateX(0); }}
        100% {{ transform: translateX(-50%); }}
    }}
    .ribbon-outer {{ overflow: hidden; width: 100%; padding: 8px 0; }}
    .ribbon-track {{
        display: flex;
        width: max-content;
        animation: scroll-ribbon 40s linear infinite;
    }}
    .ribbon-track:hover {{ animation-play-state: paused; }}
    </style></head><body>
    <div class="ribbon-outer">
        <div class="ribbon-track">{card_html}</div>
    </div>
    </body></html>"""

    components.html(ribbon_html, height=175, scrolling=False)

    st.markdown("<div style='height:64px'></div>", unsafe_allow_html=True)

    # ── About + CEO (full width) ──────────────────────────────────────────────
    st.markdown(
        "<div id='about-section'></div>"
        "<h2 style='text-align:left; margin-bottom:28px; font-size:35px; color:#FFD700;'>"
        "About</h2>",
        unsafe_allow_html=True,
    )

    about_col, ceo_col = st.columns([3, 2], gap="large")
    with about_col:
        st.markdown("""
        Hair Hub is a pioneering platform designed for the Fisk University community —
        connecting students who need hair care with talented student stylists right on campus.

        We believe every student deserves to look and feel their best, without leaving campus
        or breaking the bank.
        """)
        with st.expander("Our Mission & Vision"):
            st.markdown("**Mission**")
            st.write("Opening doors now that will remain open and beneficial to students long-term!")
            st.markdown("**Vision**")
            st.write(
                "Growing the student entrepreneurs community every school year "
                "by at least 5%. One student at a time."
            )

    with ceo_col:
        try:
            st.image(
                "Hairhub_Images/Esther Ogundele_headshot.jpg",
                caption="Esther Ogundele — Founder & CEO",
                use_container_width=True,
            )
        except Exception:
            pass

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)
    st.markdown(
        "<hr style='border:none; border-top:1px solid #e5e7eb; margin:0;'>",
        unsafe_allow_html=True,
    )

    # CSS: style the two dialog buttons in the right column as plain text links.
    # Scoped to div[data-testid="stColumn"]:has(#footer-links-marker) so it only
    # targets buttons inside that specific column and never leaks to the hero button.
    st.markdown("""
    <style>
    div[data-testid="stColumn"]:has(#footer-links-marker) button {
        background: none !important;
        border: none !important;
        color: #374151 !important;
        font-size: 20px !important;
        font-weight: 500 !important;
        padding: 0 !important;
        text-align: left !important;
        box-shadow: none !important;
        min-height: unset !important;
        line-height: 1.4 !important;
        margin-bottom: 4px !important;
    }
    div[data-testid="stColumn"]:has(#footer-links-marker) button:hover {
        color: #374151 !important;
        text-decoration: underline !important;
        background: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    footer_left, footer_right = st.columns([2, 1])
    with footer_left:
        st.markdown("""
        <div style="padding:40px 0 24px;">
            <h1 style="font-size:48px; font-weight:900; color:#FFD700;
                       margin:0 0 8px; letter-spacing:-1px;">Hair Hub</h1>
            <p style="font-size:14px; color:#6b7280; letter-spacing:1px;
                      text-transform:uppercase; margin:0;">
                Elevating the Fisk Experience</p>
        </div>
        """, unsafe_allow_html=True)

    with footer_right:
        # Anchor links scroll the page without triggering a Streamlit rerun.
        # Buttons open the dialogs directly with no URL change.
        st.markdown("""
        <div id="footer-links-marker" style="padding-top:40px; margin-right:22%;">
            <a href="#about-section"
               style="display:block; font-size:20px; color:#374151;
                      text-decoration:none; font-weight:500; margin-bottom:12px;">
                About Hair Hub</a>
            <a href="#how-it-works"
               style="display:block; font-size:20px; color:#374151;
                      text-decoration:none; font-weight:500; margin-bottom:12px;">
                How It Works</a>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Get Started", key="footer_get_started"):
            _auth_dialog()
        if st.button("Get Help", key="footer_get_help"):
            _get_help_dialog()

    st.markdown(
        "<p style='text-align:center; font-size:13px; color:#9ca3af; "
        "padding:24px 0 0; margin-bottom:-60px;'>© 2026 Hair Hub. All rights reserved.</p>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# App routing
# ─────────────────────────────────────────────────────────────────────────────

user_role   = st.session_state.get("user_role")
pending_uid = st.session_state.get("pending_uid")

# ── Unauthenticated ───────────────────────────────────────────────────────────
if pending_uid and not user_role:
    auth.render_role_selection()

elif not user_role:
    _render_landing()

# ── Authenticated ─────────────────────────────────────────────────────────────
else:
    with open("hairhub.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    _render_sidebar_notifications()

    # User header
    display_name = st.session_state.get("user_display_name", "")
    greeting     = "✂️" if user_role == "stylist" else "👋"
    col_name, col_logout = st.columns([6, 1])
    with col_name:
        st.markdown(f"#### Welcome back, **{display_name}** {greeting}")
    with col_logout:
        if st.button("Log out", use_container_width=True):
            auth.logout()

    # Dynamic nav — no Home tab
    if user_role == "stylist":
        nav_items   = ["My Profile", "Appointments"]
        nav_icons   = ["person-circle", "calendar-check"]
        default_idx = 0   # My Profile
    else:
        nav_items   = ["Stylists", "My Bookings"]
        nav_icons   = ["people-fill", "calendar-check"]
        default_idx = 0   # Stylists

    # Consume any pending nav request BEFORE the widget is instantiated.
    # Also delete the stored widget key so default_index takes effect on this run.
    _nav_target = st.session_state.pop("_nav_target", None)
    if _nav_target and _nav_target in nav_items:
        default_idx = nav_items.index(_nav_target)
        st.session_state.pop("main_nav", None)

    selected = option_menu(
        None,
        nav_items,
        icons=nav_icons,
        default_index=default_idx,
        orientation="horizontal",
        key="main_nav",
        styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "icon": {"color": "orange", "font-size": "22px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "0px",
                "--hover-color": "#eee",
            },
            "nav-link-selected": {"background-color": "#1a1a2e"},
        },
    )

    st.divider()

    if selected in ("Stylists", "My Profile"):
        Stylists.app()
    elif selected in ("My Bookings", "Appointments"):
        Book.app()

    # ── Authenticated footer ──────────────────────────────────────────────────
    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='border-top:1px solid #e5e7eb; padding-top:20px; "
        "text-align:right;'></div>",
        unsafe_allow_html=True,
    )
    _, help_col = st.columns([5, 1])
    with help_col:
        if st.button("Get Help", key="auth_help_btn", use_container_width=True):
            _get_help_dialog()
    st.markdown(
        "<p style='text-align:center; font-size:13px; color:#9ca3af; "
        "padding:16px 0 0; margin-bottom:-60px;'>© 2026 Hair Hub. All rights reserved.</p>",
        unsafe_allow_html=True,
    )
