#TeamWork weekly_prompt.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from contextlib import contextmanager
import ollama
import time
import re
import os
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
from ollama_utils import get_available_models  # Import the function
import base64  # Import base64 for encoding

# Email settings
EMAIL_SUBJECT = "Prompt of the Week"
UNSUBSCRIBE_LINK_TEMPLATE = "https://yourdomain.com/unsubscribe?email={email}"

# Initialize session state variables
def init_session_state():
    if 'prompts_df' not in st.session_state:
        st.session_state.prompts_df = pd.DataFrame(columns=['prompt', 'status', 'approval_date', 'delete'])
    if 'used_prompts' not in st.session_state:
        st.session_state.used_prompts = []
    if 'workflow_log' not in st.session_state:
        st.session_state.workflow_log = []
    if 'email_content' not in st.session_state:
        st.session_state.email_content = ""
    if 'selected_prompt' not in st.session_state:
        st.session_state.selected_prompt = None
    if 'selected_model_prompt' not in st.session_state:
        available_models = get_available_models()
        st.session_state.selected_model_prompt = available_models[0] if available_models else None
    if 'selected_model_email' not in st.session_state:
        available_models = get_available_models()
        st.session_state.selected_model_email = available_models[0] if available_models else None

init_session_state()

@contextmanager
def get_db_connection():
    conn = sqlite3.connect('prompts.db')
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prompts'")
        if not c.fetchone():
            c.execute('''CREATE TABLE prompts
                         (id INTEGER PRIMARY KEY, prompt TEXT, status TEXT, approval_date TEXT)''')
        else:
            c.execute("PRAGMA table_info(prompts)")
            columns = [column[1] for column in c.fetchall()]
            if 'approval_date' not in columns:
                c.execute("ALTER TABLE prompts ADD COLUMN approval_date TEXT")
        conn.commit()

def delete_prompt_from_db(prompt):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM prompts WHERE prompt = ?", (prompt,))
        conn.commit()

def save_prompt_to_db(prompt, status, approval_date=None):
    if approval_date is not None:
        approval_date = approval_date.strftime('%Y-%m-%d %H:%M:%S')
    with get_db_connection() as conn:
        conn.execute("INSERT OR REPLACE INTO prompts (prompt, status, approval_date) VALUES (?, ?, ?)",
                     (prompt, status, approval_date))
        conn.commit()

def load_prompts_from_db():
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("PRAGMA table_info(prompts)")
        columns = [column[1] for column in c.fetchall()]
        if 'approval_date' in columns:
            c.execute("SELECT prompt, status, approval_date FROM prompts")
        else:
            c.execute("SELECT prompt, status FROM prompts")
        prompts = c.fetchall()
        if 'approval_date' not in columns:
            prompts = [(prompt, status, None) for prompt, status in prompts]
    return prompts

def generate_prompts(num_prompts=3, model_name='mistral:instruct', temperature=0.2):
    new_prompts = []
    example_prompts = [
        """Write a blog post about the importance of local SEO for small retail businesses. Highlight practical tips and real-world examples.""",
        
        """Create a social media content calendar for the next month that focuses on promoting new products and engaging with customers. Include post ideas and suggested captions.""",
        
        """Develop a marketing campaign to attract customers during the holiday season. Outline the key messages, channels to use, and promotional offers.""",
        
        """Write a series of email newsletters to keep customers informed about upcoming sales, new products, and company news. Include subject lines and main content points.""",
        
        """Brainstorm three innovative marketing strategies for a small bakery to increase foot traffic and online orders.""",
        
        """Generate a detailed plan for a customer loyalty program that includes rewards, referral bonuses, and engagement tactics.""",
        
        """Create a crisis management plan for handling negative reviews and customer complaints online. Include steps for immediate response and long-term reputation management.""",
        
        """Write a guide on how to effectively use social media ads to target local customers. Include budget tips and ad design suggestions.""",
        
        """Develop a content strategy for a small business blog that aims to increase website traffic and engage the audience. Outline topics, posting frequency, and promotion tactics.""",
        
        """Create a scenario where a small business faces a sudden supply chain disruption. Outline steps they can take to mitigate the impact and maintain customer satisfaction."""
    ]
    
    for _ in range(num_prompts):
        try:
            # Include temperature in the prompt string
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

Here's a random core concept for an agent prompt to guide you:

{random.choice(example_prompts)}

