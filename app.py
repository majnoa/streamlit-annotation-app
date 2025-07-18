import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import pandas as pd
import json

# --- Load questions ---
QUESTIONS_FILE = "questions.json"
QUESTIONS_PER_PAGE = 10

with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
    questions = json.load(f)

total_pages = (len(questions) - 1) // QUESTIONS_PER_PAGE + 1

# --- Connect to Google Sheets ---
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read()

# --- Ensure expected columns exist ---
EXPECTED_COLUMNS = ["timestamp", "annotator_id", "page", "question_id", "answer"]
if df.empty:
    df = pd.DataFrame(columns=EXPECTED_COLUMNS)
else:
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = ""

# --- UI Setup ---
st.title("📝 Annotation Task")

# --- Annotator Login ---
annotator_id = st.text_input("Enter your annotator ID:")
if not annotator_id:
    st.stop()

# --- Page number state ---
if "page" not in st.session_state:
    st.session_state.page = 1

st.number_input(
    f"Select page (1 to {total_pages})",
    min_value=1,
    max_value=total_pages,
    step=1,
    key="page"
)

current_page = st.session_state.page
start = (current_page - 1) * QUESTIONS_PER_PAGE
end = min(start + QUESTIONS_PER_PAGE, len(questions))

# --- Display questions for the current page ---
st.subheader(f"🔍 Questions – Page {current_page}")
responses = {}

for q in questions[start:end]:
    qid = str(q["id"])
    st.markdown(f"**Q{qid}**", unsafe_allow_html=True)
    st.markdown(q["question"], unsafe_allow_html=True)
    selected = st.radio(f"Answer for Q{qid}:", q["choices"], key=f"q_{qid}")
    responses[qid] = selected
    st.markdown("---")

# --- Submit answers ---
if st.button("✅ Submit This Page"):
    now = datetime.utcnow().isoformat()
    new_rows = [
        {
            "timestamp": now,
            "annotator_id": annotator_id,
            "page": current_page,
            "question_id": qid,
            "answer": answer
        }
        for qid, answer in responses.items()
    ]

    updated_df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)[EXPECTED_COLUMNS]

    try:
        conn.update(data=updated_df)
        st.success(f"✅ Page {current_page} submitted!")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Failed to update sheet: {e}")
