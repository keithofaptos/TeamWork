# agent_builder.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from contextlib import contextmanager
import ollama
import time
import re
import os
import random
from ollama_utils import get_available_models  # Import the function
import base64  # Import base64 for encoding

# Initialize session state variables
def init_session_state():
    if 'agent_prompts_df' not in st.session_state:
        st.session_state.agent_prompts_df = pd.DataFrame(columns=['prompt', 'status', 'approval_date', 'delete'])
    if 'used_agent_prompts' not in st.session_state:
        st.session_state.used_agent_prompts = []
    if 'agent_workflow_log' not in st.session_state:
        st.session_state.agent_workflow_log = []
    if 'selected_agent_prompt' not in st.session_state:
        st.session_state.selected_agent_prompt = None
    if 'selected_model_prompt' not in st.session_state:
        available_models = get_available_models()
        st.session_state.selected_model_prompt = available_models[0] if available_models else None
    if 'problem_statement' not in st.session_state:
        st.session_state.problem_statement = ""

init_session_state()

@contextmanager
def get_db_connection():
    conn = sqlite3.connect('agent_prompts.db')
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agent_prompts'")
        if not c.fetchone():
            c.execute('''CREATE TABLE agent_prompts
                         (id INTEGER PRIMARY KEY, prompt TEXT, status TEXT, approval_date TEXT)''')
        else:
            c.execute("PRAGMA table_info(agent_prompts)")
            columns = [column[1] for column in c.fetchall()]
            if 'approval_date' not in columns:
                c.execute("ALTER TABLE agent_prompts ADD COLUMN approval_date TEXT")
        conn.commit()

def delete_agent_prompt_from_db(prompt):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM agent_prompts WHERE prompt = ?", (prompt,))
        conn.commit()

def save_agent_prompt_to_db(prompt, status, approval_date=None):
    if approval_date is not None:
        approval_date = approval_date.strftime('%Y-%m-%d %H:%M:%S')
    with get_db_connection() as conn:
        conn.execute("INSERT OR REPLACE INTO agent_prompts (prompt, status, approval_date) VALUES (?, ?, ?)",
                     (prompt, status, approval_date))
        conn.commit()

def load_agent_prompts_from_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("PRAGMA table_info(agent_prompts)")
        columns = [column[1] for column in c.fetchall()]
        if 'approval_date' in columns:
            c.execute("SELECT prompt, status, approval_date FROM agent_prompts")
        else:
            c.execute("SELECT prompt, status FROM agent_prompts")
        prompts = c.fetchall()
        if 'approval_date' not in columns:
            prompts = [(prompt, status, None) for prompt, status in prompts]
    return prompts

def generate_agent_prompts(problem_statement, num_prompts=3, model_name='mistral:instruct', temperature=0.2):
    new_prompts = []
    
    for _ in range(num_prompts):
        try:
            prompt_with_temp = f"""You are an expert AI agent prompt engineer, specializing in generating unique and useful AI agent prompts for small business owners. 
Your primary functions include content creation, brainstorming ideas, and testing scenarios to address specific business challenges with the prompts.
The prompts should provide the AI agent they're for, the following information:
When creating an AI agent prompt, several key elements need to be considered to ensure clarity, context, and effective guidance for the model. 

Here is a comprehensive list of these elements:

### Core Elements of AI Agent Prompt

1. **Role Specification**:
   - Clearly define the social or occupational role of the AI Agent, such as "You are a helpful assistant," "mentor," or "partner".
   - Consider the relevance of the role to the task or query the AI Agent is expected to handle.
2. **Purpose and Identity**:
   - Articulate the core purpose and identity of the AI Agent, such as providing customer support, generating creative content, or assisting with technical queries.
3. **Context and Background**:
   - Provide detailed context for the task. For example, specify the type of content and the specific topic.
   - Include any necessary background information or specifics upfront to inform the AI Agent.
4. **Language and Tone**:
   - Customize the language, tone, and behavioral traits to align with the agent’s role. For example, empathetic language for customer support or formal language for technical advice.
   - Decide on the formality or casualness of the responses.
5. **Structure and Clarity**:
   - Use clear and specific language to outline the desired outcome, format, and style of the output.
   - Employ markup and markdown to structure the prompt, such as headers and separators to distinguish instructions from context.
6. **Examples and Pre-filled Responses**:
   - Include examples in the prompt to illustrate the desired output format or style.
   - Prefill responses with a few words to guide the output in the desired direction.
7. **Iteration and Refinement**:
   - Write, test, and refine the prompt iteratively based on the model's output. Slight changes in wording or structure can significantly impact responses.
### Advanced Techniques
1. **Visualization of Thought (VoT)**:
   - Instruct the AI Agent to visualize its thought process step-by-step to clarify understanding and context.
2. **Chain of Thought (CoT)**:
   - Encourage step-by-step thinking to improve the quality of the output by breaking down complex tasks into smaller, manageable steps.
3. **Tree of Thought (ToT)**:
   - Provide a tree-structured process for problem-solving, ensuring all possible paths and decisions are considered.
4. **Chain-of-Abstraction Reasoning**:
   - Use abstract placeholders and then call domain-specific tools to fill in detailed knowledge, ensuring comprehensive and accurate responses.
### Customization and Flexibility
1. **Scenario-Based Instructions**:
   - Include instructions for different scenarios that the AI Agent might encounter, preparing it to handle a wide range of interactions effectively.
2. **Balance Specificity and Flexibility**:
   - Provide specific instructions to guide behavior while allowing flexibility to handle unexpected situations gracefully.
3. **Consistency and Documentation**:
   - Ensure consistency in the use of formatting elements and thoroughly document prompt design choices, especially when collaborating or sharing prompts with others.
### Practical Considerations
1. **Markup and Special Characters**:
   - Use minimal markup for structuring content, ensuring clarity and organization.

Here's the problem statement provided by the user:

"{problem_statement}"

Now, generate a complete prompt for this problem statement, focusing on a different aspect of small business operations.
?t={temperature}"""

            response = ollama.generate(
                model=model_name,
                prompt=prompt_with_temp  # Use the modified prompt
            )
            new_prompt = response['response'].strip()

            if new_prompt not in st.session_state.used_agent_prompts and new_prompt not in new_prompts:
                new_prompts.append(new_prompt)
                st.session_state.used_agent_prompts.append(new_prompt)
                save_agent_prompt_to_db(new_prompt, 'review')
        except Exception as e:
            st.error(f"Error generating prompt: {e}")
    return new_prompts

