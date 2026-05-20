"""
Stylists.py — Professional stylist portfolio page for Hair Hub.

Views:
  - Browser  : specialty-filtered grid of stylist cards
  - Profile  : cover photo banner, bio, variant-priced services, portfolio gallery
  - Edit mode: dynamic portfolio editor (owner only) with file uploads
  - Create   : first-time profile setup for new stylist accounts
"""

import time
import streamlit as st
import pandas as pd
from datetime import datetime, timezone, date, timedelta

from firebase_config import get_db
from cloudinary_config import upload_image as _cloudinary_upload
from google.cloud.firestore import transactional as firestore_transactional

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

SPECIALTIES = ["Braider", "Barber", "Loctician"]

BADGE_COLOR = {
    "Braider":   "#6366f1",
    "Barber":    "#0ea5e9",
    "Loctician": "#10b981",
}

MAX_PORTFOLIO  = 12
BIO_PREVIEW    = 200
ALLOWED_IMG    = ["jpg", "jpeg", "png", "webp"]

_COVER_PLACEHOLDER = (
    "https://images.unsplash.com/photo-1560066984-138dadb4c035"
    "?w=1200&q=80&auto=format&fit=crop"
)

# ─────────────────────────────────────────────────────────────────────────────
# Booking dialog — opens from a stylist's profile page
# ─────────────────────────────────────────────────────────────────────────────

@st.dialog("Book an Appointment")
def _booking_dialog(db, doc, user_uid, user_name):
    from Book import _build_service_options

    stylist_id   = doc.get("uid", "")
    stylist_name = doc.get("name", "")
    specialty    = doc.get("specialty", "")
    avatar       = doc.get("profileImageUrl") or _avatar_url(stylist_name)
    badge_color  = BADGE_COLOR.get(specialty, "#888")

    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:14px;
                padding:14px; background:#f9fafb;
                border-radius:10px; margin-bottom:16px;
                border:1px solid #e5e7eb;">
        <img src="{avatar}" style="width:56px; height:56px; border-radius:50%;
                                    object-fit:cover; border:2px solid {badge_color}; flex-shrink:0;">
        <div>
            <p style="margin:0; font-size:17px; font-weight:700; color:#1a1a2e;">{stylist_name}</p>
            <span style="background:{badge_color}; color:#fff; padding:2px 10px;
                         border-radius:20px; font-size:11px; font-weight:600;">{specialty}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    now_str   = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    all_slots = sorted([s for s in (doc.get("availableSlots") or []) if s > now_str])

    if not all_slots:
        st.info("No available slots right now — check back soon.")
        return

    # Group slots by date
    date_groups: dict = {}
    for slot in all_slots:
        date_groups.setdefault(slot.split(" ")[0], []).append(slot)

    date_keys   = list(date_groups.keys())
    date_labels = {d: datetime.strptime(d, "%Y-%m-%d").strftime("%A, %B %d") for d in date_keys}

    st.markdown(
        "<p style='margin:0 0 4px; font-size:13px; font-weight:600; color:#6b7280;'>DATE</p>",
        unsafe_allow_html=True,
    )
    selected_date = st.selectbox(
        "Date", date_keys, format_func=lambda d: date_labels[d],
        key="bd_date", label_visibility="collapsed",
    )
    st.markdown(
        "<p style='margin:10px 0 4px; font-size:13px; font-weight:600; color:#6b7280;'>TIME</p>",
        unsafe_allow_html=True,
    )
    selected_slot = st.radio(
        "Time", date_groups[selected_date],
        format_func=lambda s: _fmt_slot_time(s.split(" ")[1]),
        horizontal=True, key="bd_slot", label_visibility="collapsed",
    )
    if not selected_slot:
        return

    st.markdown(
        "<p style='margin:10px 0 4px; font-size:13px; font-weight:600; color:#6b7280;'>SERVICE</p>",
        unsafe_allow_html=True,
    )
    services = doc.get("services") or []
    if not services:
        st.warning("This stylist hasn't listed any services yet.")
        service_label = None
    else:
        service_label = st.selectbox(
            "Service", _build_service_options(services),
            key="bd_service", label_visibility="collapsed",
        )

    st.markdown(
        "<p style='margin:10px 0 4px; font-size:13px; font-weight:600; color:#6b7280;'>"
        "INSPIRATION PHOTO <span style='font-weight:400;'>(optional)</span></p>",
        unsafe_allow_html=True,
    )
    inspiration_file = st.file_uploader(
        "Upload inspiration photo", type=ALLOWED_IMG,
        key="bd_inspiration", label_visibility="collapsed",
    )
    st.markdown(
        "<p style='margin:10px 0 4px; font-size:13px; font-weight:600; color:#6b7280;'>NOTES</p>",
        unsafe_allow_html=True,
    )
    notes = st.text_area(
        "Notes for your stylist", max_chars=500,
        key="bd_notes", label_visibility="collapsed",
        placeholder="Any special requests or details for your stylist…",
    )

    st.divider()
    if st.button("Confirm Booking", type="primary", use_container_width=True, key="bd_submit"):
        if not service_label:
            st.error("Please select a service.")
            return

        inspiration_url = ""
        if inspiration_file:
            with st.spinner("Uploading…"):
                public_id = f"{int(time.time())}_{inspiration_file.name.rsplit('.', 1)[0]}"
                inspiration_url = _cloudinary_upload(
                    inspiration_file.getvalue(),
                    folder=f"bookings/{user_uid}",
                    public_id=public_id,
                )

        date_str, time_str = selected_slot.split(" ", 1)
        appt_dt = datetime.strptime(selected_slot, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)

        booking_ref  = db.collection("bookings").document()
        stylist_ref  = db.collection("stylists").document(stylist_id)
        booking_data = {
            "clientUid":           user_uid,
            "clientName":          user_name,
            "stylistId":           stylist_id,
            "stylistName":         stylist_name,
            "service":             service_label,
            "appointmentDate":     appt_dt,
            "slotKey":             selected_slot,
            "status":              "pending",
            "notes":               notes,
            "inspirationImageUrl": inspiration_url,
            "createdAt":           datetime.now(timezone.utc),
        }

        try:
            _run_booking_transaction(
                db.transaction(), stylist_ref, booking_ref, selected_slot, booking_data
            )
            date_display = datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y")
            st.success(
                f"Booked with **{stylist_name}** on **{date_display}** "
                f"at **{_fmt_slot_time(time_str)}**. Your stylist will confirm shortly."
            )
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


