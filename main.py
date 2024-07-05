# main.py
import streamlit as st
import sys
import os
from streamlit_option_menu import option_menu
from streamlit_extras.buy_me_a_coffee import button
import json
from welcome import show_welcome  # Import the welcome page function

# Ensure the current working directory is the root of the project
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'leads'))
sys.path.append(os.path.join(current_dir, 'onboarding'))
sys.path.append(os.path.join(current_dir, 'domains'))
sys.path.append(os.path.join(current_dir, 'task_management'))
sys.path.append(os.path.join(current_dir, 'prompts'))  # Add prompts to sys.path

# Set page config before any other Streamlit commands
st.set_page_config(page_title="TeamWork", page_icon="🐴", layout="wide")

# Import the necessary functions from each script
from lead_generator import run_lead_generator
from onboarding_workflow import run_onboarding_workflow
from check_domain import run_domain_checker
from task_management import run_task_management
from weekly_prompt import run_weekly_prompt  # Import the new function
from agent_builder import run_agent_builder  # Import the new function

custom_css = """
<style>
body, h1, h2, h3, h4, h5, h6, p {
    font-family: Helvetica, sans-serif!important;
    font-size: 18px;
}
</style>
"""

def check_secret_key(file_path, expected_key):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
            return data.get('secret_key') == expected_key
    return False

def main():
    # Show the welcome page initially
    if 'page' not in st.session_state:
        st.session_state.page = 'welcome'

    # Sidebar navigation
    with st.sidebar:
        # Style the app title
        st.markdown(
            """
            <style>
            body, h1, h2, h3, h4, h5, h6, p {
            font-family: Open Sans, Helvetica, Arial, sans-serif!important;
            }
            .app-title {
                font-size: 44px!important; /* Adjust font size as needed */
                font-family: Open Sans, Helvetica, Arial, sans-serif!important;
            }
            .app-title span {
                color: orange;
            }
            </style>
            <h1 class="app-title">🐴 Team<span>Work</span></h1>
            """,
            unsafe_allow_html=True
        )

        # Create a more visually appealing navigation menu
        selected = option_menu(
            menu_title=None,
            options=["Welcome", "Leads", "Prompts", "Onboarding", "Domains", "Task Management"],  # Add "Prompts"
            icons=["house", "bullseye", "star", "rocket-takeoff", "globe", "kanban"],  # Add an icon for "Prompts"
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "orange", "font-size": "25px"},
                "nav-link": {"font-size": "16px", "color": "#999", "text-align": "left", "margin": "0px", "--hover-color": "#333"},
                "nav-link-selected": {"background-color": "#333"},
               "nav-link": {
                "font-size": "16px", 
                "color": "#999", 
                "text-align": "left", 
                "margin": "0px", 
                "--hover-color": "#333",
                "font-family": "Open Sans, Helvetica, Arial, sans-serif"
            },
            }
        )

        # Check if the secret key JSON file exists and has the correct key
        secret_key_file = 'secret_key_off.json'
        secret_key_value = 'I_am_an_honest_person'
        if not check_secret_key(secret_key_file, secret_key_value):
            # Add Buy Me a Coffee button and image in a 2-column layout
            st.markdown("---")  # Add a separator

            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown(
                    '<a href="https://github.com/marc-shade" target="_blank"><img src="https://2acrestudios.com/wp-content/uploads/2024/06/marc-cyberpunk.png" '
                    'style="border-radius: 50%; max-width: 70px; object-fit: cover;" /></a>',
                    unsafe_allow_html=True,
                )
            with col2:
                button(
                    username=os.getenv("BUYMEACOFFEE_USERNAME", "marcshade"),
                    floating=False,
                    text="Support Marc",
                    emoji="☕",
                    bg_color="#FF5F5F",
                    font_color="#FFFFFF",
                )
            st.markdown(
                '<span style="font-size:17px; font-weight:normal; font-family:Courier;">Find this tool useful? Your support means a lot! Give a donation of $10 or more to remove this notice.</span>',
                unsafe_allow_html=True,
            )

    # Page routing
    if selected == "Welcome":
        show_welcome()
    elif selected == "Leads":
        st.title("🎯 Lead Generator")
        run_lead_generator()
    elif selected == "Prompts":
        submenu = option_menu(
            menu_title="Prompts",
            options=["Agent Builder", "Weekly Prompts"],
            icons=["calendar", "robot"],
            menu_icon="star",
            default_index=0,
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#333"},
                "icon": {"color": "orange", "font-size": "20px"},
                "nav-link": {"font-size": "14px", "color": "#FFF", "text-align": "center", "margin": "0px", "--hover-color": "#444"},
                "nav-link-selected": {"background-color": "#444"},
            }
        )

        if submenu == "Weekly Prompts":
            run_weekly_prompt()
        elif submenu == "Agent Builder":
            st.title("🤖 Agent Builder")
            run_agent_builder()
    elif selected == "Onboarding":
        st.title("🚀 Onboarding Workflow")
        run_onboarding_workflow()
    elif selected == "Domains":
        run_domain_checker()
    elif selected == "Task Management":
        st.title("🗂️ Task Management")
        run_task_management()


if __name__ == "__main__":
    main()