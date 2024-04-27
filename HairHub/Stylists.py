import streamlit as st

def app():
    st.title('Stylists Spotlight')
    # Add content for Stylists page here
    services = ["Braiders", "Barbers", "Locticians"]
  
    col1, col2, col3 = st.columns(3)
    with col1:

        mood_board1 = ""
        image_url = "https://storage.cloud.google.com/ceo_image/Image1.jpeg"
        mood_board1 += f"""
            <div class='mood-item'>
                <img src="{image_url}" alt='Image' width="150" height="150">
            </div>
        """
        st.markdown(mood_board1, unsafe_allow_html=True)
        st.button(services[0])

    with col2:
        mood_board2 = ""
        image_url = "https://storage.cloud.google.com/ceo_image/Image%202.jpeg"
        mood_board2 += f"""
            <div class='mood-item'>
                <img src="{image_url}" alt='Image' width="150" height="150">
            </div>
        """
        
        st.markdown(mood_board2, unsafe_allow_html=True)
        st.button(services[1])
        
    with col3:
        mood_board3 = ""
        image_url = "https://storage.cloud.google.com/ceo_image/Image%203.png"
        mood_board3 += f"""
            <div class='mood-item'>
                <img src="{image_url}" alt='Image' width="150" height="150">
            </div>
        """
        
        st.markdown(mood_board3, unsafe_allow_html=True)
        st.button(services[2])
        
   

    st.title("Sample Braider")
    # st.title(title)
    col1, col2 = st.columns([2, 3])
    with col1:
        mood_board4 = ""
        image_url = "https://storage.cloud.google.com/ceo_image/Image5.jpeg"
        mood_board4 += f"""
            <div class='mood-item'>
                <img src="{image_url}" alt='Image' width="280" height="280">
                <h3>{"Anna"}</h3>
            </div>
        """
        st.markdown(mood_board4, unsafe_allow_html=True)
    with col2:
        st.write(
            "<div style='margin-left: -2px;'>"
            "Anna is a Braider from Memphis TN with a 10 year experience. "
            "She specializes in braids of various sizes with extra care to "
            "every client she encounters."
            "</div>",
            unsafe_allow_html=True
        )
        st.write(
            "<div style='margin-left: -2px;'>"
            "<h4>Her Services:</h4>"
            "<ul>"
            "<li>Regular Braids</li>"
            "<li>Stitch Braids</li>"
            "<li>Fulani Braids</li>"
            "<li>Locs</li>"
            "</ul>"
            "Handles: I.G: @anna_hair, Facebook: @annahair_"
            "</div>",
            unsafe_allow_html=True
        )
    

if __name__ == "__main__":
    app()
