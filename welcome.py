# welcome.py

import streamlit as st

def show_welcome():
    st.title("Select a tool from the sidebar to get started.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🎯 Lead Generator")
        st.write("Quickly find and qualify potential clients by generating business leads based on keywords and location.")

    with col2:
        st.subheader("✨ Prompts")
        st.write("Spark creativity and efficiency with AI Agent Builder and Weekly Prompts with an AI Agent Builder and Weekly Prompts for marketing and business purposes.")

    with col3:
        st.subheader("🚀 Onboarding Workflow")
        st.write("Seamlessly onboard new clients with automated processes and analysis with an automated workflow to analyze onboarding data.")

    col4, col5, col6 = st.columns(3)

    with col4:
        st.subheader("🌐 Domain Checker")
        st.write("Check the availability of domain names.")

    with col5:
        st.subheader("🗂️ Task Management")
        st.write("Manage tasks, assign them to team members, and track their progress.")