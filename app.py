import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

st.title("✅ Google Sheets Write Test")

try:
    # Use flat credentials from secrets
    gspread_secrets = st.secrets["gspread"]
    creds_dict = {
        "type": gspread_secrets["type"],
        "project_id": gspread_secrets["project_id"],
        "private_key_id": gspread_secrets["private_key_id"],
        "private_key": gspread_secrets["private_key"],
        "client_email": gspread_secrets["client_email"],
        "client_id": gspread_secrets["client_id"],
        "auth_uri": gspread_secrets["auth_uri"],
        "token_uri": gspread_secrets["token_uri"],
        "auth_provider_x509_cert_url": gspread_secrets["auth_provider_x509_cert_url"],
        "client_x509_cert_url": gspread_secrets["client_x509_cert_url"],
    }

    # Create credentials
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)

    # Authorize and connect
    client = gspread.authorize(credentials)
    worksheet = client.open_by_key(gspread_secrets["spreadsheet_id"]).worksheet(gspread_secrets["worksheet_name"])

    # Append test row
    now = datetime.utcnow().isoformat()
    worksheet.append_row([now, "✅ Success!", "Streamlit wrote this"])

    st.success("Row successfully written to Google Sheet!")
    st.write("📄 Current Sheet Contents:")
    st.write(worksheet.get_all_records())

except Exception as e:
    st.error(f"❌ Error: {e}")
