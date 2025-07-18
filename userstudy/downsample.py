import pandas as pd
import random
from collections import defaultdict, Counter

# --- Config ---
INPUT_FILE = "gt_predictions_3categories_500_including0_2.csv"
OUTPUT_FILE = "balanced_user_study_sample_500_2.csv"
TARGET_TOTAL = 500
CATEGORIES = [1, 2, 3]
SIM_LEVELS = [1, 2, 3, 4]
TARGET_PER_BIN = TARGET_TOTAL // (len(CATEGORIES) * len(SIM_LEVELS))  # ≈ 41–42

# --- Load Data ---
df = pd.read_csv(INPUT_FILE)
df["bin"] = list(zip(df["category"], df["similarity_level"]))

# --- Print duplicate image_id stats ---
id_counts = df["image_id"].value_counts()
duplicates = id_counts[id_counts > 1]

print(f"\n🧮 Total unique image_ids: {df['image_id'].nunique()}")
print(f"🧮 Total rows in input file: {len(df)}")
print(f"🔁 Number of image_ids with duplicates: {len(duplicates)}")
print(f"🔁 Top 10 most duplicated image_ids:")
print(duplicates.head(10))


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
used_ids = set()
fallback_counts = defaultdict(int)

# --- Helper to pick from bin with unique image_id ---
def pick_unique(b, used_ids, n):
    selected = []
    for row in b:
        if row["image_id"] not in used_ids:
            selected.append(row)
            used_ids.add(row["image_id"])
        if len(selected) == n:
            break
    return selected

# --- Pass 1: Try to sample target per bin ---
for cat in CATEGORIES:
    for sim in SIM_LEVELS:
        key = (cat, sim)
        picked = pick_unique(bins[key], used_ids, TARGET_PER_BIN)
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
                if row["image_id"] not in used_ids:
                    final.append(row)
                    used_ids.add(row["image_id"])
                    fallback_counts[key] += 1
                    made_progress = True
                    break
    if not made_progress:
        tries += 1
        print(f"⚠️  No new samples added in pass {tries}. Retrying fallback...")
    else:
        tries = 0

# --- Step 3A: Global top-off from underrepresented bins ---
if len(final) < TARGET_TOTAL:
    print(f"\n🔁 Step 3A: Sampling globally to reach 500...")
    current_counts = Counter((r["category"], r["similarity_level"]) for r in final)
    needed_per_bin = {(cat, sim): TARGET_PER_BIN - current_counts.get((cat, sim), 0)
                      for cat in CATEGORIES for sim in SIM_LEVELS}

    remaining_candidates = []
    for key, rows in bins.items():
        for row in rows:
            if row["image_id"] not in used_ids:
                remaining_candidates.append((key, row))

    remaining_candidates.sort(key=lambda x: needed_per_bin.get(x[0], 0), reverse=True)

    for key, row in remaining_candidates:
        if len(final) >= TARGET_TOTAL:
            break
        if row["image_id"] not in used_ids:
            final.append(row)
            used_ids.add(row["image_id"])
            fallback_counts[key] += 1
print(f"\n📈 Step 3A complete — collected {len(final)} rows (target: {TARGET_TOTAL})")


# --- Step 3B: Evening out bin distribution ---
print("\n⚖️ Step 3B: Evening out overfull vs underfull bins...")

final_df = pd.DataFrame(final)
bin_counts = final_df.groupby(["category", "similarity_level"]).size()
overfull_bins = bin_counts[bin_counts > TARGET_PER_BIN].sort_values(ascending=False)
underfull_bins = bin_counts[bin_counts < TARGET_PER_BIN].sort_values()

bin_to_rows = defaultdict(list)
for i, row in final_df.iterrows():
    bin_to_rows[(row["category"], row["similarity_level"])].append((i, row))

swaps = 0
for under_bin in underfull_bins.index:
    needed = TARGET_PER_BIN - bin_counts[under_bin]
    if needed <= 0:
        continue

    for over_bin in overfull_bins.index:
        if bin_counts[over_bin] <= TARGET_PER_BIN:
            continue

        for i, row in bin_to_rows[over_bin]:
            for candidate in bins[under_bin]:
                if candidate["image_id"] not in used_ids:
                    final[i] = candidate
                    used_ids.add(candidate["image_id"])
                    bin_counts[under_bin] += 1
                    bin_counts[over_bin] -= 1
                    fallback_counts[under_bin] += 1
                    swaps += 1
                    break
            if bin_counts[under_bin] >= TARGET_PER_BIN:
                break
        if bin_counts[under_bin] >= TARGET_PER_BIN:
            break

print(f"✅ Step 3B complete — {swaps} rows swapped to even bins.")

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
