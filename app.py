import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.title("✅ Google Sheets Write Test")

try:
    # Load credentials directly from Streamlit secrets (flat dict)
    creds_dict = {
        "type": st.secrets["gspread"]["type"],
        "project_id": st.secrets["gspread"]["project_id"],
        "private_key_id": st.secrets["gspread"]["private_key_id"],
        "private_key": st.secrets["gspread"]["private_key"],
        "client_email": st.secrets["gspread"]["client_email"],
        "client_id": st.secrets["gspread"]["client_id"],
        "auth_uri": st.secrets["gspread"]["auth_uri"],
        "token_uri": st.secrets["gspread"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gspread"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gspread"]["client_x509_cert_url"],
        "universe_domain": st.secrets["gspread"]["universe_domain"],
    }
    spreadsheet_id = st.secrets["gspread"]["spreadsheet_id"]
    worksheet_name = st.secrets["gspread"]["worksheet_name"]

    # Auth
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
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
