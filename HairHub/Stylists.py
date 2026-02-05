import streamlit as st

def app():
    # 1. Add CSS to force image dimensions and 'cover' behavior
    st.markdown("""
        <style>
        /* Target images inside the streamlit containers */
        [data-testid="stImage"] img {
            width: 100%;
            height: 200px; /* Force all images to this height */
            object-fit: cover; /* This crops the image to fill the space without stretching */
            border-radius: 5px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title('Stylists Spotlight')
    services = ["Braiders", "Barbers", "Locticians"]
  
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border=True):
            st.image("HairHub/Hairhub_Images/Braider.jpeg")
            st.button(services[0], key="btn_braider", use_container_width=True)

    with col2:
        with st.container(border=True):
            st.image("HairHub/Hairhub_Images/Barber.jpeg")
            st.button(services[1], key="btn_barber", use_container_width=True)
        
    with col3:
        with st.container(border=True):
            st.image("HairHub/Hairhub_Images/Loctician.jpg")
            st.button(services[2], key="btn_loc", use_container_width=True)

    st.divider() 

    # Sample Braider Section
    st.title("Sample Braider")
    
    col_img, col_text = st.columns([2, 3])
    
    with col_img:
        with st.container(border=True):
            st.image("HairHub/Hairhub_Images/Sample_Braider.webp", use_container_width=True)
            st.markdown("<h3 style='text-align: center;'>Anna</h3>", unsafe_allow_html=True)
        
    with col_text:
        st.subheader("About Anna")
        st.write("""
            Anna is a Braider from Memphis, TN with 10 years of experience. 
            She specializes in braids of various sizes with extra care to 
            every client she encounters.
        """)
        
        st.markdown("#### Her Services")
        st.markdown("""
        * Regular Braids
        * Stitch Braids
        * Fulani Braids
        * Locs
        """)
        
        st.info("**Handles:** IG: @anna_hair | Facebook: @annahair_")

if __name__ == "__main__":
    app()