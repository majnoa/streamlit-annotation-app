import pandas as pd
from collections import defaultdict

# --- FILE PATHS ---
GT_PATH = "sampled_hoi_gt_500.csv"
OBJ_MAP_PATH = "hico_objects_with_synsets.csv"      # save your object mapping here
VERB_MAP_PATH = "matched_verb_synsets_hico_annotated.csv"       # save your verb mapping here
OUTPUT_PATH = "sampled_hoi_gt_500_with_synsets.csv"

# --- Load GT ---
gt_df = pd.read_csv(GT_PATH)

# --- Load Mappings ---
obj_df = pd.read_csv(OBJ_MAP_PATH)  # columns: Object, Synset
verb_df = pd.read_csv(VERB_MAP_PATH)  # columns: original_verb, lemmatized, synset

# --- Build mapping dictionaries ---
object_to_synset = defaultdict(set)
for _, row in obj_df.iterrows():
    object_to_synset[row["Object"].strip()].add(row["Synset"].strip())

verb_to_synset = defaultdict(set)
for _, row in verb_df.iterrows():
    verb_to_synset[row["original_verb"].strip()].add(row["synset"].strip())

# --- Attach Synsets ---
verb_synsets = []
object_synsets = []
missing_verb, missing_obj = set(), set()
multi_verb, multi_obj = set(), set()

for _, row in gt_df.iterrows():
    verb = row["verb"].strip()
    obj = row["object"].strip()

    vset = verb_to_synset.get(verb, set())
    oset = object_to_synset.get(obj, set())

    # Verb synset
    if len(vset) == 0:
        verb_synsets.append(None)
        missing_verb.add(verb)
    elif len(vset) > 1:
        multi_verb.add(verb)
        verb_synsets.append(sorted(vset)[0])  # pick consistent default
    else:
        verb_synsets.append(next(iter(vset)))

    # Object synset
    if len(oset) == 0:
        object_synsets.append(None)
        missing_obj.add(obj)
    elif len(oset) > 1:
        multi_obj.add(obj)
        object_synsets.append(sorted(oset)[0])
    else:
        object_synsets.append(next(iter(oset)))

gt_df["verb_synset"] = verb_synsets
gt_df["object_synset"] = object_synsets

# --- Report problems ---
print(f"✅ Extended GT with synsets. Saving to {OUTPUT_PATH}")
print(f"❌ Missing verb mappings: {sorted(missing_verb)}")
print(f"❌ Missing object mappings: {sorted(missing_obj)}")
print(f"⚠️ Multiple synsets for verbs: {sorted(multi_verb)}")
print(f"⚠️ Multiple synsets for objects: {sorted(multi_obj)}")

# --- Save ---
gt_df.to_csv(OUTPUT_PATH, index=False)