Now, generate a complete prompt for a different aspect of small business operations.
?t={temperature}"""  

            response = ollama.generate(
                model=model_name,
                prompt=prompt_with_temp # Use the modified prompt 
            )
            new_prompt = response['response'].strip()

            if new_prompt not in st.session_state.used_prompts and new_prompt not in new_prompts:
                new_prompts.append(new_prompt)
                st.session_state.used_prompts.append(new_prompt)
                save_prompt_to_db(new_prompt, 'review')
        except Exception as e:
            st.error(f"Error generating prompt: {e}")
    return new_prompts

def log_step(step_description):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.workflow_log.append(f"{timestamp}: {step_description}")

def generate_email_content(prompt, model_name='mistral:instruct', temperature=0.4):
    """Generates email content to deliver the prompt of the week."""
    try:
        # Insert the prompt directly into the instructions with placeholders
        prompt_with_temp = f"""You are an expert email marketer and your job is to create an email to deliver the 'Prompt of the Week' to small business owners. 
Here is the prompt for your own reference to inform your writing, but do not include it in the email yourself, it's only for your reference:
{prompt}

The complete prompt will be inserted programmatically into this email at the location marked with 'PROMPT_INSERTION'. Do not include that text as part of your generated response though, it gets done programatically.

Your task is to write the rest of the email, ensuring the content flows naturally with the inserted prompt:

1. Start the email with a brief introduction explaining the purpose of the 'Prompt of the Week'.
2. Then, explain who would benefit from this prompt and why.
3. Provide simple instructions on how to use the prompt as a user that will copy and paste and maybe tweak it a bit. They will copy it from the email and paste it into the chat interface in ChatGPT https://chatgpt.com/ or whatever AI agent they are using. Tell them to keep a prompt library of their own.
4. **IMPORTANT:** At the location marked 'PROMPT_INSERTION', the complete prompt will be inserted programmatically. Ensure your email content flows smoothly before and after this insertion point. 
5. Close with an encouragement to engage with the prompt and a brief sign-off.

The email should be friendly, and encourage recipients to use the prompt. Do not use the prompt to generate content; instead, focus on delivering it directly as it is.

