import pandas as pd

# Load the CSV
df = pd.read_csv("/home/maja/HOI/streamlit/userstudy/balanced_user_study_sample_500_unique_gt.csv")

# Define the columns to check for duplicates
dup_columns = [
    "gt_verb",
    "gt_object",
    "gt_verb_synset",
    "gt_object_synset",
    "pred_verb_synset",
    "pred_object_synset"
]

# Find duplicates
duplicates = df[df.duplicated(subset=dup_columns, keep=False)]

# Print result
if not duplicates.empty:
    print(f"Found {len(duplicates)} duplicated rows based on {dup_columns}")
    print(duplicates)
else:
    print("No duplicates found based on specified columns.")
