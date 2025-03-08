import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import pages
from app.pages import dashboard, weather_page, subway_page
from app.sidebar import create_sidebar

# Configure the page
st.set_page_config(
    page_title="NYC Local Dashboard",
    page_icon="🗽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
try:
    css_file = "app/assets/styles.css"
    if os.path.exists(css_file):
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"CSS file not found at {css_file}")
except Exception as e:
    st.warning(f"Error loading CSS: {e}")

# Create sidebar and get selected page
selected_page = create_sidebar()

# Display the selected page
if selected_page == "Dashboard":
    dashboard.show()
elif selected_page == "Weather":
    weather_page.show()
elif selected_page == "Subway":
    subway_page.show()