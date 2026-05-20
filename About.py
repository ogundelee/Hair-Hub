import streamlit as st


def app():
    st.title("About Hair Hub")

    st.markdown("""
    Hair Hub is a pioneering platform designed for the Fisk University community —
    connecting students who need hair care with talented student stylists right on campus.

    We believe every student deserves to look and feel their best, without leaving campus
    or breaking the bank.
    """)

    st.divider()

    col_text, col_img = st.columns([3, 2])

    with col_text:
        st.markdown("### Mission")
        st.write("Opening doors now that will remain open and beneficial to students long-term!")

        st.markdown("### Vision")
        st.write(
            "Growing the student entrepreneurs community every school year by at least 5%. "
            "One student at a time."
        )

    with col_img:
        st.image(
            "Hairhub_Images/Esther Ogundele_headshot.jpg",
            caption="Esther Ogundele — Founder & CEO",
            use_container_width=True,
        )
