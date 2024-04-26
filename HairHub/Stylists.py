import streamlit as st

def app():
    st.title('Stylists')
    # Add content for Stylists page here
    services = ["Braiders", "Barbers", "Locticians"]
    for category in services:
        col1 = st.columns(1)
        with col1:
            mood_board1 = ""
            if category == "Braiders":
                image_url = "https://storage.cloud.google.com/ceo_image/Image1.jpeg"
            elif category == "Barbers":
                image_url = "https://storage.cloud.google.com/ceo_image/Image%202.jpeg"
            elif category == "Locticians":
                image_url = "https://storage.cloud.google.com/ceo_image/Image%203.png"

            mood_board1 += f"""
                <div class='mood-item'>
                    <img src="{image_url}" alt='Image' width="150" height="150">
                    <h3>{content_list[0]["title"]}</h3>
                </div>
            """
            st.markdown(mood_board1, unsafe_allow_html=True)

# if __name__ == '__main__':
#     show_stylists()




