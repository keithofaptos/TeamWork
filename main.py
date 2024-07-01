import streamlit as st
import sys
import os

# Ensure the current working directory is the root of the project
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, 'leads'))
sys.path.append(os.path.join(current_dir, 'onboarding'))
sys.path.append(os.path.join(current_dir, 'domains'))
sys.path.append(os.path.join(current_dir, 'task_management'))

# Import the necessary functions from each script
from lead_generator import run_lead_generator
from onboarding_workflow import run_onboarding_workflow
from check_domain import run_domain_checker
from task_management import run_task_management

st.set_page_config(page_title="TeamWork", page_icon="🐴", layout="wide")

def main():
    st.sidebar.title("🐴 TeamWork")
    
    # Create a radio button for navigation
    page = st.sidebar.radio("Choose a tool:", ["Leads", "Onboarding", "Domains", "Task Management"])
    
    if page == "Leads":
        st.title("🎯 Lead Generator")
        run_lead_generator()
    
    elif page == "Onboarding":
        st.title("🚀 Onboarding Workflow")
        run_onboarding_workflow()
    
    elif page == "Domains":
        st.title("🌐 Domain Checker")
        run_domain_checker()

    elif page == "Task Management":
        st.title("🗂️ Task Management")
        run_task_management()

if __name__ == "__main__":
    main()
