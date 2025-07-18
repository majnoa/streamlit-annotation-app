import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.title("✅ Native Streamlit Google Sheets Write Example")

# Connect to GSheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Read current data
df = conn.read()

# Append a row
new_row = {
    "timestamp": datetime.utcnow().isoformat(),
    "status": "✅ Success!",
    "note": "Streamlit wrote this!"
}
df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

# Write back
conn.update(df)

st.success("Row written and saved!")

# Show contents
st.dataframe(df)
