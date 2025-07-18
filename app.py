import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime

st.title("✅ Google Sheets Write Test")

try:
    # Load credentials from Streamlit secrets
    creds_dict = json.loads(st.secrets["gspread"]["gcp_service_account"])
    spreadsheet_id = st.secrets["gspread"]["spreadsheet_id"]
    worksheet_name = st.secrets["gspread"]["worksheet_name"]

    # Auth
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    # Open sheet
    worksheet = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)

    # Append test row
    now = datetime.utcnow().isoformat()
    test_row = [now, "✅ Success!", "Streamlit wrote this"]
    worksheet.append_row(test_row)

    st.success("Row successfully written to Google Sheet!")

    # Optional: show sheet contents
    st.write("📄 Current Sheet Contents:")
    st.write(worksheet.get_all_records())

except Exception as e:
    st.error(f"❌ Error: {e}")
