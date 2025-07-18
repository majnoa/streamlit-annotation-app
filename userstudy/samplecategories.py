import pandas as pd
import random
from collections import defaultdict, Counter

# --- Config ---
INPUT_FILE = "gt_predictions_3categories_500_including0_2.csv"
OUTPUT_FILE = "balanced_user_study_sample_500_unique_gt.csv"
TARGET_TOTAL = 500
CATEGORIES = [1, 2, 3]
SIM_LEVELS = [1, 2, 3, 4]
TARGET_PER_BIN = TARGET_TOTAL // (len(CATEGORIES) * len(SIM_LEVELS))  # ≈ 41–42

# --- Load Data ---
df = pd.read_csv(INPUT_FILE)
df["bin"] = list(zip(df["category"], df["similarity_level"]))

# --- Initialize Bins ---
bins = defaultdict(list)
for _, row in df.iterrows():
    bins[(row["category"], row["similarity_level"])].append(row)

# --- Shuffle all bins ---
for k in bins:
    random.shuffle(bins[k])

# --- Bin size stats ---
bin_sizes = pd.Series({k: len(v) for k, v in bins.items()})
print("📉 Bin sizes (before uniqueness filtering):")
print(bin_sizes.sort_values())

# --- Sampled Tracker ---
final = []
used_gts = set()
fallback_counts = defaultdict(int)

def get_gt_key(row):
    return (row["image_id"], row["gt_verb_synset"], row["gt_object_synset"])

# --- Helper to pick from bin with unique GT ---
def pick_unique(b, used_gts, n):
    selected = []
    for row in b:
        gt_key = get_gt_key(row)
        if gt_key not in used_gts:
            selected.append(row)
            used_gts.add(gt_key)
        if len(selected) == n:
            break
    return selected

# --- Pass 1: Try to sample target per bin ---
for cat in CATEGORIES:
    for sim in SIM_LEVELS:
        key = (cat, sim)
        picked = pick_unique(bins[key], used_gts, TARGET_PER_BIN)
        final.extend(picked)

# --- Pass 2: Fill remaining (up to 500) from any bin ---
previous_len = -1
max_tries = 5
tries = 0

while len(final) < TARGET_TOTAL and tries < max_tries:
    made_progress = False
    for cat in CATEGORIES:
        for sim in SIM_LEVELS:
            key = (cat, sim)
            if len(final) >= TARGET_TOTAL:
                break
            for row in bins[key]:
                gt_key = get_gt_key(row)
                if gt_key not in used_gts:
                    final.append(row)
                    used_gts.add(gt_key)
                    fallback_counts[key] += 1
                    made_progress = True
                    break  # pick only 1 at a time
    if not made_progress:
        tries += 1
        print(f"⚠️  No new samples added in pass {tries}. Retrying fallback...")
    else:
        tries = 0  # reset

# --- Output ---
out_df = pd.DataFrame(final)
out_df.to_csv(OUTPUT_FILE, index=False)
print(f"\n✅ Saved balanced sample file to {OUTPUT_FILE} with {len(out_df)} rows")

# --- Stats ---
print("\n📊 Final Category Distribution:")
print(out_df["category"].value_counts().sort_index())

print("\n📊 Final Similarity Level Distribution:")
print(out_df["similarity_level"].value_counts().sort_index())

print("\n📊 Final (Category, Similarity) Bin Counts:")
print(out_df.groupby(["category", "similarity_level"]).size())

print("\n⚠️ Fallbacks Used (beyond target per bin):")
for k, v in sorted(fallback_counts.items()):
    print(f"  Bin {k}: +{v}")

if len(out_df) < TARGET_TOTAL:
    print(f"\n⚠️ Only collected {len(out_df)} unique predictions — some bins were too sparse.")
