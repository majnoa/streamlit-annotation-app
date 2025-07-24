import pandas as pd
import random
from collections import defaultdict

# --- Config ---
INPUT_FILE = "balanced_user_study_sample_500_unique_gt.csv"
VERB_SIM_FILE = "/home/maja/HOI/predictionsverb/merged_verb_scores_finalscore.csv"
OBJ_SIM_FILE = "/home/maja/HOI/predictionsobject/merged_object_scores_finalscore.csv"
OUTPUT_FILE = "balanced_user_study_nodup_final.csv"

# --- Load ---
df = pd.read_csv(INPUT_FILE)

verb_sim_df = pd.read_csv(VERB_SIM_FILE)
obj_sim_df = pd.read_csv(OBJ_SIM_FILE)

# --- Create lookup for replacements ---
def build_sim_lookup(df, label):
    lookup = defaultdict(lambda: defaultdict(list))
    for _, row in df.iterrows():
        s1, s2 = row["synset_1"], row["synset_2"]
        score = row["majority_score"]
        if pd.notna(score):
            sim = int(score)
            lookup[s1][sim].append(s2)
            lookup[s2][sim].append(s1)  # symmetric
    return lookup

verb_sim_lookup = build_sim_lookup(verb_sim_df, "verb")
obj_sim_lookup = build_sim_lookup(obj_sim_df, "object")

# --- Uniqueness check ---
def row_signature(row):
    return (
        row["gt_verb"], row["gt_object"],
        row["gt_verb_synset"], row["gt_object_synset"],
        row["pred_verb_synset"], row["pred_object_synset"]
    )

seen = set()
duplicates = []

for idx, row in df.iterrows():
    sig = row_signature(row)
    if sig in seen:
        duplicates.append(idx)
    else:
        seen.add(sig)

print(f"🔍 Found {len(duplicates)} duplicates to replace")

# --- Replace duplicates using external similarity source ---
replaced = 0
used_signatures = set(seen)  # to track new uniqueness

for idx in duplicates:
    row = df.loc[idx]
    cat = row["category"]
    level = row["similarity_level"]
    gt_verb, gt_obj = row["gt_verb_synset"], row["gt_object_synset"]

    new_row = None

    if cat == 1:
        # same verb, new object
        candidates = obj_sim_lookup[gt_obj][level]
        random.shuffle(candidates)
        for obj_pred in candidates:
            sig = row_signature({**row, "pred_object_synset": obj_pred})
            if sig not in used_signatures:
                new_row = row.copy()
                new_row["pred_object_synset"] = obj_pred
                used_signatures.add(sig)
                break

    elif cat == 2:
        # same object, new verb
        candidates = verb_sim_lookup[gt_verb][level]
        random.shuffle(candidates)
        for verb_pred in candidates:
            sig = row_signature({**row, "pred_verb_synset": verb_pred})
            if sig not in used_signatures:
                new_row = row.copy()
                new_row["pred_verb_synset"] = verb_pred
                used_signatures.add(sig)
                break

    elif cat == 3:
        # new verb and object
        v_cands = verb_sim_lookup[gt_verb][level]
        o_cands = obj_sim_lookup[gt_obj][level]
        random.shuffle(v_cands)
        random.shuffle(o_cands)

        for v in v_cands:
            for o in o_cands:
                sig = row_signature({**row, "pred_verb_synset": v, "pred_object_synset": o})
                if sig not in used_signatures:
                    new_row = row.copy()
                    new_row["pred_verb_synset"] = v
                    new_row["pred_object_synset"] = o
                    used_signatures.add(sig)
                    break
            if new_row is not None:
                break

    if new_row is not None:
        df.loc[idx] = new_row
        replaced += 1
    else:
        print(f"⚠️ Could not find replacement for row {idx} in bin (cat={cat}, sim={level})")

print(f"✅ Replaced {replaced}/{len(duplicates)} duplicates")

# --- Save ---
df.to_csv(OUTPUT_FILE, index=False)
print(f"📁 Final deduplicated file saved to: {OUTPUT_FILE}")