?t={temperature}"""

        response = ollama.generate(
            model=model_name,
            prompt=prompt_with_temp  # Use the modified prompt
        )
        email_content = response['response'].strip()

        # Insert the prompt programmatically ONLY ONCE
        email_content = email_content.replace('PROMPT_INSERTION', f"```\n{prompt}\n```")

        return email_content
    except Exception as e:
        st.error(f"Error generating email content: {e}")
        return ""

def sanitize_filename(name):
    """Sanitize the filename by removing disallowed characters and limiting length."""
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    return name[:50]  # Limit length to 50 characters

def save_email_as_eml(email_content, filename):
    """Save the email content as a .eml file."""
    msg = MIMEMultipart()
    msg['Subject'] = EMAIL_SUBJECT
    msg['From'] = "your_email@example.com"
    msg['To'] = "recipient@example.com"
    msg.attach(MIMEText(email_content, 'plain'))
    
    if not os.path.exists('emails'):
        os.makedirs('emails')
    filepath = os.path.join('emails', filename)
    with open(filepath, 'w') as f:
        f.write(msg.as_string())
    st.success(f"Email saved as {filename}")
    return filepath  # Return the filepath

# Create a function to run the weekly prompt script
def run_weekly_prompt():
    # Initialize session state variables
    init_session_state()  # Call the initialization function

    # Initialize database
    init_db()

    # Load prompts from database
    db_prompts = load_prompts_from_db()
    st.session_state.prompts_df = pd.DataFrame(db_prompts, columns=['prompt', 'status', 'approval_date'])
    st.session_state.prompts_df['delete'] = False

    # Model Selection for Prompt Generation
    st.sidebar.header("Prompt Generation Settings")
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
        with st.spinner("Generating prompts..."):
            new_prompts = generate_prompts(
                model_name=selected_model_prompt,
                temperature=temperature_prompt
            )
            new_prompts_df = pd.DataFrame(new_prompts, columns=['prompt'])
            new_prompts_df['status'] = 'review'
            new_prompts_df['approval_date'] = None
            new_prompts_df['delete'] = False
            st.session_state.prompts_df = pd.concat([st.session_state.prompts_df, new_prompts_df], ignore_index=True)
            log_step(f"Generated {len(new_prompts)} new prompts")
        st.success("New prompts generated and added to the review queue")
        st.balloons()

    # Display DataFrame with prompts
    st.header("🔢 Prompt Queue")
    st.write("Review each prompt by clicking on each prompt in the list. Approve them by clicking on the 'Status' setting for each one. Setting it to 'approved' will promote the prompt to the next step, generating the email.")
    if not st.session_state.prompts_df.empty:
        st.session_state.prompts_df['approval_date'] = pd.to_datetime(st.session_state.prompts_df['approval_date'], errors='coerce')

        edited_df = st.data_editor(
            st.session_state.prompts_df,
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
        st.session_state.prompts_df = edited_df.copy()

        # Delete selected rows
        if st.button("❌ Delete Selected Prompts"):
            to_delete = st.session_state.prompts_df[st.session_state.prompts_df['delete'] == True]
            if not to_delete.empty:
                for idx, row in to_delete.iterrows():
                    delete_prompt_from_db(row['prompt'])
                st.session_state.prompts_df = st.session_state.prompts_df[st.session_state.prompts_df['delete'] == False]
                st.session_state.prompts_df.reset_index(drop=True, inplace=True)
                st.success("Selected prompts deleted.")
                st.rerun()
            else:
                st.warning("No prompts selected for deletion.")

        # Update statuses and approval dates
        for i, row in st.session_state.prompts_df.iterrows():
            if row['status'] == 'approved' and pd.isnull(row['approval_date']):
                st.session_state.prompts_df.at[i, 'approval_date'] = datetime.now()
                save_prompt_to_db(row['prompt'], 'approved', st.session_state.prompts_df.at[i, 'approval_date'])

    # Select an approved prompt to process
    st.header("👍 Select Approved Prompt for Processing")
    approved_prompts = st.session_state.prompts_df[st.session_state.prompts_df['status'] == 'approved']

    if not approved_prompts.empty:
        selected_prompt = st.selectbox("Select a prompt to process", approved_prompts['prompt'].tolist())

        # Model Selection for Email Content
        st.sidebar.header("Email Content Generation Settings")
        selected_model_email = st.sidebar.selectbox(
            "Select Model for Email Content:",
            available_models,
            key="selected_model_email",
            index=available_models.index(st.session_state.selected_model_email) if st.session_state.selected_model_email in available_models else 0
        )
        temperature_email = st.sidebar.slider("Temperature for Email Content:", 0.0, 1.0, 0.2, 0.1)

        if selected_prompt and st.button("✉️ Generate Email Content"):
            st.session_state.selected_prompt = selected_prompt
            st.session_state.email_content = generate_email_content(
                selected_prompt,
                model_name=selected_model_email,
                temperature=temperature_email
            )
            log_step(f"Generated email content for prompt: {selected_prompt}")

            # Delete the prompt from the database
            delete_prompt_from_db(selected_prompt) 
            st.rerun()

    # Email content generation and editing
    st.header("✉️ Email Content")
    if st.session_state.email_content:
        edited_email = st.text_area("Edit the email content:", st.session_state.email_content, height=300)
        if st.button("👀 Preview Email"):
            st.title("Email Preview:")
            st.write(edited_email)
            log_step("Displayed email preview")

        if st.button("📥 Save Email as .eml"):
            sanitized_filename = sanitize_filename(st.session_state.selected_prompt)
            save_email_as_eml(edited_email, f"{sanitized_filename}.eml")
            log_step(f"Saved email as .eml: {sanitized_filename}.eml")
            st.session_state.email_content = ""
            st.rerun()

    # Display saved .eml files
    st.header("📨 Saved Email Files")
    if os.path.exists('emails'):
        for filename in os.listdir('emails'):
            if filename.endswith(".eml"):
                col1, col2, col3 = st.columns([3, 1, 1])  # 3 columns for filename, download, delete
                with col1:
                    st.write(filename)  # Display filename
                with col2:
                    with open(os.path.join('emails', filename), 'rb') as f:
                        eml_content = f.read()
                    b64 = base64.b64encode(eml_content).decode()
                    st.download_button(
                        label="📥 Download Email",
                        data=eml_content,
                        file_name=filename,
                        mime='message/rfc822',
                        key=f"download_{filename}"
                    )
                with col3:
                    # Add a unique key to the delete button
                    if st.button(f"❌ Delete Email", key=f"delete_{filename}"):
                        os.remove(os.path.join('emails', filename))
                        st.success(f"File {filename} deleted.")
                        st.rerun()
    else:
        st.info("No email files saved yet.")

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
    log_entries = "<br>".join(reversed(st.session_state.workflow_log))
    st.markdown(f"<div class='terminal'>{log_entries}</div>", unsafe_allow_html=True)
