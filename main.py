import os
import base64
import datetime
import json
import re

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Set up the Gmail API credentials and token file path
credentials_path = 'path/to/credentials.json'
token_path = 'path/to/token.json'

# Set up the required Gmail scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    """Authenticates and returns a Gmail API service instance"""
    creds = None

    # Load the stored token if it exists
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    # If no valid token is found, authenticate using the credentials file
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the token for future use
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    # Build and return the Gmail API service
    service = build('gmail', 'v1', credentials=creds)
    return service

def get_emails(user_id='me', query=''):
    """Fetches Gmail emails based on the provided query"""
    try:
        service = get_gmail_service()
        response = service.users().messages().list(userId=user_id, q=query).execute()
        messages = response.get('messages', [])

        if messages:
            for message in messages:
                msg = service.users().messages().get(userId=user_id, id=message['id']).execute()
                print(f"Subject: {get_header(msg['payload']['headers'], 'Subject')}")
                print(f"From: {get_header(msg['payload']['headers'], 'From')}")
                print(f"Date: {get_header(msg['payload']['headers'], 'Date')}")
                print(f"Snippet: {msg['snippet']}")
                print("====================================")
                # Perform additional operations with the email
                # For example, save the email content to a file
                save_email_to_file(msg)

        else:
            print('No emails found.')

    except HttpError as error:
        print(f'An error occurred: {error}')

def get_header(headers, name):
    """Helper function to extract header value from email headers"""
    for header in headers:
        if header['name'].lower() == name.lower():
            return header['value']
    return None

def save_email_to_file(email):
    """Saves the email content to a file"""
    subject = get_header(email['payload']['headers'], 'Subject')
    date = get_header(email['payload']['headers'], 'Date')
    sender = get_header(email['payload']['headers'], 'From')
    snippet = email['snippet']

    # Clean up the subject to create a valid filename
    subject = re.sub(r'[^\w\s-]', '', subject)

    # Create a filename using the subject and date
    filename = f"{date}_{subject}.txt"
    filename = filename.replace(' ', '_')

    # Create a directory to store the email files if it doesn't exist
    if not os.path.exists('email_files'):
        os.makedirs('email_files')

    # Save the email content to the file
    with open(f"email_files/{filename}", 'w') as file:
        file.write(f"Subject: {subject}\n")
        file.write(f"From: {sender}\n")
        file.write(f"Date: {date}\n")
        file.write(f"Snippet: {snippet}\n")
        file.write("====================================\n")

        # Check if the email has parts
        if 'parts' in email['payload']:
            parts = email['payload']['parts']
            for part in parts:
                if part.get('body') and part['body'].get('data'):
                    data = part['body']['data']
                    file.write(base64.urlsafe_b64decode(data).decode())
                    file.write("\n")

        # Check if the email has attachments
        if email['payload'].get('attachments'):
            attachments = email['payload']['attachments']
            for attachment in attachments:
                attachment_data = attachment['body']['attachmentData']
                file_data = base64.urlsafe_b64decode(attachment_data).decode()
                file.write(f"Attachment: {attachment['filename']}\n")
                file.write(file_data)
                file.write("\n")

# Fetch emails from a particular user
get_emails(user_id='user@example.com', query='is:unread')
