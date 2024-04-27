import streamlit as st
# from streamlit_calendar import calendar
from datetime import datetime
def app():
    st.title('Book With Us')
    # Add content for Book With Us page here


    # Dictionary to store appointments
    appointments = {}

    # Display calendar interface
    selected_date = st.date_input("Select a date for your appointment")

    # Get user input for appointment time
    appointment_time = st.time_input("Select a time for your appointment")

    # Book appointment
    if st.button("Book Appointment"):
        if selected_date in appointments:
            appointments[selected_date].append(appointment_time)
        else:
            appointments[selected_date] = [appointment_time]
        st.success(f"Appointment booked for {selected_date} at {appointment_time}")

    # Display booked appointments
    if selected_date in appointments:
        st.write("Booked Appointments:")
        for time_slot in appointments[selected_date]:
            st.write(f"- {selected_date} at {time_slot}")
    else:
        st.write("No appointments booked for selected date")


