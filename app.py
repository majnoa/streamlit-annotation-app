import streamlit as st
import json
import os

# --- Config ---
QUESTIONS_PER_PAGE = 10
QUESTIONS_FILE = "questions.json"
RESPONSES_DIR = "responses/responses_in_progress"
SUBMITTED_DIR = "responses/responses_submitted"


os.makedirs(RESPONSES_DIR, exist_ok=True)
os.makedirs(SUBMITTED_DIR, exist_ok=True)

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
    st.info("Valid IDs are: " + ", ".join(sorted(ALLOWED_ANNOTATORS)))
    st.stop()

response_file = os.path.join(RESPONSES_DIR, f"{annotator_id}.json")

# --- Load Previous Responses ---
if os.path.exists(response_file):
    with open(response_file, "r", encoding="utf-8") as f:
        responses = json.load(f)
else:
    responses = {}

# --- Determine first unanswered page ---
def find_first_unanswered_page():
    for idx, q in enumerate(questions):
        if str(q["id"]) not in responses:
            return idx // QUESTIONS_PER_PAGE + 1
    return 1

if "page" not in st.session_state:
    st.session_state.page = find_first_unanswered_page()

# --- Page Navigation ---
page = st.number_input(
    f"Page (1 to {total_pages})",
    min_value=1,
    max_value=total_pages,
    value=st.session_state.page,
    step=1,
    key="page"
)

start_idx = (page - 1) * QUESTIONS_PER_PAGE
end_idx = min(start_idx + QUESTIONS_PER_PAGE, len(questions))

# --- Submission tracking ---
submitted_file = os.path.join(SUBMITTED_DIR, f"{annotator_id}_pg{page}.json")
page_submitted = os.path.exists(submitted_file)

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
                f'<div style="background-color:#6892A4;padding:10px;border-radius:5px">'
                f"{q['question']}</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(q["question"], unsafe_allow_html=True)


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

# --- Save Responses ---
if updated:
    with open(response_file, "w", encoding="utf-8") as f:
        json.dump(responses, f, indent=2)
    st.success("Progress saved automatically.")

# --- Submit Page ---
if all_answered and not page_submitted:
    if st.button("✅ Submit This Page"):
        page_data = {
            str(q["id"]): responses[str(q["id"])]
            for q in questions[start_idx:end_idx]
        }
        with open(submitted_file, "w", encoding="utf-8") as f:
            json.dump(page_data, f, indent=2)
        st.success(f"Page {page} submitted and locked.")
        st.rerun()
elif page_submitted:
    st.info("✅ This page has been submitted and cannot be changed.")
