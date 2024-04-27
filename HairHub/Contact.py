import streamlit as st


def app():
    st.title('Contact Us')
    # Add content for Contact Us page here

    st.write("Have questions or feedback? We'd love to hear from you! Please fill out the form below:")

    # Contact form inputs
    name = st.text_input("Your Name")
    email = st.text_input("Your Email")
    message = st.text_area("Message", height=150)

    # Submit button
    if st.button("Submit"):
        # Validate inputs (e.g., check if email is valid)
        if not name:
            st.error("Please enter your name.")
        elif not email:
            st.error("Please enter your email.")
        elif not message:
            st.error("Please enter a message.")
        else:
            # Process the message (e.g., send email, store in database)
            st.success("Message submitted successfully! We'll get back to you soon.")


