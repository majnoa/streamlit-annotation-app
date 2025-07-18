import streamlit as st
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- Google Sheets: Load + Save ---
def load_responses_from_sheet(annotator_id: str) -> dict:
    creds_dict = json.loads(st.secrets["gspread"]["gcp_service_account"])
    spreadsheet_id = st.secrets["gspread"]["spreadsheet_id"]
    worksheet_name = st.secrets["gspread"]["worksheet_name"]

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    worksheet = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)

    responses = {}
    all_rows = worksheet.get_all_records()
    for row in all_rows:
        if row["annotator_id"] == annotator_id:
            responses[str(row["question_id"])] = row["answer"]
    return responses

def page_already_submitted(annotator_id: str, page: int, total_questions: int) -> bool:
    creds_dict = json.loads(st.secrets["gspread"]["gcp_service_account"])
    spreadsheet_id = st.secrets["gspread"]["spreadsheet_id"]
    worksheet_name = st.secrets["gspread"]["worksheet_name"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    worksheet = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)
    all_rows = worksheet.get_all_records()
    count = sum(1 for row in all_rows if row["annotator_id"] == annotator_id and row["page"] == page)
    return count >= total_questions

def save_to_gsheet(responses: dict, annotator_id: str, page: int):
    creds_dict = json.loads(st.secrets["gspread"]["gcp_service_account"])
    spreadsheet_id = st.secrets["gspread"]["spreadsheet_id"]
    worksheet_name = st.secrets["gspread"]["worksheet_name"]

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    worksheet = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)

    now = datetime.utcnow().isoformat()
    for qid, answer in responses.items():
        worksheet.append_row([now, annotator_id, page, qid, answer])

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

responses = load_responses_from_sheet(annotator_id)

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

page_submitted = page_already_submitted(annotator_id, page, QUESTIONS_PER_PAGE)

# --- Question Loop ---
updated = False
all_answered = True

for q in questions[start_idx:end_idx]:
    qid = str(q["id"])
    saved_choice = responses.get(qid, None)
    choices = q["choices"]

    if saved_choice in choices:
        display_choices = choices
        default_index = choices.index(saved_choice)
    else:
        display_choices = ["⬜ Please select an answer"] + choices
        default_index = 0

    unanswered = saved_choice is None
    all_answered &= not unanswered

    with st.container():
        if unanswered:
            st.markdown(
                f'<div style="background-color:#3E3E3D;padding:10px;border-radius:5px">'
                f"<strong>Q{qid}:</strong> {q['question']}</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(f"**Q{qid}: {q['question']}**")

        selected = st.radio(
            f"Select an answer for Q{qid}",
            options=display_choices,
            index=default_index,
            key=f"{annotator_id}_q_{qid}",
            disabled=page_submitted
        )

        if not page_submitted and selected != "⬜ Please select an answer":
            if responses.get(qid) != selected:
                responses[qid] = selected
                updated = True

    st.markdown("---")

# --- Submit Page ---
if all_answered and not page_submitted:
    if st.button("✅ Submit This Page"):
        page_data = {
            str(q["id"]): responses[str(q["id"])]
            for q in questions[start_idx:end_idx]
        }
        try:
            save_to_gsheet(page_data, annotator_id, page)
            st.success(f"✅ Page {page} submitted and saved to Google Sheets.")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to save to Google Sheets: {e}")
elif page_submitted:
    st.info("✅ This page has been submitted and cannot be changed.")