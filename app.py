import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pandas as pd
import json

# --- Load questions ---
QUESTIONS_FILE = "questions.json"
with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
    questions = json.load(f)

# --- Connect to Google Sheets ---
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read()

st.title("📝 Annotation Task")

# --- Ensure expected columns exist ---
EXPECTED_COLUMNS = ["timestamp", "annotator_id", "page", "question_id", "answer"]
if df.empty:
    df = pd.DataFrame(columns=EXPECTED_COLUMNS)
else:
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = ""

# --- Annotator login ---
annotator_id = st.text_input("Enter your annotator ID:")
if not annotator_id:
    st.stop()

page = 1  # Fixed page for now

# --- Render questions ---
st.subheader("🔍 Questions")
responses = {}
for q in questions:
    qid = str(q["id"])
    st.markdown(f"**Q{qid}**", unsafe_allow_html=True)
    st.markdown(q["question"], unsafe_allow_html=True)
    selected = st.radio(f"Answer for Q{qid}:", q["choices"], key=f"q_{qid}")
    responses[qid] = selected
    st.markdown("---")

# --- Submit answers ---
if st.button("✅ Submit"):
    new_rows = []
    now = datetime.utcnow().isoformat()
    for qid, answer in responses.items():
        new_rows.append({
            "timestamp": now,
            "annotator_id": annotator_id,
            "page": page,
            "question_id": qid,
            "answer": answer
        })
    updated_df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)[EXPECTED_COLUMNS]
    try:
        conn.update(data=updated_df)
        st.success("✅ Responses submitted and saved to Google Sheets!")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Failed to update sheet: {e}")
