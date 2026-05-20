"""
Book.py — Appointment booking page for Hair Hub.

Client view:
  - Pick a stylist from Firestore
  - Pick a service (with variant) from that stylist's profile
  - Choose date and time
  - Upload an optional inspiration photo
  - Submit → creates a booking document in Firestore
  - View and track existing bookings

Stylist view:
  - See incoming bookings (pending → confirmed → completed)
  - Update booking status
"""

import time
from datetime import datetime, timezone, date, timedelta

import streamlit as st
from google.cloud.firestore import transactional as firestore_transactional

from firebase_config import get_db
from cloudinary_config import upload_image

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

ALLOWED_IMG = ["jpg", "jpeg", "png", "webp"]

STATUS_COLORS = {
    "pending":   "#f59e0b",
    "confirmed": "#6366f1",
    "completed": "#10b981",
    "cancelled": "#ef4444",
}

STATUS_LABELS = {
    "pending":   "Pending",
    "confirmed": "Confirmed",
    "completed": "Completed",
    "cancelled": "Cancelled",
}

# Allowed status transitions (stylist-driven)
TRANSITIONS = {
    "pending":   ["confirmed", "cancelled"],
    "confirmed": ["completed", "cancelled"],
    "completed": [],
    "cancelled": [],
}

# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def app():
    user_role = st.session_state.get("user_role")

    if user_role == "stylist":
        _stylist_view()
    else:
        _client_view()


# ─────────────────────────────────────────────────────────────────────────────
# Client view
# ─────────────────────────────────────────────────────────────────────────────

