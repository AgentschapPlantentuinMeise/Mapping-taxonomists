import pandas as pd
import matplotlib.pyplot as plt
import os

# Load datasets
articles = pd.read_pickle("../../data/processed/taxonomic_articles_with_subjects.pkl")
#backbone = pd.read_csv("../../data/external/backbone/Taxon.tsv", sep="\t", on_bad_lines='skip')

file_path = "../../data/external/backbone/Taxon.tsv"

if not os.path.exists(file_path):
    raise FileNotFoundError(f"The file {file_path} does not exist. Please check the path.")

backbone = pd.read_csv(file_path, sep="\t", on_bad_lines='skip', low_memory=False)

# Reduce the size of backbone for easier searching
backbone = backbone[backbone["taxonomicStatus"] != "doubtful"]
backbone = backbone[["canonicalName", "family"]]
# Remove taxa with no known species name or family
backbone = backbone.dropna().drop_duplicates(ignore_index=True).reset_index(drop=True)

## Link Articles to Taxonomic Backbone
articles["families"] = [list() for _ in range(len(articles.index))]

# Create a dictionary for quick family lookups
seen_species = {}

for species in backbone.itertuples():
    if species.canonicalName not in seen_species:
        seen_species[species.canonicalName] = species.family

# For each article, find families based on species
for i, article in articles.iterrows():
    for species in article["species_subject"]:
        if species in seen_species:
            family_name = seen_species[species]
            if family_name not in article["families"]:
                articles.at[i, "families"].append(family_name)

# Count occurrences of each family across all articles
family_counts = {}

for fam_list in articles["families"]:
    for family in fam_list:
        if family in family_counts:
            family_counts[family] += 1
        else:
            family_counts[family] = 1  # Start from 1

# Create Histogram with Formatting Adjustments
plt.clf()  # Clear the current figure
fig, ax = plt.subplots(figsize=(7.5, 6.5))  # Set dimensions in inches

ax.hist(family_counts.values(), bins=50, range=(0, 50))

# Set axis labels with specified font size
ax.set_xlabel("Articles", fontsize=20, fontname="Arial")
ax.set_ylabel("Families (%)", fontsize=20, fontname="Arial")

ax.tick_params(axis='y', labelsize=18)
ax.tick_params(axis='x', labelsize=18)

for label in ax.get_xticklabels() + ax.get_yticklabels():
    label.set_fontname("Arial")

# If you have a legend to add:
#ax.legend(["Family Distribution"], loc="lower left", fontsize=16)

#plt.title("Histogram of Articles per Family", fontsize=20)
plt.tight_layout()  # Ensure everything fits well
plt.savefig("../../reports/figures/histogram_families.png")

output_path = "../../reports/figures/FigS3.tif"
plt.savefig(output_path, dpi=600, format="tif", pil_kwargs={"compression": "tiff_lzw"})  # Use LZW compression to reduce file size

plt.show()

# Print the Top 10 Families
top_10_families = sorted(family_counts.items(), key=lambda x: x[1], reverse=True)[:10]

# Format the output
formatted_families = ", ".join([f"{family}: {count}" for family, count in top_10_families])
print(f"The top 10 families by number of articles are {formatted_families}.")