@firestore_transactional
def _run_booking_transaction(transaction, stylist_ref, booking_ref, slot_key, booking_data):
    """Atomically claim the slot and create the booking."""
    snap = stylist_ref.get(transaction=transaction)
    if not snap.exists:
        raise Exception("Stylist not found.")
    available = list(snap.to_dict().get("availableSlots", []))
    if slot_key not in available:
        raise Exception(
            "This time slot was just taken by another client. "
            "Please choose a different time."
        )
    available.remove(slot_key)
    transaction.update(stylist_ref, {"availableSlots": available})
    transaction.set(booking_ref, booking_data)


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def app():
    db        = get_db()
    user_uid  = st.session_state.get("user_uid")
    user_role = st.session_state.get("user_role")

    if user_role == "stylist":
        _stylist_dashboard(db, user_uid)
    else:
        _client_browser(db, user_uid)


# ─────────────────────────────────────────────────────────────────────────────
# Stylist dashboard — own profile + edit tools
# ─────────────────────────────────────────────────────────────────────────────

def _stylist_dashboard(db, user_uid):
    doc = _fetch_stylist(db, user_uid)
    if doc is None:
        _show_create_profile(db, user_uid)
        return
    name = doc.get("name", "")
    st.markdown(f"""
    <div style="padding:20px 0 4px; text-align:center;">
        <h2 style="margin:0; font-size:40px; font-weight:800; color:#1a1a2e;">My Profile</h2>
        <p style="margin:4px 0 0; font-size:18px; color:#6b7280;">
            This is how clients see you on Hair Hub,
            <span style="color:#FFD700; font-weight:600;">{name}</span>.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    _show_profile(db, doc, user_uid)


# ─────────────────────────────────────────────────────────────────────────────
# Client browser — marketplace grid + profile view
# ─────────────────────────────────────────────────────────────────────────────

def _client_browser(db, user_uid):
    if "viewing_stylist_id" in st.session_state:
        doc = _fetch_stylist(db, st.session_state["viewing_stylist_id"])
        if doc is None:
            st.error("Stylist profile not found.")
            del st.session_state["viewing_stylist_id"]
            st.rerun()
            return
        if st.button("← Back to Stylists", key="back_btn"):
            del st.session_state["viewing_stylist_id"]
            for k in ("edit_mode", "_edit_uid", "_edit_svcs", "_svc_ver"):
                st.session_state.pop(k, None)
            st.rerun()
        _show_profile(db, doc, user_uid)
        return

    _show_browser(db)


# ─────────────────────────────────────────────────────────────────────────────
# Browser
# ─────────────────────────────────────────────────────────────────────────────

def _show_browser(db):
    st.title("Stylists Spotlight")

    filter_col, campus_col = st.columns([3, 1])
    with filter_col:
        selected = st.radio(
            "Specialty", ["All"] + SPECIALTIES,
            horizontal=True, label_visibility="collapsed",
        )
    with campus_col:
        on_campus_only = st.toggle("📍 On-Campus Only", value=False)

    specialty_filter = None if selected == "All" else selected
    st.divider()

    stylists = _fetch_all_stylists(db, specialty_filter)
    if on_campus_only:
        stylists = [s for s in stylists if s.get("on_campus")]

    if not stylists:
        msg = "No on-campus stylists found." if on_campus_only else "No stylists found yet — check back soon!"
        st.info(msg)
        return

    cols = st.columns(3)
    for i, doc in enumerate(stylists):
        with cols[i % 3]:
            _render_stylist_card(doc)


def _render_stylist_card(doc):
    uid       = doc.get("uid", "")
    name      = doc.get("name", "Unknown")
    specialty = doc.get("specialty", "")
    bio       = doc.get("bio", "")
    on_campus = doc.get("on_campus", False)
    color     = BADGE_COLOR.get(specialty, "#888")
    avatar    = doc.get("profileImageUrl") or _avatar_url(name)
    campus_html = (
        '<span style="font-size:11px;">📍 On Campus</span>'
        if on_campus else
        '<span style="font-size:11px; color:#9ca3af;">🚗 Off Campus</span>'
    )

    with st.container(border=True):
        st.markdown(f"""
        <div style="text-align:center; padding:12px 4px 4px;">
            <img src="{avatar}"
                 style="width:80px; height:80px; border-radius:50%;
                        object-fit:cover; border:3px solid {color};">
            <h4 style="margin:10px 0 2px;">{name}</h4>
            <span style="background:{color}; color:#fff; padding:3px 12px;
                         border-radius:20px; font-size:12px; font-weight:600;">
                {specialty}
            </span>
            <div style="margin-top:6px;">{campus_html}</div>
            <p style="margin:8px 0 0; font-size:13px; color:#666; min-height:36px;">
                {bio[:90]}{'…' if len(bio) > 90 else ''}
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.button("View Profile", key=f"view_{uid}", use_container_width=True):
            st.session_state["viewing_stylist_id"] = uid
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Full profile view
# ─────────────────────────────────────────────────────────────────────────────

def _show_profile(db, doc, user_uid):
    is_owner = bool(user_uid and user_uid == doc.get("uid"))
    _render_header(doc)

    if is_owner:
        _, toggle_col = st.columns([4, 1])
        with toggle_col:
            edit_mode = st.toggle("✏️ Edit Profile", key="edit_mode")
    else:
        edit_mode = False
        if user_uid:
            _, book_col = st.columns([4, 1])
            with book_col:
                if st.button("📅 Book", type="primary",
                             key=f"book_cta_{doc.get('uid')}",
                             use_container_width=True):
                    _booking_dialog(
                        db, doc, user_uid,
                        st.session_state.get("user_display_name", ""),
                    )

    st.divider()

    if is_owner and edit_mode:
        _render_edit_form(db, doc)
        return

    col_main, col_side = st.columns([3, 2])
    with col_main:
        _render_bio(doc)
        _render_portfolio_grid(doc)
    with col_side:
        _render_services(doc)
        _render_handles(doc)


# ── Header: cover banner → avatar overlapping → name + badges on solid bg ────

def _render_header(doc):
    name         = doc.get("name", "")
    specialty    = doc.get("specialty", "")
    on_campus    = doc.get("on_campus", False)
    color        = BADGE_COLOR.get(specialty, "#888")
    avatar       = doc.get("profileImageUrl") or _avatar_url(name)
    cover        = doc.get("coverPhotoUrl")   or _COVER_PLACEHOLDER
    campus_label = "📍 On Campus"  if on_campus else "🚗 Off Campus"
    campus_color = "#16a34a"       if on_campus else "#9ca3af"

    st.markdown(f"""
    <!-- Cover photo banner -->
    <div style="height:240px;
                background: url('{cover}') center/cover no-repeat,
                            linear-gradient(135deg,#1a1a2e,#2d3748);
                border-radius:12px; overflow:hidden;">
    </div>

    <!-- Circular avatar overlapping the cover -->
    <div style="padding:0 24px; margin-top:-48px; margin-bottom:0;">
        <img src="{avatar}"
             style="width:96px; height:96px; border-radius:50%;
                    border:4px solid white; object-fit:cover;
                    box-shadow:0 2px 12px rgba(0,0,0,0.25);">
    </div>

    <!-- Name + badges on solid background below -->
    <div style="padding:10px 24px 16px;">
        <h2 style="margin:0 0 8px; font-size:24px;">{name}</h2>
        <span style="background:{color}; color:#fff; padding:4px 14px;
                     border-radius:20px; font-size:13px; font-weight:600;
                     margin-right:6px;">
            {specialty}
        </span>
        <span style="background:{campus_color}; color:#fff; padding:4px 14px;
                     border-radius:20px; font-size:13px; font-weight:600;">
            {campus_label}
        </span>
    </div>
    """, unsafe_allow_html=True)


# ── Bio ───────────────────────────────────────────────────────────────────────

def _render_bio(doc):
    bio = doc.get("bio", "")
    st.markdown(
        "<h3 style='font-size:18px; font-weight:700; color:#FFD700; "
        "border-left:3px solid #FFD700; padding-left:10px; margin-bottom:10px;'>About</h3>",
        unsafe_allow_html=True,
    )
    if not bio:
        st.caption("No bio added yet.")
        return
    if len(bio) <= BIO_PREVIEW:
        st.write(bio)
    else:
        st.write(bio[:BIO_PREVIEW] + "…")
        with st.expander("Read more"):
            st.write(bio)


# ── Services with variant pricing ─────────────────────────────────────────────

def _render_services(doc):
    services = [s for s in _normalize_services(doc.get("services", [])) if s.get("name")]
    st.markdown(
        "<h3 style='font-size:18px; font-weight:700; color:#FFD700; "
        "border-left:3px solid #FFD700; padding-left:10px; margin-bottom:10px;'>Services</h3>",
        unsafe_allow_html=True,
    )
    if not services:
        st.caption("No services listed yet.")
        return

    for svc in services:
        name     = svc.get("name", "")
        duration = svc.get("duration", "")
        variants = [v for v in svc.get("variants", []) if v.get("option")]
        prices   = [v.get("price", "") for v in variants if v.get("price")]
        price_display = f"From {prices[0]}" if prices else "Price on request"

        st.markdown(f"""
        <div style="background:#ffffff; border:1px solid #e5e7eb; border-radius:12px;
                    padding:14px 16px; margin-bottom:10px;
                    box-shadow:0 1px 4px rgba(0,0,0,0.05);">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div>
                    <p style="margin:0; font-size:15px; font-weight:700; color:#1a1a2e;">{name}</p>
                    {"<p style='margin:3px 0 0; font-size:12px; color:#9ca3af;'>⏱ " + duration + "</p>" if duration else ""}
                </div>
                <span style="background:#fefce8; color:#854d0e; border:1px solid #fde68a;
                             border-radius:999px; padding:4px 12px;
                             font-size:13px; font-weight:600; white-space:nowrap;">
                    {price_display}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if len(variants) > 1:
            with st.expander("Price details"):
                for v in variants:
                    opt   = v.get("option", "")
                    price = v.get("price", "")
                    st.markdown(f"• **{opt}** — {price}" if price else f"• {opt}")
        elif len(variants) == 1:
            v   = variants[0]
            opt = v.get("option", "")
            price = v.get("price", "")
            if opt and opt.lower() not in ("standard", ""):
                st.caption(f"{opt}: {price}")


# ── Social handles ────────────────────────────────────────────────────────────

def _render_handles(doc):
    handles = doc.get("handles", {})
    ig = (handles.get("ig") or "").strip().lstrip("@")
    fb = (handles.get("facebook") or "").strip().lstrip("@")
    if not ig and not fb:
        return

    st.markdown(
        "<h3 style='font-size:18px; font-weight:700; color:#FFD700; "
        "border-left:3px solid #FFD700; padding-left:10px; margin-bottom:10px;'>Contact</h3>",
        unsafe_allow_html=True,
    )
    chips = ""
    if ig:
        chips += f"""
        <a href="https://instagram.com/{ig}" target="_blank" style="
            display:inline-flex; align-items:center; gap:6px;
            background:#f3f4f6; border:1px solid #e5e7eb;
            border-radius:999px; padding:8px 16px;
            font-size:14px; font-weight:600; color:#1a1a2e;
            text-decoration:none; margin-right:8px;">
            📷 @{ig}
        </a>"""
    if fb:
        chips += f"""
        <a href="https://facebook.com/{fb}" target="_blank" style="
            display:inline-flex; align-items:center; gap:6px;
            background:#f3f4f6; border:1px solid #e5e7eb;
            border-radius:999px; padding:8px 16px;
            font-size:14px; font-weight:600; color:#1a1a2e;
            text-decoration:none;">
            👤 @{fb}
        </a>"""
    st.markdown(f"<div style='margin-top:4px;'>{chips}</div>", unsafe_allow_html=True)


# ── 3-column portfolio gallery ────────────────────────────────────────────────

def _render_portfolio_grid(doc):
    images = [u for u in doc.get("portfolioImages", []) if u]
    if not images:
        return
    st.markdown(
        "<h3 style='font-size:18px; font-weight:700; color:#FFD700; "
        "border-left:3px solid #FFD700; padding-left:10px; margin-bottom:10px;'>Portfolio</h3>",
        unsafe_allow_html=True,
    )
    cols = st.columns(3)
    for i, url in enumerate(images[:MAX_PORTFOLIO]):
        with cols[i % 3]:
            st.markdown(f"""
            <div style="border-radius:12px; overflow:hidden; margin-bottom:8px;">
                <img src="{url}" style="width:100%; display:block; object-fit:cover;">
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Edit mode — outside st.form so dynamic service buttons and uploads work freely
# ─────────────────────────────────────────────────────────────────────────────

def _render_edit_form(db, doc):
    uid = doc.get("uid")

    # Reset edit state when entering a new profile's edit view
    if st.session_state.get("_edit_uid") != uid:
        st.session_state["_edit_svcs"]  = _normalize_services(doc.get("services", []))
        st.session_state["_edit_uid"]   = uid
        st.session_state["_svc_ver"]    = 0
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        st.session_state["_edit_slots"] = sorted(
            [s for s in doc.get("availableSlots", []) if s[:10] >= today_str]
        )
        st.session_state["_slot_ver"]   = 0

    st.markdown("---")
    st.markdown("<h2 style='text-align:center;'>Edit Portfolio</h2>", unsafe_allow_html=True)

    # ── Profile image ─────────────────────────────────────────────────────────
    st.markdown("#### Profile Image")
    if doc.get("profileImageUrl"):
        st.image(doc["profileImageUrl"], width=90)
    profile_upload = st.file_uploader(
        "Upload a new profile photo", type=ALLOWED_IMG, key="profile_upload",
    )

    # ── Cover photo ───────────────────────────────────────────────────────────
    st.markdown("#### Cover Photo")
    if doc.get("coverPhotoUrl"):
        st.image(doc["coverPhotoUrl"], use_container_width=True)
    cover_upload = st.file_uploader(
        "Upload a new cover photo", type=ALLOWED_IMG, key="cover_upload",
    )

    # ── Bio + campus toggle ───────────────────────────────────────────────────
    st.markdown("#### Bio")
    bio = st.text_area(
        "Bio", value=doc.get("bio", ""), max_chars=500, height=130,
        label_visibility="collapsed",
    )
    on_campus = st.toggle("📍 Available On Campus", value=doc.get("on_campus", False))

    # ── Social handles ────────────────────────────────────────────────────────
    st.markdown("#### Social Handles")
    handles = doc.get("handles", {})
    col_ig, col_fb = st.columns(2)
    with col_ig:
        ig = st.text_input("Instagram", value=handles.get("ig", ""), placeholder="handle (no @)")
    with col_fb:
        fb = st.text_input("Facebook",  value=handles.get("facebook", ""), placeholder="handle (no @)")

    # ── Services with per-service variant editor ──────────────────────────────
    st.markdown("#### Services")
    st.caption(
        "Each service can have multiple size / length variants with individual prices."
    )

    version   = st.session_state["_svc_ver"]
    edit_svcs = st.session_state["_edit_svcs"]
    collected_services = []

    for i, svc in enumerate(edit_svcs):
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 1])
            with c1:
                svc_name = st.text_input(
                    "Service name", value=svc.get("name", ""),
                    placeholder="e.g. Knotless Braids",
                    key=f"sn_{version}_{i}", label_visibility="collapsed",
                )
            with c2:
                svc_dur = st.text_input(
                    "Duration", value=svc.get("duration", ""),
                    placeholder="e.g. 4–6 hrs",
                    key=f"sd_{version}_{i}", label_visibility="collapsed",
                )
            with c3:
                if st.button("🗑", key=f"del_{version}_{i}", help="Remove service"):
                    st.session_state["_edit_svcs"].pop(i)
                    st.session_state["_svc_ver"] += 1
                    st.rerun()

            raw_variants = svc.get("variants") or [{"option": "", "price": ""}]
            variants_df = st.data_editor(
                pd.DataFrame(raw_variants),
                num_rows="dynamic",
                use_container_width=True,
                column_config={
                    "option": st.column_config.TextColumn(
                        "Option  (e.g. Small, Medium, Large)", max_chars=50
                    ),
                    "price": st.column_config.TextColumn(
                        "Price  (e.g. $80)", max_chars=20
                    ),
                },
                key=f"sv_{version}_{i}",
            )
            collected_services.append({
                "name":     (svc_name or "").strip(),
                "duration": (svc_dur or "").strip(),
                "variants": (
                    variants_df
                    .dropna(subset=["option"])
                    .query("option != ''")
                    .to_dict("records")
                ),
            })

    if st.button("➕ Add Service", key=f"add_svc_{version}"):
        st.session_state["_edit_svcs"].append(
            {"name": "", "duration": "", "variants": [{"option": "", "price": ""}]}
        )
        st.session_state["_svc_ver"] += 1
        st.rerun()

    # ── Availability ──────────────────────────────────────────────────────────
    st.markdown(
        "<h3 style='font-size:18px; font-weight:700; color:#FFD700; "
        "border-left:3px solid #FFD700; padding-left:10px; margin:24px 0 8px;'>Availability</h3>",
        unsafe_allow_html=True,
    )
    st.caption("Add the dates and times you're open so clients can book from your real schedule.")

    slot_ver   = st.session_state.get("_slot_ver", 0)
    edit_slots = st.session_state.get("_edit_slots", [])

    TIME_OPTIONS = [f"{h:02d}:{m:02d}" for h in range(8, 20) for m in (0, 30)]

    col_avail_d, col_avail_t, col_avail_btn = st.columns([2, 3, 1])
    with col_avail_d:
        add_date = st.date_input(
            "Date", min_value=date.today(),
            value=date.today() + timedelta(days=1),
            key=f"avail_date_{slot_ver}",
            label_visibility="collapsed",
        )
    with col_avail_t:
        selected_times = st.multiselect(
            "Times", TIME_OPTIONS,
            format_func=_fmt_slot_time,
            placeholder="Pick time slots…",
            key=f"avail_times_{slot_ver}",
            label_visibility="collapsed",
        )
    with col_avail_btn:
        st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)
        if st.button("➕ Add", key=f"add_slots_{slot_ver}", use_container_width=True):
            date_str = add_date.strftime("%Y-%m-%d")
            for t in selected_times:
                slot_key = f"{date_str} {t}"
                if slot_key not in edit_slots:
                    edit_slots.append(slot_key)
            st.session_state["_edit_slots"] = sorted(edit_slots)
            st.session_state["_slot_ver"]  += 1
            st.rerun()

    if edit_slots:
        st.caption("Upcoming slots — click 🗑 to remove:")
        grouped: dict = {}
        for slot in edit_slots:
            d_part = slot.split(" ")[0]
            grouped.setdefault(d_part, []).append(slot)

        for d_str, day_slots in grouped.items():
            d_obj = datetime.strptime(d_str, "%Y-%m-%d")
            st.markdown(f"**{d_obj.strftime('%A, %B %d, %Y')}**")
            slot_cols = st.columns(min(len(day_slots), 4))
            for idx, slot in enumerate(day_slots):
                t_part = slot.split(" ")[1]
                with slot_cols[idx % 4]:
                    safe_key = slot.replace(" ", "_").replace(":", "")
                    if st.button(f"🗑 {_fmt_slot_time(t_part)}", key=f"rm_{safe_key}"):
                        st.session_state["_edit_slots"].remove(slot)
                        st.session_state["_slot_ver"] += 1
                        st.rerun()
    else:
        st.info("No upcoming slots added yet.")

    # ── Portfolio image management ────────────────────────────────────────────
    st.markdown(f"#### Portfolio Images *(up to {MAX_PORTFOLIO})*")

    existing_imgs = [u for u in doc.get("portfolioImages", []) if u]
    keep_imgs     = []

    if existing_imgs:
        st.caption("Uncheck any image to remove it from your portfolio:")
        img_cols = st.columns(4)
        for i, url in enumerate(existing_imgs):
            with img_cols[i % 4]:
                st.image(url, use_container_width=True)
                if st.checkbox(
                    "Keep", value=True,
                    key=f"keep_img_{i}", label_visibility="collapsed",
                ):
                    keep_imgs.append(url)

    remaining = MAX_PORTFOLIO - len(keep_imgs)
    if remaining > 0:
        new_imgs = st.file_uploader(
            f"Add up to {remaining} new image{'s' if remaining != 1 else ''}",
            type=ALLOWED_IMG,
            accept_multiple_files=True,
            key="new_portfolio_imgs",
        )
    else:
        st.caption(f"Portfolio is full ({MAX_PORTFOLIO}/{MAX_PORTFOLIO}).")
        new_imgs = []

    # ── Save ──────────────────────────────────────────────────────────────────
    st.divider()
    if st.button("💾  Save Changes", type="primary", use_container_width=True, key="save_edits"):
        services_clean = [s for s in collected_services if s["name"]]

        with st.spinner("Saving…"):
            try:
                profile_url_final = doc.get("profileImageUrl", "")
                cover_url_final   = doc.get("coverPhotoUrl", "")

                if profile_upload:
                    profile_url_final = _upload_image(
                        profile_upload, uid, "profile"
                    )
                if cover_upload:
                    cover_url_final = _upload_image(
                        cover_upload, uid, "cover"
                    )

                portfolio_urls = list(keep_imgs)
                for f in (new_imgs or []):
                    portfolio_urls.append(_upload_image(f, uid, "portfolio"))
                portfolio_urls = portfolio_urls[:MAX_PORTFOLIO]

                _save_profile(db, uid, {
                    "profileImageUrl": profile_url_final,
                    "coverPhotoUrl":   cover_url_final,
                    "bio":             (bio or "").strip(),
                    "on_campus":       on_campus,
                    "handles": {
                        "ig":       (ig or "").strip().lstrip("@"),
                        "facebook": (fb or "").strip().lstrip("@"),
                    },
                    "services":        services_clean,
                    "portfolioImages": portfolio_urls,
                    "availableSlots":  st.session_state.get("_edit_slots", []),
                })
            except Exception as exc:
                st.error(f"Upload failed: {exc}")


