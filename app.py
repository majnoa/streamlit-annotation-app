import streamlit as st
import json
import os

# --- Config ---
QUESTIONS_PER_PAGE = 5
QUESTIONS_FILE = "questions.json"
RESPONSES_DIR = "responses"

os.makedirs(RESPONSES_DIR, exist_ok=True)

# --- Load Questions ---
with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
    questions = json.load(f)

total_pages = (len(questions) - 1) // QUESTIONS_PER_PAGE + 1

# --- Annotator Login ---
st.title("Annotation Task")
annotator_id = st.text_input("Enter your name or ID:")

if not annotator_id:
    st.warning("Please enter your ID to begin.")
    st.stop()

response_file = os.path.join(RESPONSES_DIR, f"{annotator_id}.json")

# --- Load Previous Responses ---
if os.path.exists(response_file):
    with open(response_file, "r", encoding="utf-8") as f:
        responses = json.load(f)
else:
    responses = {}

# --- Page Navigation ---
page = st.number_input(
    f"Page (1 to {total_pages})", min_value=1, max_value=total_pages, value=1, step=1
)

start_idx = (page - 1) * QUESTIONS_PER_PAGE
end_idx = min(start_idx + QUESTIONS_PER_PAGE, len(questions))

# --- Question Loop ---
updated = False
for q in questions[start_idx:end_idx]:
    qid = str(q["id"])
    st.markdown(f"**Q{qid}: {q['question']}**")
    choice = st.radio(
        f"Select an answer for Q{qid}",
        options=q["choices"],
        index=q["choices"].index(responses[qid]) if qid in responses else 0,
        key=f"q_{qid}"
    )
    if responses.get(qid) != choice:
        responses[qid] = choice
        updated = True
    st.markdown("---")

# --- Save Responses ---
if updated:
    with open(response_file, "w", encoding="utf-8") as f:
        json.dump(responses, f, indent=2)

st.success("Progress saved automatically.")
