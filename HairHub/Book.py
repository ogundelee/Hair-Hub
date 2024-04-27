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

    # calendar_options = {
    #     "editable": "true",
    #     "selectable": "true",
    #     "headerToolbar": {
    #         "left": "today prev,next",
    #         "center": "title",
    #         "right": "resourceTimelineDay,resourceTimelineWeek,resourceTimelineMonth",
    #     },
    #     "slotMinTime": "06:00:00",
    #     "slotMaxTime": "18:00:00",
    #     "initialView": "resourceTimelineDay",
    #     "resourceGroupField": "building",
    #     "resources": [
    #         {"id": "a", "building": "Building A", "title": "Building A"},
    #         {"id": "b", "building": "Building A", "title": "Building B"},
    #         {"id": "c", "building": "Building B", "title": "Building C"},
    #         {"id": "d", "building": "Building B", "title": "Building D"},
    #         {"id": "e", "building": "Building C", "title": "Building E"},
    #         {"id": "f", "building": "Building C", "title": "Building F"},
    #     ],
    # }
    # calendar_events = [
    #     {
    #         "title": "Event 1",
    #         "start": "2023-07-31T08:30:00",
    #         "end": "2023-07-31T10:30:00",
    #         "resourceId": "a",
    #     },
    #     {
    #         "title": "Event 2",
    #         "start": "2023-07-31T07:30:00",
    #         "end": "2023-07-31T10:30:00",
    #         "resourceId": "b",
    #     },
    #     {
    #         "title": "Event 3",
    #         "start": "2023-07-31T10:40:00",
    #         "end": "2023-07-31T12:30:00",
    #         "resourceId": "a",
    #     }
    # ]
    # custom_css="""
    #     .fc-event-past {
    #         opacity: 0.8;
    #     }
    #     .fc-event-time {
    #         font-style: italic;
    #     }
    #     .fc-event-title {
    #         font-weight: 700;
    #     }
    #     .fc-toolbar-title {
    #         font-size: 2rem;
    #     }
    # """

    # calendars = calendar(events=calendar_events, options=calendar_options, custom_css=custom_css)
    #commented it to stop displaying unnecessary stuff
    # st.write(calendars)

    

# if __name__ == '__main__':
#     show_book_with_us()