def _client_view():
    st.markdown("""
    <div style="padding:20px 0 4px; text-align:center;">
        <h2 style="margin:0; font-size:40px; font-weight:800; color:#1a1a2e;">My Bookings</h2>
        <p style="margin:4px 0 0; font-size:18px; color:#6b7280;">
            Your upcoming and past appointments.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    db       = get_db()
    user_uid = st.session_state.get("user_uid", "")

    _render_client_bookings(db, user_uid)


def _create_booking(db, user_uid, user_name, stylist, service_label,
                    selected_slot, notes, inspiration_file):
    """Atomically claim a time slot and write the booking to Firestore."""
    inspiration_url = ""
    if inspiration_file:
        with st.spinner("Uploading inspiration photo…"):
            public_id = f"{int(time.time())}_{inspiration_file.name.rsplit('.', 1)[0]}"
            inspiration_url = upload_image(
                inspiration_file.getvalue(),
                folder=f"bookings/{user_uid}",
                public_id=public_id,
            )

    date_str, time_str = selected_slot.split(" ", 1)
    appt_dt = datetime.strptime(selected_slot, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)

    booking_ref  = db.collection("bookings").document()
    stylist_ref  = db.collection("stylists").document(stylist["id"])

    booking_data = {
        "clientUid":           user_uid,
        "clientName":          user_name,
        "stylistId":           stylist["id"],
        "stylistName":         stylist["name"],
        "service":             service_label,
        "appointmentDate":     appt_dt,
        "slotKey":             selected_slot,
        "status":              "pending",
        "notes":               notes,
        "inspirationImageUrl": inspiration_url,
        "createdAt":           datetime.now(timezone.utc),
    }

    try:
        transaction = db.transaction()
        _atomic_book_slot(transaction, stylist_ref, booking_ref, selected_slot, booking_data)
        date_display = datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %d, %Y")
        time_display = _fmt_slot_label(time_str)
        st.success(
            f"Appointment booked with **{stylist['name']}** on "
            f"**{date_display}** at **{time_display}**. "
            "Your stylist will confirm shortly."
        )
        for key in ("book_service", "book_notes", "book_inspiration",
                    "book_slot", "book_date_select"):
            st.session_state.pop(key, None)
        st.rerun()
    except Exception as e:
        st.error(str(e))


@firestore_transactional
def _atomic_book_slot(transaction, stylist_ref, booking_ref, slot_key, booking_data):
    """
    Read the stylist doc, verify the slot is still available, remove it,
    and create the booking — all in a single atomic transaction.
    """
    stylist_snap = stylist_ref.get(transaction=transaction)
    if not stylist_snap.exists:
        raise Exception("Stylist not found.")
    available = list(stylist_snap.to_dict().get("availableSlots", []))
    if slot_key not in available:
        raise Exception(
            "This time slot was just taken by another client. "
            "Please choose a different time."
        )
    available.remove(slot_key)
    transaction.update(stylist_ref, {"availableSlots": available})
    transaction.set(booking_ref, booking_data)


def _render_client_bookings(db, user_uid):
    """Show the current client's bookings. Auto-deletes entries older than 7 days."""
    if not user_uid:
        return
    try:
        docs = (
            db.collection("bookings")
            .where("clientUid", "==", user_uid)
            .order_by("appointmentDate")
            .stream()
        )
        bookings = [{"id": d.id, **(d.to_dict() or {})} for d in docs]
    except Exception as e:
        st.error(f"Could not load your bookings: {e}")
        return

    # Silently delete bookings whose appointment date is more than 7 days ago
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    fresh  = []
    for b in bookings:
        appt_dt = b.get("appointmentDate")
        if isinstance(appt_dt, datetime) and appt_dt.replace(tzinfo=timezone.utc) < cutoff:
            try:
                db.collection("bookings").document(b["id"]).delete()
            except Exception:
                pass
        else:
            fresh.append(b)

    if not fresh:
        st.markdown("""
        <div style="text-align:center; padding:48px 0;">
            <p style="font-size:56px; margin:0;">💇</p>
            <h3 style="color:#1a1a2e; margin:12px 0 6px;">No bookings yet</h3>
            <p style="color:#6b7280; margin:0;">
                Browse the Stylists tab to find your perfect stylist and book an appointment.
            </p>
        </div>
        """, unsafe_allow_html=True)
        return

    groups = {"pending": [], "confirmed": [], "completed": [], "cancelled": []}
    for b in fresh:
        groups.setdefault(b.get("status", "pending"), []).append(b)

    for status in ("pending", "confirmed", "completed", "cancelled"):
        bucket = groups[status]
        if not bucket:
            continue
        color = STATUS_COLORS[status]
        label = STATUS_LABELS[status]
        st.markdown(
            f"<h3 style='color:{color}; margin-bottom:4px;'>{label} ({len(bucket)})</h3>",
            unsafe_allow_html=True,
        )
        for b in bucket:
            _booking_card(b, viewer="client")
        st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Stylist view
# ─────────────────────────────────────────────────────────────────────────────

def _stylist_view():
    st.markdown("<h1 style='text-align:center;'>Appointments</h1>", unsafe_allow_html=True)

    db       = get_db()
    user_uid = st.session_state.get("user_uid", "")

    try:
        docs = (
            db.collection("bookings")
            .where("stylistId", "==", user_uid)
            .order_by("appointmentDate")
            .stream()
        )
        bookings = [{"id": d.id, **(d.to_dict() or {})} for d in docs]
    except Exception as e:
        st.error(f"Could not load bookings: {e}")
        return

    if not bookings:
        st.info("No appointments yet. Share your profile so clients can find you!")
        return

    # Silently delete appointments older than 7 days
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    fresh  = []
    for b in bookings:
        appt_dt = b.get("appointmentDate")
        if isinstance(appt_dt, datetime) and appt_dt.replace(tzinfo=timezone.utc) < cutoff:
            try:
                db.collection("bookings").document(b["id"]).delete()
            except Exception:
                pass
        else:
            fresh.append(b)

    if not fresh:
        st.info("No appointments yet. Share your profile so clients can find you!")
        return

    bookings = fresh

    # Group by status
    groups = {"pending": [], "confirmed": [], "completed": [], "cancelled": []}
    for b in bookings:
        groups.setdefault(b.get("status", "pending"), []).append(b)

    for status in ("pending", "confirmed", "completed", "cancelled"):
        bucket = groups[status]
        if not bucket:
            continue
        color = STATUS_COLORS[status]
        label = STATUS_LABELS[status]
        st.markdown(
            f"<h3 style='color:{color}; margin-bottom:4px;'>{label} ({len(bucket)})</h3>",
            unsafe_allow_html=True,
        )
        for b in bucket:
            _booking_card(b, viewer="stylist", db=db)
        st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Shared booking card
# ─────────────────────────────────────────────────────────────────────────────

def _booking_card(b: dict, viewer: str, db=None):
    """Render a single booking as an expandable card."""
    status      = b.get("status", "pending")
    color       = STATUS_COLORS.get(status, "#888")
    label       = STATUS_LABELS.get(status, status.title())
    appt_dt     = b.get("appointmentDate")
    booking_id  = b["id"]

    # Format date
    if isinstance(appt_dt, datetime):
        date_str = appt_dt.strftime("%B %d, %Y at %I:%M %p")
    else:
        date_str = str(appt_dt) if appt_dt else "Date TBD"

    if viewer == "client":
        header = f"{b.get('stylistName', '—')} · {b.get('service', '—')}"
    else:
        header = f"{b.get('clientName', '—')} · {b.get('service', '—')}"

    with st.expander(f"{header} — {date_str}", expanded=(status == "pending")):
        st.markdown(
            f"<span style='background:{color}; color:white; padding:4px 12px; "
            f"border-radius:12px; font-size:13px; font-weight:600;'>{label}</span>",
            unsafe_allow_html=True,
        )
        st.markdown("")

        has_photo = bool(b.get("inspirationImageUrl"))
        col_info, col_img = st.columns([2, 1]) if has_photo else (st.columns([1])[0], None)

        with col_info:
            st.markdown(f"**Service:** {b.get('service', '—')}")
            if viewer == "client":
                st.markdown(f"**Stylist:** {b.get('stylistName', '—')}")
            else:
                st.markdown(f"**Client:** {b.get('clientName', '—')}")
            st.markdown(f"**Date:** {date_str}")
            if b.get("notes"):
                st.markdown(
                    f"<p style='background:#f9fafb; border-left:3px solid #FFD700; "
                    f"padding:8px 12px; border-radius:4px; margin:6px 0; font-size:14px;'>"
                    f"📝 {b['notes']}</p>",
                    unsafe_allow_html=True,
                )

        if has_photo and col_img is not None:
            with col_img:
                st.image(b["inspirationImageUrl"], caption="Inspiration", use_container_width=True)

        # Status update buttons — stylist only
        if viewer == "stylist" and db is not None:
            next_statuses = TRANSITIONS.get(status, [])
            if next_statuses:
                st.markdown("**Update status:**")
                cols = st.columns(len(next_statuses))
                for i, new_status in enumerate(next_statuses):
                    btn_label = STATUS_LABELS[new_status]
                    btn_type  = "primary" if new_status in ("confirmed", "completed") else "secondary"
                    with cols[i]:
                        if st.button(btn_label, key=f"status_{booking_id}_{new_status}", type=btn_type):
                            _update_booking_status(db, booking_id, new_status)


def _update_booking_status(db, booking_id: str, new_status: str):
    try:
        db.collection("bookings").document(booking_id).update({"status": new_status})
        st.success(f"Booking marked as **{STATUS_LABELS[new_status]}**.")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to update status: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_stylists(db) -> list[dict]:
    """Return all stylist documents as plain dicts with an 'id' key."""
    try:
        docs = db.collection("stylists").stream()
        return [{"id": d.id, **d.to_dict()} for d in docs]
    except Exception as e:
        st.error(f"Could not load stylists: {e}")
        return []


def _fmt_slot_label(t_str: str) -> str:
    """Format 'HH:MM' → '9:00 AM' with no leading zero."""
    h, m = map(int, t_str.split(":"))
    suffix = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d} {suffix}"


def _build_service_options(services: list) -> list[str]:
    """
    Flatten a stylist's services list into selectable strings.

    New format: [{name, duration, variants: [{option, price}]}]
    Legacy:     [{style, price, duration}]
    """
    options = []
    for svc in services:
        if isinstance(svc, str):
            options.append(svc)
            continue
        name     = svc.get("name") or svc.get("style", "Service")
        duration = svc.get("duration", "")
        variants = svc.get("variants", [])
        if variants:
            for v in variants:
                opt   = v.get("option", "")
                price = v.get("price", "")
                label = f"{name}"
                if opt:
                    label += f" – {opt}"
                if price:
                    label += f" (${price})"
                if duration:
                    label += f" · {duration}"
                options.append(label)
        else:
            price = svc.get("price", "")
            label = name
            if price:
                label += f" (${price})"
            if duration:
                label += f" · {duration}"
            options.append(label)
    return options if options else ["No services listed"]
