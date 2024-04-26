import streamlit as st
from streamlit_option_menu import option_menu
import About, Book, Contact, Stylists

# st.set_page_config(
#     page_title= "Hair Hub App",
#     page_icon = "💇‍♀️",
# )
st.title('Hair Hub')
# horizontal menu
selected2 = option_menu(None, ["Home", "About", "Stylists", "Book", "Contact"],
    icons=['house', 'bullseye', "person-fill", 'calendar-check', 'telephone'],
    menu_icon="cast", default_index=0, orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#fafafa"},
        "icon": {"color": "orange", "font-size": "25px"}, 
        "nav-link": {"font-size": "18px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "green"},
    })
selected2

if selected2 == "Home":



# st.sidebar.success("Select a Page above.")
    def client_login():
        st.title('Client Login')
        choice = ('Login/Sign Up', ('Login', 'Sign Up'))
        if choice == 'Login':
            email = st.text_input('Email address')
            password = st.text_input('Password', type='password')

            st.button('Login')
        else:
            email = st.text_input('Email address')
            password = st.text_input('Password', type='password')

            new_user = st.text_input('Enter your unique username ')
            st.button('Create account')

        # if st.button('Login'):
        #     # Check if the username and password are valid
        #     if is_valid_credentials(username, password):
        #         st.success('Logged in as client')
        #         show_overview()
        #     else:
        #         st.error('Invalid username or password')
        # if st.button('Sign Up'):
        #     # Implement sign up functionality
        #     st.write("Sign up for clients")

    def business_owner_login():
        st.title('Business Owner Login')
        choice = ('Login/Sign Up', ('Login', 'Sign Up'))
        if choice == 'Login':
            email = st.text_input('Email address')
            password = st.text_input('Password', type='password')

            st.button('Login')
        else:
            email = st.text_input('Email address')
            password = st.text_input('Password', type='password')

            new_user = st.text_input('Enter your unique username ')
            st.button('Create account')
        # username = st.text_input('Username')
        # password = st.text_input('Password', type='password')
        # if st.button('Login'):
        #     # Check if the username and password are valid
        #     if is_valid_credentials(username, password):
        #         st.success('Logged in as business owner')
        #         show_overview()
        #     else:
        #         st.error('Invalid username or password')
        # if st.button('Sign Up'):
        #     # Implement sign up functionality
        #     st.write("Sign up for business owners")

    def show_overview():
        st.title('Hair Hub Overview')
        # Add content for Hair Hub overview page here

    def is_valid_credentials(username, password):
        # Add logic to check if the username and password are valid
        # This could involve checking a database or some other form of authentication
        return True

    def main():
        login_option = st.radio('Select login option', ('Client', 'Business Owner'), key="login")

        if login_option == 'Client':
            client_login()
        elif login_option == 'Business Owner':
            business_owner_login()



    if __name__ == '__main__':
        main()

if selected2 == "About":
    About.app()
if selected2 == "Stylists":
    Stylists.app()
if selected2 == "Book":
    Book.app()
if selected2 == "Contact":
    Contact.app()

# streamlit run YOURFILENAME.py --server.enableCORS=false
# streamlit run 0_🏠_Home.py --server.enableCORS=false



