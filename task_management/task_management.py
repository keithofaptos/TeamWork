import streamlit as st
import pandas as pd
from datetime import datetime

def add_task():
    task = st.session_state.new_task
    assignee = st.session_state.assignee
    deadline = st.session_state.deadline
    priority = st.session_state.priority

    if task and assignee and deadline and priority:
        st.session_state.tasks.append({
            'Task': task,
            'Assignee': assignee,
            'Deadline': deadline,
            'Priority': priority,
            'Status': 'Pending'
        })
        st.session_state.new_task = ''
        st.session_state.assignee = ''
        st.session_state.deadline = datetime.now().date()
        st.session_state.priority = 'Medium'

def update_task_status(index, status):
    st.session_state.tasks[index]['Status'] = status

def run_task_management():
    if 'tasks' not in st.session_state:
        st.session_state.tasks = []
    
    if 'new_task' not in st.session_state:
        st.session_state.new_task = ''
    
    if 'assignee' not in st.session_state:
        st.session_state.assignee = ''
    
    if 'deadline' not in st.session_state:
        st.session_state.deadline = datetime.now().date()
    
    if 'priority' not in st.session_state:
        st.session_state.priority = 'Medium'

    # Sidebar for task input
    with st.sidebar:
        st.header("Add New Task")
        st.text_input("Task", key='new_task')
        st.text_input("Assignee", key='assignee')
        st.date_input("Deadline", value=st.session_state.deadline, key='deadline')
        st.selectbox("Priority", ['High', 'Medium', 'Low'], key='priority')
        st.button("Add Task", on_click=add_task)

    # Display tasks
    if st.session_state.tasks:
        st.subheader("Task List")
        df = pd.DataFrame(st.session_state.tasks)
        st.table(df)

        for i, task in enumerate(st.session_state.tasks):
            status = task['Status']
            if status == 'Pending':
                st.button(f"Mark as Completed - Task {i+1}", on_click=update_task_status, args=(i, 'Completed'))
            elif status == 'Completed':
                st.button(f"Mark as Pending - Task {i+1}", on_click=update_task_status, args=(i, 'Pending'))
    else:
        st.write("No tasks added yet.")

if __name__ == "__main__":
    run_task_management()
