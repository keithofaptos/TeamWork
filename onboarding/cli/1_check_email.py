import imaplib
import email
import os
from email.header import decode_header
import json
from tqdm import tqdm

# Load IMAP server and login credentials from config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

IMAP_SERVER = config['IMAP_SERVER']
EMAIL_ADDRESS = config['EMAIL_ADDRESS']
PASSWORD = config['PASSWORD']

# Local folder to store downloaded emails
LOCAL_FOLDER = 'email_downloads'

# Connect to the IMAP server
mail = imaplib.IMAP4_SSL(IMAP_SERVER)

# Login to your email account
mail.login(EMAIL_ADDRESS, PASSWORD)

# Select the mailbox you want to download emails from
mailbox = 'INBOX'
mail.select(mailbox)

# Search for all unseen (unread) emails
status, email_ids = mail.search(None, 'UNSEEN')

if status == 'OK':
    email_id_list = email_ids[0].split()
    
    # Create a progress bar
    progress_bar = tqdm(email_id_list, unit='email', desc='Downloading Emails', dynamic_ncols=True)
    
    for email_id in progress_bar:
        # Fetch the email by its ID
        status, email_data = mail.fetch(email_id, '(RFC822)')

        if status == 'OK':
            # Parse the email content
            raw_email = email_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Extract email subject
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or 'utf-8')
            
            # Create a local filename based on the email subject
            filename = f"{email_id.decode('utf-8')}_{subject}.eml"
            
            # Create the full local path, including subfolders
            local_path = os.path.join(LOCAL_FOLDER, filename)
            
            # Ensure that the directory structure exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Check if the email has not been downloaded before
            if not os.path.exists(local_path):
                # Save the email locally
                with open(local_path, 'wb') as email_file:
                    email_file.write(raw_email)
                progress_bar.set_postfix(downloaded=f"{filename}")
            else:
                progress_bar.set_postfix(skipped=f"{filename} (already exists)")

# Close the mailbox and logout
mail.close()
mail.logout()
