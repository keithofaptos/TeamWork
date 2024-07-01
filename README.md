# 🐴 TeamWork

<img src="https://2acrestudios.com/wp-content/uploads/2024/07/00007-872985090.png" style="width: 300px;" align="right" />

TeamWork is an internal tool designed to help team members manage various tasks such as generating leads, managing onboarding workflows, checking domain availability, and managing tasks. This app integrates multiple functionalities into a single Streamlit interface for easy access and use.

**Features**

- **🎯 Lead Generator**: Generate business leads based on provided keywords and location.
- **🚀 Onboarding Workflow**: Manage and analyze onboarding workflows using email data.
- **🌐 Domain Checker**: Check the availability of domain names.
- **🗂️ Task Management**: Manage tasks, assign them to team members, and track their progress.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/2acrestudios/teamwork.git
    cd teamwork
    ```

2. Create a virtual environment and activate it:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. Run the Streamlit app:

    ```bash
    streamlit run main.py
    ```

2. Navigate through the different tools using the sidebar.

## File Structure

- `main.py`: The main entry point of the application.
- `leads/lead_generator.py`: Contains the logic for the Lead Generator tool.
- `onboarding/onboarding_workflow.py`: Contains the logic for the Onboarding Workflow tool.
- `domains/check_domain.py`: Contains the logic for the Domain Checker tool.
- `task_management/task_management.py`: Contains the logic for the Task Management tool.
- `requirements.txt`: Lists all the dependencies required for the project.
