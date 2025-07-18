import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pandas as pd

# --- Connect to the Google Sheet ---
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read()

st.title("📝 Annotation Logger")

# --- Ensure expected columns exist ---
EXPECTED_COLUMNS = ["timestamp", "annotator_id", "page", "question_id", "answer"]
if df.empty:
    df = pd.DataFrame(columns=EXPECTED_COLUMNS)
else:
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = ""

# --- Show sheet contents ---
st.subheader("📄 Current Sheet Contents")
st.dataframe(df)

# --- Input form ---
st.subheader("➕ Add New Annotation")
with st.form("annotation_form"):
    annotator_id = st.text_input("Annotator ID")
    page = st.number_input("Page Number", min_value=0, step=1)
    question_id = st.text_input("Question ID")
    answer = st.selectbox("Answer", ["0", "1", "2", "3", "4"])
    submitted = st.form_submit_button("Submit")

# --- On submission ---
if submitted:
    new_row = pd.DataFrame([{
        "timestamp": datetime.utcnow().isoformat(),
        "annotator_id": annotator_id,
        "page": page,
        "question_id": question_id,
        "answer": answer
    }])

    updated_df = pd.concat([df, new_row], ignore_index=True)[EXPECTED_COLUMNS]

    try:
        conn.update(data=updated_df)
        st.success("✅ Annotation submitted!")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Failed to update sheet: {e}")
