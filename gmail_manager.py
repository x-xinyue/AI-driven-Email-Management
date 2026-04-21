import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


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


def apply_label_to_email(service, creds, email_id, label_name):
  """
  Moves an email from INBOX to a specified label.
  If the label doesn't exist, it creates it first.
  In Gmail, 'archiving' an email is essentially removing it from the INBOX.
  """
  existing_labels = get_all_labels(service)
  label_id = None
  for label in existing_labels:
    if label["id"] == label_name:
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


def fetch_latest_emails(service, count=1):
  """
  Fetches the latest emails from the user's inbox.
  """
  try:
    results = service.users().messages().list(userId="me", labelIds=["INBOX"], maxResults=count).execute()
    messages = results.get("messages", [])

    if not messages:
      print("No messages found.")
      return
    else:
      print(f"Latest {count} emails:")
      for msg in messages:
        m = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
        payload = m["payload"]
        headers = payload.get("headers", [])
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
        print(f"Email ID: {msg['id']} | Subject: {subject}")
  except HttpError as error:
    print(f"An error occurred: {error}")


# if __name__ == "__main__":
#   service = get_gmail_service()
#   fetch_latest_emails(service, count=1)
#   apply_label_to_email(service, None, "19dafc8eb1d6034a", "testing_label")
