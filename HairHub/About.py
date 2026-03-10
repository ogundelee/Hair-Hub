import streamlit as st

st.subheader("About Us")
def app():
    st.title('The Gist')
    st.write('Hair Hub is a pioneering web-based platform designed to address the diverse' + 
    'hair care needs of students at Fisk Campus. Serving as a comprehensive central hub, Hair Hub' +
    'offers a user-friendly interface where students can seamlessly access a variety of hair' + 
    'services including braiding, barbering, and loc maintenance. Unlike existing platforms,' +
    'Hair Hub distinguishes itself by consolidating all essential hair care services into one' +
    'easily accessible platform, streamlining the process of finding and booking appointments with skilled professionals.')

    st.title('Mission')
    st.write('Opening doors now that will remain open and beneficial to students long-term!')

    st.title('Vision')
    st.write('Growing the student entrepreneurs community every school year by at least 5%. One student at a time.')

    st.title('Meet our C.E.O')
    # File path to your image
    image_path = 'Hairhub_Images/Esther Ogundele_headshot.jpg'

    st.image(image_path, caption='Esther Ogundele - C.E.O of Hair Hub', use_container_width=True)

# if __name__ == '__main__':
#     app()

