import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime

st.title("✅ Google Sheets Test")

try:
    creds_dict = json.loads(st.secrets["gspread"]["gcp_service_account"])
    spreadsheet_id = st.secrets["gspread"]["spreadsheet_id"]
    worksheet_name = st.secrets["gspread"]["worksheet_name"]

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    worksheet = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)

    # Append test row
    now = datetime.utcnow().isoformat()
    test_row = [now, "TEST_USER", 0, "9999", "✅ test ok"]
    worksheet.append_row(test_row)
    st.success("Appended test row!")

    # Show all rows
    data = worksheet.get_all_records()
    st.write("📋 Current Sheet Content:")
    st.write(data)

except Exception as e:
    st.error(f"❌ Error: {e}")
