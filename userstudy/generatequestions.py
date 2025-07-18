import pandas as pd
import json
from nltk.corpus import wordnet as wn
from tqdm import tqdm

# --- Config ---
INPUT_CSV = "balanced_user_study_sample_500_unique_gt.csv"
OUTPUT_JSON = "/home/maja/HOI/streamlit/questions.json"

# --- Load Sample ---
df = pd.read_csv(INPUT_CSV)

# --- Helper to get synset gloss ---
def get_gloss(synset_name):
    try:
        return wn.synset(synset_name).definition()
    except:
        return "[Definition not found]"

# --- Generate questions ---
questions = []

for i, row in tqdm(df.iterrows(), total=len(df)):
    verb_gt = row["gt_verb"]
    obj_gt = row["gt_object"]
    verb_pred = row["pred_verb_synset"]
    obj_pred = row["pred_object_synset"]

    gt_verb_syn = row["gt_verb_synset"]
    gt_obj_syn = row["gt_object_synset"]

    question_text = (
        f"Please compare the following labels:<br><br>"
        f"<span style='font-weight:bold; color:#D6455C;'>  {verb_gt} {obj_gt} (ground truth) ↔ "
        f"{verb_pred.split('.')[0]} {obj_pred.split('.')[0]} (prediction)</span><br><br>"
        f"→ Definition {gt_obj_syn}: {get_gloss(gt_obj_syn)}<br>"
        f"→ Definition {gt_verb_syn}: {get_gloss(gt_verb_syn)}<br>"
        f"→ Definition {obj_pred}: {get_gloss(obj_pred)}<br>"
        f"→ Definition {verb_pred}: {get_gloss(verb_pred)}<br><br>"
        f"How similar is the prediction to the ground truth?<br>"
        f"The prediction describes ..."
    )

    questions.append({
        "id": i + 1,
        "question": question_text,
        "choices": ["0 = ... a completly dissimilar interaction", "1 = ... a somewhat related but clearly distinct interaction", "2 = ... a related interaction but it is easily distinguishable", "3 = ... a very similar interaction with subtle differences", "4 = ... an interaction that you would use interchangeably or synonymous with the ground truth"],
    })

# --- Save to JSON ---
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(questions, f, indent=2, ensure_ascii=False)

print(f"✅ Saved {len(questions)} questions to {OUTPUT_JSON}")