def _save_profile(db, uid, updates):
    db.collection("stylists").document(uid).update(
        {**updates, "updatedAt": datetime.now(timezone.utc)}
    )
    for k in ("_edit_uid", "_edit_svcs", "_svc_ver", "_edit_slots", "_slot_ver"):
        st.session_state.pop(k, None)
    st.success("Portfolio updated!")
    st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Create profile (new stylists)
# ─────────────────────────────────────────────────────────────────────────────

def _show_create_profile(db, uid):
    st.title("Set Up Your Portfolio")
    st.write("Tell Fisk students who you are and what you offer.")
    st.divider()

    with st.form("create_profile", border=False):
        col_name, col_spec = st.columns([2, 1])
        with col_name:
            name = st.text_input("Your Name")
        with col_spec:
            specialty = st.selectbox("Specialty", SPECIALTIES)

        bio = st.text_area(
            "Bio", max_chars=500, height=130,
            placeholder="Tell clients about your experience, style, and approach…",
        )
        on_campus = st.toggle("📍 I'm available on campus")

        st.markdown("#### Profile Photo *(optional)*")
        profile_img = st.file_uploader(
            "Upload a profile photo", type=ALLOWED_IMG, key="create_profile_img",
        )

        st.markdown("#### Services")
        st.caption(
            "Add your services with a starting price. "
            "You can add detailed size/length variants later in Manage Portfolio."
        )
        services_df = st.data_editor(
            pd.DataFrame([{"name": "", "starting_price": "", "duration": ""}]),
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "name":           st.column_config.TextColumn("Service Name",    max_chars=80, required=True),
                "starting_price": st.column_config.TextColumn("Starting Price",  max_chars=20),
                "duration":       st.column_config.TextColumn("Duration",        max_chars=30),
            },
            key="create_svc",
        )

        st.markdown("#### Social Handles *(optional)*")
        col_ig, col_fb = st.columns(2)
        with col_ig:
            ig = st.text_input("Instagram", placeholder="handle (no @)")
        with col_fb:
            fb = st.text_input("Facebook",  placeholder="handle (no @)")

        submitted = st.form_submit_button(
            "Create Profile", use_container_width=True, type="primary"
        )

    if submitted:
        if not name.strip() or not bio.strip():
            st.error("Please fill in your name and bio.")
            return

        services_clean = []
        for _, row in services_df.dropna(subset=["name"]).iterrows():
            n = str(row.get("name", "")).strip()
            if not n:
                continue
            price = str(row.get("starting_price", "")).strip()
            services_clean.append({
                "name":     n,
                "duration": str(row.get("duration", "")).strip(),
                "variants": [{"option": "Standard", "price": price}] if price else [],
            })

        with st.spinner("Creating your profile…"):
            try:
                profile_url = ""
                if profile_img:
                    profile_url = _upload_image(profile_img, uid, "profile")

                now = datetime.now(timezone.utc)
                db.collection("stylists").document(uid).set({
                    "uid":             uid,
                    "name":            (name or "").strip(),
                    "specialty":       specialty,
                    "bio":             (bio or "").strip(),
                    "on_campus":       on_campus,
                    "services":        services_clean,
                    "handles":         {"ig": (ig or "").strip().lstrip("@"), "facebook": (fb or "").strip().lstrip("@")},
                    "profileImageUrl": profile_url,
                    "coverPhotoUrl":   "",
                    "portfolioImages": [],
                    "createdAt":       now,
                    "updatedAt":       now,
                })
                st.session_state["viewing_stylist_id"] = uid
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to create profile: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _upload_image(file, uid: str, image_type: str) -> str:
    """
    Upload a Streamlit UploadedFile to Cloudinary.

    image_type: "profile" | "cover" | "portfolio"
    Returns the permanent Cloudinary URL.
    """
    if image_type == "portfolio":
        public_id = f"{int(time.time())}_{file.name.rsplit('.', 1)[0]}"
        return _cloudinary_upload(file.getvalue(), folder=f"stylists/{uid}/portfolio", public_id=public_id)
    else:
        return _cloudinary_upload(file.getvalue(), folder=f"stylists/{uid}", public_id=image_type)


