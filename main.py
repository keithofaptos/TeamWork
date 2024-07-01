import streamlit as st
import sys
import os
from streamlit_option_menu import option_menu

# Ensure the current working directory is the root of the project
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'leads'))
sys.path.append(os.path.join(current_dir, 'onboarding'))
sys.path.append(os.path.join(current_dir, 'domains'))
sys.path.append(os.path.join(current_dir, 'task_management'))

# Set page config before any other Streamlit commands
st.set_page_config(page_title="TeamWork", page_icon="🐴", layout="wide")

# Import the necessary functions from each script
from lead_generator import run_lead_generator
from onboarding_workflow import run_onboarding_workflow
from check_domain import run_domain_checker
from task_management import run_task_management

def main():
    with st.sidebar:
        st.title("🐴 TeamWork")
        
        # Create a more visually appealing navigation menu
        selected = option_menu(
            menu_title=None,
            options=["Leads", "Onboarding", "Domains", "Task Management"],
            icons=["bullseye", "rocket-takeoff", "globe", "kanban"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#000"},
                "icon": {"color": "red", "font-size": "25px"}, 
                "nav-link": {"font-size": "16px", "color": "#999", "text-align": "left", "margin":"0px", "--hover-color": "#333"},
                "nav-link-selected": {"background-color": "#333"},
            }
        )
    
    if selected == "Leads":
        st.title("🎯 Lead Generator")
        run_lead_generator()
    
    elif selected == "Onboarding":
        st.title("🚀 Onboarding Workflow")
        run_onboarding_workflow()
    
    elif selected == "Domains":
        st.title("🌐 Domain Checker")
        run_domain_checker()

    elif selected == "Task Management":
        st.title("🗂️ Task Management")
        run_task_management()

if __name__ == "__main__":
    main()
