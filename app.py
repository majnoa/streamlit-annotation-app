import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pandas as pd

# Connect to the Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read()

st.title("📋 Sheet Contents")

# Show the current contents
if df.empty:
    st.info("The sheet is currently empty.")
else:
    st.dataframe(df)

# Add a new row
if st.button("➕ Add Row"):
    now = datetime.utcnow().isoformat()
    new_row = pd.DataFrame([{
        "timestamp": now,
        "status": "✅ Success!",
        "message": "Streamlit wrote this"
    }])
    updated_df = pd.concat([df, new_row], ignore_index=True)
    conn.update(updated_df)
    st.success("Row added!")
    st.rerun()
