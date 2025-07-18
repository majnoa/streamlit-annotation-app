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
df = conn.read(worksheet="sheet1")  # In-progress data
submitted_df = conn.read(worksheet="submissions")  # Final submitted pages

# --- Ensure expected columns exist ---
EXPECTED_COLUMNS = ["timestamp", "annotator_id", "page", "question_id", "answer"]
for dframe in [df, submitted_df]:
    for col in EXPECTED_COLUMNS:
        if col not in dframe.columns:
            dframe[col] = ""

# --- Normalize column types ---
submitted_df["annotator_id"] = submitted_df["annotator_id"].astype(str).str.strip().str.lower()
submitted_df["page"] = submitted_df["page"].astype(str)

# --- Annotator login ---
st.title("📝 Annotation Task")
annotator_id = st.text_input("Enter your annotator ID:")
ALLOWED_ANNOTATORS = {"Hawk", "Joey", "Maja", "AJ", "Qianqian", "Student1"}

if not annotator_id:
    st.warning("Please enter your ID to begin.")
    st.stop()

if annotator_id not in ALLOWED_ANNOTATORS:
    st.error(f"❌ '{annotator_id}' is not a valid annotator ID.")
    st.info("Valid IDs are: " + ", ".join(sorted(ALLOWED_ANNOTATORS)))
    st.stop()

normalized_id = annotator_id.strip().lower()

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

# --- Function to check if page is already submitted ---
def is_page_submitted(submitted_df, annotator_id, page):
    return any(
        row["annotator_id"] == annotator_id and row["page"] == str(page)
        for _, row in submitted_df.iterrows()
    )

already_submitted = is_page_submitted(submitted_df, normalized_id, current_page)

st.subheader(f"🔍 Questions – Page {current_page}")
responses = {}
all_answered = True  # Track if all questions are answered

# --- Display questions ---
for q in questions[start:end]:
    qid = str(q["id"])
    st.markdown(f"**Q{qid}**", unsafe_allow_html=True)
    st.markdown(q["question"], unsafe_allow_html=True)

    key = f"q_{qid}"
    saved = df[
        (df["annotator_id"] == annotator_id) & 
        (df["question_id"] == qid)
    ]
    default = saved["answer"].values[0] if not saved.empty else None

    # Prepare choices with a default placeholder
    choices = ["⬜ Please select an answer"] + q["choices"]
    if default in q["choices"]:
        index = q["choices"].index(default) + 1
    else:
        index = 0

    selected = st.radio(
        f"Answer for Q{qid}:",
        choices,
        key=key,
        index=index,
        disabled=already_submitted
    )

    if selected == "⬜ Please select an answer":
        all_answered = False
    else:
        responses[qid] = selected

    st.markdown("---")

# --- Save if submit clicked ---
if st.button("✅ Submit This Page") and not already_submitted:
    if not all_answered:
        st.warning("⚠️ Please answer all questions before submitting.")
    else:
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

        try:
            updated_df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)[EXPECTED_COLUMNS]
            conn.update(data=updated_df, worksheet="sheet1")

            updated_submissions = pd.concat([submitted_df, pd.DataFrame(new_rows)], ignore_index=True)[EXPECTED_COLUMNS]
            conn.update(data=updated_submissions, worksheet="submissions")

            submitted_df = conn.read(worksheet="submissions")
            submitted_df["annotator_id"] = submitted_df["annotator_id"].astype(str).str.strip().str.lower()
            submitted_df["page"] = submitted_df["page"].astype(str)
            already_submitted = is_page_submitted(submitted_df, normalized_id, current_page)

            st.success(f"✅ Page {current_page} submitted and finalized.")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to update sheets: {e}")
elif already_submitted:
    st.info("✅ This page has already been submitted and is locked.")
