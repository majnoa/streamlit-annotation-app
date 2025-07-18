import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- Config ---
INPUT_FILE = "balanced_user_study_sample500including0.csv"
OUTPUT_IMAGE = "similarity_per_category.png"

# --- Load and group data ---
df = pd.read_csv(INPUT_FILE)
grouped = df.groupby(["category", "similarity_level"]).size().unstack(fill_value=0)

# Ensure all similarity levels (0–4) are included, even if missing
for sim_level in range(0, 5):
    if sim_level not in grouped.columns:
        grouped[sim_level] = 0

grouped = grouped[[0, 1, 2, 3, 4]]  # sort columns

# --- Plot grouped bar chart ---
plt.figure(figsize=(10, 6))
bar_width = 0.15
x = np.arange(len(grouped.index))
colors = ["#999999", "#4c72b0", "#55a868", "#c44e52", "#8172b3"]
offsets = np.linspace(-2, 2, 5) * bar_width

for i, sim_level in enumerate(range(0, 5)):
    plt.bar(
        x + offsets[i],
        grouped[sim_level],
        width=bar_width,
        label=f"Sim {sim_level}",
        color=colors[i]
    )

plt.xticks(x, [f"Category {c}" for c in grouped.index])
plt.xlabel("Category")
plt.ylabel("Count")
plt.title("Similarity Level Distribution per Category")
plt.legend(title="Similarity Level")
plt.tight_layout()
plt.savefig(OUTPUT_IMAGE, dpi=300)
plt.close()

print(f"✅ Saved grouped bar chart to {OUTPUT_IMAGE}")
