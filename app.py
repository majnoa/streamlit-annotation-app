import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import datetime

st.title("🧪 Google Sheets Debug Test")

def js_console_log(msg):
    # Forces message into browser console
    st.markdown(f"<script>console.log({json.dumps('[Streamlit Log] ' + msg)})</script>", unsafe_allow_html=True)

try:
    js_console_log("Loading secrets...")
    creds_dict = json.loads(st.secrets["gspread"]["gcp_service_account"])
    spreadsheet_id = st.secrets["gspread"]["spreadsheet_id"]
    worksheet_name = st.secrets["gspread"]["worksheet_name"]
    js_console_log("Secrets loaded and parsed successfully.")

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    js_console_log("Google client authorized.")

    worksheet = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)
    js_console_log(f"Worksheet '{worksheet_name}' opened.")

    # Append test row
    now = datetime.utcnow().isoformat()
    test_row = [now, "DEBUG_USER", 0, "9999", "✅ test ok"]
    worksheet.append_row(test_row)
    js_console_log("Test row appended.")

    # Show data
    data = worksheet.get_all_records()
    js_console_log(f"Fetched {len(data)} rows from sheet.")
    st.success("✅ All operations succeeded")
    st.write(data)

except Exception as e:
    js_console_log(f"❌ ERROR: {str(e)}")
    st.error(f"❌ Streamlit error: {e}")
