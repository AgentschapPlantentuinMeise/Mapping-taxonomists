from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# ── PATH SETUP ─────────────────────────────────────────────

# Resolve root directory from script location
this_file = Path(__file__).resolve()
root_dir = this_file.parents[2]

# Paths to input and output
articles_path = root_dir / "data" / "processed" / "taxonomic_articles_with_subjects.pkl"
backbone_path = root_dir / "data" / "external" / "backbone" / "Taxon.tsv"
figures_dir = root_dir / "reports" / "figures"
figures_dir.mkdir(parents=True, exist_ok=True)

# Output files
png_output = figures_dir / "FigS3.png"
tif_output = figures_dir / "FigS3.tif"

# ── LOAD DATA ─────────────────────────────────────────────

# Load articles
articles = pd.read_pickle(articles_path)

# Check if backbone file exists
if not backbone_path.exists():
    raise FileNotFoundError(f"The file {backbone_path} does not exist. Please check the path.")

# Load and filter backbone
backbone = pd.read_csv(backbone_path, sep="\t", on_bad_lines='skip', low_memory=False)
backbone = backbone[backbone["taxonomicStatus"] != "doubtful"]
backbone = backbone[["canonicalName", "family"]].dropna().drop_duplicates(ignore_index=True)

# ── LINK ARTICLES TO FAMILIES ─────────────────────────────

# Initialize families column
articles["families"] = [[] for _ in range(len(articles))]

# Create lookup for species → family
seen_species = {row.canonicalName: row.family for row in backbone.itertuples()}

# Fill families per article
for i, article in articles.iterrows():
    for species in article["species_subject"]:
        family = seen_species.get(species)
        if family and family not in article["families"]:
            articles.at[i, "families"].append(family)

# ── AGGREGATE COUNTS AND PLOT ─────────────────────────────

# Count family occurrences
family_counts = {}
for fam_list in articles["families"]:
    for family in fam_list:
        family_counts[family] = family_counts.get(family, 0) + 1

# Plot histogram
plt.clf()
fig, ax = plt.subplots(figsize=(7.5, 6.5))
ax.hist(family_counts.values(), bins=50, range=(0, 50))

# Axis labels and styling
ax.set_xlabel("Articles", fontsize=20, fontname="Arial")
ax.set_ylabel("Families (%)", fontsize=20, fontname="Arial")
ax.tick_params(axis='y', labelsize=18)
ax.tick_params(axis='x', labelsize=18)
for label in ax.get_xticklabels() + ax.get_yticklabels():
    label.set_fontname("Arial")

plt.tight_layout()
plt.savefig(png_output, format="png", dpi=300, bbox_inches="tight")
plt.savefig(tif_output, format="tif", dpi=600, bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"})
plt.show()

# ── SUMMARY OUTPUT ─────────────────────────────────────────

# Print top 10 families
top_10 = sorted(family_counts.items(), key=lambda x: x[1], reverse=True)[:10]
formatted_top = ", ".join([f"{fam}: {count}" for fam, count in top_10])
print(f"The top 10 families by number of articles are {formatted_top}.")