def log_step(step_description):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.agent_workflow_log.append(f"{timestamp}: {step_description}")

def sanitize_filename(name):
    """Sanitize the filename by removing disallowed characters and limiting length."""
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    return name[:50]  # Limit length to 50 characters

def save_prompt_as_txt(prompt, filename):
    """Save the prompt content as a .txt file."""
    if not os.path.exists('agent_prompts'):
        os.makedirs('agent_prompts')
    filepath = os.path.join('agent_prompts', filename)
    with open(filepath, 'w') as f:
        f.write(prompt)
    st.success(f"Prompt saved as {filename}")
    return filepath  # Return the filepath

# Create a function to run the Agent Builder script
def run_agent_builder():
    # Initialize session state variables
    init_session_state()  # Call the initialization function

    # Initialize database
    init_db()

    # Load prompts from database
    db_prompts = load_agent_prompts_from_db()
    st.session_state.agent_prompts_df = pd.DataFrame(db_prompts, columns=['prompt', 'status', 'approval_date'])
    st.session_state.agent_prompts_df['delete'] = False

    # Get problem statement from user
    problem_statement = st.text_input("What problem are you trying to solve? What would you like the AI Agent to do?", st.session_state.problem_statement)
    if problem_statement:
        st.session_state.problem_statement = problem_statement

    # Model Selection for Prompt Generation
    st.sidebar.header("Agent Prompt Generation Settings")
    available_models = get_available_models()
    selected_model_prompt = st.sidebar.selectbox(
        "Select Model for Prompt Generation:",
        available_models,
        key="selected_model_prompt",
        index=available_models.index(st.session_state.selected_model_prompt) if st.session_state.selected_model_prompt in available_models else 0
    )
    temperature_prompt = st.sidebar.slider("Temperature for Prompt Generation:", 0.0, 1.0, 0.2, 0.1)

    # Button to Generate Prompts
    if st.button("🎉 Generate 3 New Prompts"):
        if not problem_statement:
            st.error("Please provide a problem statement to generate prompts.")
        else:
            with st.spinner("Generating prompts..."):
                new_prompts = generate_agent_prompts(
                    problem_statement=problem_statement,
                    num_prompts=3,
                    model_name=selected_model_prompt,
                    temperature=temperature_prompt
                )
                new_prompts_df = pd.DataFrame(new_prompts, columns=['prompt'])
                new_prompts_df['status'] = 'review'
                new_prompts_df['approval_date'] = None
                new_prompts_df['delete'] = False
                st.session_state.agent_prompts_df = pd.concat([st.session_state.agent_prompts_df, new_prompts_df], ignore_index=True)
                log_step(f"Generated {len(new_prompts)} new prompts")
            st.success("New prompts generated and added to the review queue")
            st.balloons()

    # Display DataFrame with prompts
    st.header("🔢 Agent Prompt Queue")
    st.write("Review each prompt by clicking on each prompt in the list. Approve them by clicking on the 'Status' setting for each one. Setting it to 'approved' will promote the prompt to the next step.")
    if not st.session_state.agent_prompts_df.empty:
        st.session_state.agent_prompts_df['approval_date'] = pd.to_datetime(st.session_state.agent_prompts_df['approval_date'], errors='coerce')

        edited_df = st.data_editor(
            st.session_state.agent_prompts_df,
            column_config={
                "delete": st.column_config.CheckboxColumn(
                    "Delete",
                    help="Mark prompt for deletion",
                    default=False,
                ),
                "approval_date": st.column_config.DatetimeColumn(
                    "Approval Date",
                    format="YYYY-MM-DD HH:mm:ss",
                ),
                "status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["review", "approved", "used"],
                ),
            },
            hide_index=True,
            num_rows="dynamic",
            use_container_width=True
        )

        # Update the session state DataFrame
        st.session_state.agent_prompts_df = edited_df.copy()

        # Delete selected rows
        if st.button("❌ Delete Selected Prompts"):
            to_delete = st.session_state.agent_prompts_df[st.session_state.agent_prompts_df['delete'] == True]
            if not to_delete.empty:
                for idx, row in to_delete.iterrows():
                    delete_agent_prompt_from_db(row['prompt'])
                st.session_state.agent_prompts_df = st.session_state.agent_prompts_df[st.session_state.agent_prompts_df['delete'] == False]
                st.session_state.agent_prompts_df.reset_index(drop=True, inplace=True)
                st.success("Selected prompts deleted.")
                st.rerun()
            else:
                st.warning("No prompts selected for deletion.")

        # Update statuses and approval dates
        for i, row in st.session_state.agent_prompts_df.iterrows():
            if row['status'] == 'approved' and pd.isnull(row['approval_date']):
                st.session_state.agent_prompts_df.at[i, 'approval_date'] = datetime.now()
                save_agent_prompt_to_db(row['prompt'], 'approved', st.session_state.agent_prompts_df.at[i, 'approval_date'])

    # Select an approved prompt to process
    st.header("👍 Select Approved Prompt for Processing")
    approved_prompts = st.session_state.agent_prompts_df[st.session_state.agent_prompts_df['status'] == 'approved']

    if not approved_prompts.empty:
        selected_prompt = st.selectbox("Select a prompt to process", approved_prompts['prompt'].tolist())

        if selected_prompt and st.button("💾 Save Prompt to File"):
            st.session_state.selected_agent_prompt = selected_prompt
            sanitized_filename = sanitize_filename(selected_prompt)
            save_prompt_as_txt(selected_prompt, f"{sanitized_filename}.txt")
            log_step(f"Saved prompt as .txt: {sanitized_filename}.txt")
            delete_agent_prompt_from_db(selected_prompt)  # Delete the prompt from the database
            st.rerun()

    # Display saved .txt files
    st.header("📂 Saved Prompt Files")
    if os.path.exists('agent_prompts'):
        for filename in os.listdir('agent_prompts'):
            if filename.endswith(".txt"):
                col1, col2, col3 = st.columns([3, 1, 1])  # 3 columns for filename, view, download
                with col1:
                    st.write(filename)  # Display filename
                with col2:
                    if st.button("👀 View", key=f"view_{filename}"):
                        with open(os.path.join('agent_prompts', filename), 'r') as f:
                            prompt_content = f.read()
                        st.session_state.selected_agent_prompt = prompt_content
                        edited_prompt = st.text_area("Edit the prompt content:", st.session_state.selected_agent_prompt, height=300)
                        if st.button("📥 Save Edited Prompt", key=f"save_{filename}"):
                            with open(os.path.join('agent_prompts', filename), 'w') as f:
                                f.write(edited_prompt)
                            st.success(f"Prompt {filename} has been updated.")
                            st.rerun()
                with col3:
                    with open(os.path.join('agent_prompts', filename), 'rb') as f:
                        txt_content = f.read()
                    b64 = base64.b64encode(txt_content).decode()
                    st.download_button(
                        label="📥 Download",
                        data=txt_content,
                        file_name=filename,
                        mime='text/plain',
                        key=f"download_{filename}"
                    )

    # Custom CSS for the terminal-looking log
    st.markdown("""
        <style>
        .terminal {
            background-color: #000000;
            color: #00FF00;
            font-family: monospace;
            padding: 10px;
            height: 300px;
            overflow-y: scroll;
            width: 100%;
            border-radius: 5px;
        }
        </style>
        """, unsafe_allow_html=True)

    # Display the log in the styled section
    st.header("⚙️ Workflow Log")
    log_entries = "<br>".join(reversed(st.session_state.agent_workflow_log))
    st.markdown(f"<div class='terminal'>{log_entries}</div>", unsafe_allow_html=True)