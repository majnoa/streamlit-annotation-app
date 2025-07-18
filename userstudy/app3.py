import streamlit as st
import json
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- Google Sheets Helper ---
def load_responses_from_sheet(conn: GSheetsConnection, annotator_id: str) -> dict:
    responses = {}
    df = conn.read(worksheet=annotator_id)
    if df is None or df.empty:
        return responses
    for _, row in df.iterrows():
        responses[str(row["question_id"])] = row["answer"]
    return responses

def page_already_submitted(conn: GSheetsConnection, annotator_id: str, page: int, total_questions: int) -> bool:
    df = conn.read(worksheet=annotator_id)
    if df is None or df.empty:
        return False
    count = df[(df["page"] == page)].shape[0]
    return count >= total_questions

def save_final_submission(conn, responses: dict, annotator_id: str, page: int):
    now = datetime.utcnow().isoformat()
    new_rows = [
        {
            "timestamp": now,
            "annotator_id": annotator_id,
            "page": page,
            "question_id": qid,
            "answer": answer
        }
        for qid, answer in responses.items()
    ]
    
    try:
        existing_df = conn.read(worksheet=annotator_id)
        updated_df = pd.concat([existing_df, pd.DataFrame(new_rows)], ignore_index=True)
        conn.update(worksheet=annotator_id, data=updated_df)
        st.success("✅ Saved final submission.")
    except Exception as e:
        st.error(f"❌ Error saving to sheet for {annotator_id}: {e}")

def save_live_response(conn, annotator_id: str, page: int, qid: str, answer: str):
    now = datetime.utcnow().isoformat()
    new_row = {
        "timestamp": now,
        "annotator_id": annotator_id,
        "page": page,
        "question_id": qid,
        "answer": answer
    }

    try:
        sheet_df = conn.read(worksheet="sheet1")
        sheet_df = sheet_df if sheet_df is not None else pd.DataFrame(columns=new_row.keys())

        # Remove any previous response for this annotator/page/qid
        mask = ~(
            (sheet_df["annotator_id"] == annotator_id) &
            (sheet_df["page"] == page) &
            (sheet_df["question_id"] == qid)
        )
        sheet_df = sheet_df[mask]

        # Append new response and write back
        sheet_df = pd.concat([sheet_df, pd.DataFrame([new_row])], ignore_index=True)
        conn.update(worksheet="sheet1", data=sheet_df)
    except Exception as e:
        st.error(f"❌ Failed live save to sheet1: {e}")

# --- Config ---
QUESTIONS_PER_PAGE = 10
QUESTIONS_FILE = "questions.json"

# --- Load Questions ---
with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
    questions = json.load(f)

total_pages = (len(questions) - 1) // QUESTIONS_PER_PAGE + 1

# --- Annotator Login ---
st.title("Annotation Task")
ALLOWED_ANNOTATORS = {"Hawk", "Joey", "Maja", "AJ", "Qianqian", "Student1"}

annotator_id = st.text_input("Enter your name or ID:")

if not annotator_id:
    st.warning("Please enter your ID to begin.")
    st.stop()

if annotator_id not in ALLOWED_ANNOTATORS:
    st.error(f"❌ '{annotator_id}' is not a valid annotator ID.")
    st.stop()

# --- GSheets Connection ---
conn = st.connection("gsheets", type=GSheetsConnection)

responses = load_responses_from_sheet(conn, annotator_id)

# --- Determine first unanswered page ---
def find_first_unanswered_page():
    for idx, q in enumerate(questions):
        if str(q["id"]) not in responses:
            return idx // QUESTIONS_PER_PAGE + 1
    return 1

if "page" not in st.session_state:
    st.session_state.page = find_first_unanswered_page()

# --- Page Navigation ---
st.number_input(
    f"Page (1 to {total_pages})",
    min_value=1,
    max_value=total_pages,
    step=1,
    key="page"
)

page = st.session_state.page
start_idx = (page - 1) * QUESTIONS_PER_PAGE
end_idx = min(start_idx + QUESTIONS_PER_PAGE, len(questions))

page_submitted = page_already_submitted(conn, annotator_id, page, QUESTIONS_PER_PAGE)

# --- Question Loop ---
all_answered = True
page_data = {}

for q in questions[start_idx:end_idx]:
    qid = str(q["id"])
    choices = q["choices"]
    key = f"{annotator_id}_q_{qid}"

    saved_choice = responses.get(qid, None)
    default_index = choices.index(saved_choice) if saved_choice in choices else 0
    display_choices = ["⬜ Please select an answer"] + choices
    index = display_choices.index(saved_choice) if saved_choice in display_choices else 0

    selected = st.radio(
        f"Q{qid}: {q['question']}",
        options=display_choices,
        index=index,
        key=key,
        disabled=page_submitted
    )

    if selected == "⬜ Please select an answer":
        all_answered = False
    else:
        page_data[qid] = selected
        if not page_submitted and selected != saved_choice:
            save_live_response(conn, annotator_id, page, qid, selected)

    # Highlight unanswered
    if selected == "⬜ Please select an answer":
        st.markdown(
            f'<div style="background-color:#3E3E3D;padding:10px;border-radius:5px">Please answer this question</div>',
            unsafe_allow_html=True
        )

    st.markdown("---")

# --- Submit Page ---
if all_answered and not page_submitted:
    if st.button("✅ Submit This Page"):
        try:
            save_final_submission(conn, page_data, annotator_id, page)
            st.success(f"✅ Page {page} submitted and saved to {annotator_id}'s worksheet.")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to save final submission: {e}")
elif page_submitted:
    st.info("✅ This page has already been submitted and cannot be changed.")
