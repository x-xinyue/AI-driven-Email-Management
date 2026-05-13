import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


SCOPES = ["https://www.googleapis.com/auth/spreadsheets", 
          "https://www.googleapis.com/auth/gmail.modify"]


def get_spreadsheet_service():
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
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

  return build("sheets", "v4", credentials=creds)


def normalize(text):
   return text.strip().lower() if text else ""


def find_existing_job_entry(rows, company_name, job_role):
    """
    Searches the Google Sheet for an existing entry with the given job title.
    Returns the row number if found, otherwise returns None.
    """
    target_company = normalize(company_name)
    target_role = normalize(job_role)

    for i, row in enumerate(rows):
        if len(row) < 2:
            continue 
        # Checking Column A (Position) and Column B (Company)
        if normalize(row[0]) == target_role and normalize(row[1]) == target_company:
            return i + 1  # +1 because Google Sheets rows are 1-indexed
            
    return None


def append_row(service, spreadsheet_id, range_name, row_values):
    """
    Appends a row of values to the specified Google Sheet.
    """
    try:
        sheet = service.spreadsheets()
        body = {"values": [row_values]}
        result = (
            sheet.values()
            .append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body=body
            ).execute()
        )
        print(f"{result.get('updates').get('updatedCells')} cells appended.")
    except HttpError as err:
        print(f"An error occurred: {err}")


def update_stage_logic(service, spreadsheet_id, sheet_name, row_num, action):
    """
    Updates specific cells in an existing row using dictionary access.
    """
    status = action.get('status_update', "Applied")
    if status:
        status = str(status).strip().title()
    
    data = [
        {"range": f"{sheet_name}!O{row_num}", "values": [[status]]},
        {"range": f"{sheet_name}!Q{row_num}", "values": [[action.get('reason', '')]]},
        {"range": f"{sheet_name}!S{row_num}", "values": [[status]]}
    ]
    
    body = {"valueInputOption": "USER_ENTERED", "data": data}
    
    service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()


def upsert_job_entry(service, spreadsheet_id, sheet_name, action):
    """
    Upserts a job entry in the Google Sheet.
    If an entry with the same job title exists, it updates that row; otherwise, it appends a new row.
    """
    # Fetch current data
    range_to_check = f"{sheet_name}!A:U"
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_to_check).execute()
    rows = result.get("values", [])

    # Search for existing entry
    existing_row_num = find_existing_job_entry(rows, action['company'], action['position'])

    if existing_row_num:
        print(f"Match: {action['company']} found at Row {existing_row_num}. Updating status.")
        # Update O (14), Q (16), and S (18)
        update_stage_logic(service, spreadsheet_id, sheet_name, existing_row_num, action)
    
    else:
        print(f"No match: Appending {action['company']} as a new entry.")
        new_row = [""] * 21
        new_row[0] = action['position']         # Col A: Position
        new_row[1] = action['company']          # Col B: Company
        new_row[2] = action.get('industry')     # Col C: is Industry
        new_row[4] = action.get('location')     # Col E: is Location
        new_row[6] = action.get('date_applied') # Col G: is Date Applied
        new_row[14] = action['status_update']   # Col O: Status
        new_row[16] = action['reason'][:200]    # Col Q: Latest word
        
        append_row(service, spreadsheet_id, f"{sheet_name}!A1", new_row)