def _normalize_services(raw):
    """Migrate any legacy service format to {name, duration, variants:[{option,price}]}."""
    if not raw:
        return []
    result = []
    for item in raw:
        if isinstance(item, str):
            result.append({"name": item, "duration": "", "variants": []})
        elif isinstance(item, dict):
            if "variants" in item:
                result.append(item)
            elif "style" in item:
                price = item.get("price", "")
                result.append({
                    "name":     item.get("style", ""),
                    "duration": item.get("duration", ""),
                    "variants": [{"option": "Standard", "price": price}] if price else [],
                })
            elif "name" in item:
                result.append({"variants": [], **item})
    return result


def _fetch_stylist(db, uid):
    doc = db.collection("stylists").document(uid).get()
    return doc.to_dict() if doc.exists else None


def _fetch_all_stylists(db, specialty=None):
    ref = db.collection("stylists")
    if specialty:
        ref = ref.where("specialty", "==", specialty)
    return [d.to_dict() for d in ref.stream()]


def _avatar_url(name):
    initials = "+".join(name.split()[:2]) if name else "HH"
    return f"https://ui-avatars.com/api/?name={initials}&background=random&size=200&bold=true"


def _fmt_slot_time(t_str: str) -> str:
    """Format 'HH:MM' → '9:00 AM' with no leading zero."""
    h, m = map(int, t_str.split(":"))
    suffix = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d} {suffix}"


if __name__ == "__main__":
    app()
