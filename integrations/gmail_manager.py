import os.path
import base64
import re
import requests

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", 
          "https://www.googleapis.com/auth/gmail.modify"]


def get_gmail_service():
  """
  Builds and returns a Gmail API service object.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  return build("gmail", "v1", credentials=creds)


def apply_label_to_email(service, email_id, label_name):
  """
  Moves an email from INBOX to a specified label.
  If the label doesn't exist, it creates it first.
  In Gmail, 'archiving' an email is essentially removing it from the INBOX.
  """
  existing_labels = get_all_labels(service)
  label_id = None
  for label in existing_labels:
    if label["name"].lower() == label_name.lower():
      label_id = label["id"]
      break
  else:
    new_label = create_label(service, label_name)
    label_id = new_label["id"]

  modify_body = {
    "addLabelIds": [label_id],
    "removeLabelIds": ['INBOX']
  }
  try:
    service.users().messages().modify(
      userId="me", id=email_id, body=modify_body).execute()
    print(f"Email labelled successfully. Email ID: {email_id} labeled with Label: {label_id}")
  except Exception as e:
    print(f"Failed to apply label: {e}")
  

def get_all_labels(service):
  """
  Fetches all labels for the user.
  """
  results = service.users().labels().list(userId="me").execute()
  labels = results.get("labels", [])

  if not labels:
    print("No labels found.")
    return
  else:
    return labels


def create_label(service, label_name):
  """
  Creates a new label with the given name.
  """
  label_body = {
    "name": label_name,
    "labelListVisibility": "labelShow",
    "messageListVisibility": "show"
  }
  created_label = service.users().labels().create(userId="me", body=label_body).execute()
  return created_label


import re
from googleapiclient.errors import HttpError

def fetch_emails(service, total_emails, query=""):
    """
    Fetches emails based on a search query. 
    If no query is provided, it just gets the latest emails.
    """
    try:
        # We pass the raw query directly to 'q'
        results = service.users().messages().list(
            userId="me", 
            labelIds=["INBOX"], # NOTE: Remove this if you want to include archived emails!
            maxResults=total_emails,
            q=query
        ).execute()
        
        messages = results.get("messages", [])
        emails_for_processing = []

        if not messages:
            print(f"No messages found for query: '{query}'")
            return []
        
        for msg in messages:
            m = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()

            payload = m["payload"]
            headers = payload.get("headers", [])

            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown Sender")
            body_snippet = m.get("snippet", "")
            unsub_header = next((h["value"] for h in headers if h["name"].lower() == "list-unsubscribe"), None)

            unsub_url = None
            if unsub_header:
                links = re.findall(r'<(http[^>]+)>', unsub_header)
                if links:
                    unsub_url = links[0]

            emails_for_processing.append({
                "id": msg["id"],
                "sender": sender,
                "subject": subject,
                "body_snippet": body_snippet,
                "unsubscribe_url": unsub_url
            })
            
        return emails_for_processing

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []
    
    
def delete_email(service, email_id):
  """
  Moves an email to the trash.
  """
  try:
    service.users().messages().trash(userId="me", id=email_id).execute()
    print(f"Email {email_id} moved to trash.")
  except Exception as e:
    print(f"Failed to trash email: {e}")

def unsubscribe_from_email(service, email_id, unsub_url):
  """
  Unsubscribes from an email using the provided unsubscribe URL.
  """
  try:
    response = requests.get(unsub_url, timeout=5)
    if response.status_code < 400:
      print(f"Successfully unsubscribed using {unsub_url}")
      delete_email(service, email_id)
    else:
      print(f"Unsubscribe link returned status {response.status_code}")
  except Exception as e:
    print(f"Failed to unsubscribe: {e}")

if __name__ == "__main__":
  service = get_gmail_service()
  latest_emails = fetch_latest_emails(service, count=5)
  print(latest_emails)
