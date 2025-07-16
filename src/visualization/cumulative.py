import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# === Set project root directory ===
root_dir = Path(__file__).resolve().parents[2]  # Adjust if script depth differs
data_dir = root_dir / "data"
interim_dir = data_dir / "interim"
reports_dir = root_dir / "reports" / "figures"

# === Load data ===
authors_path = interim_dir / "country_authors_with_all_taxonomic_articles.pkl"
authors = pd.read_pickle(authors_path)

# === Process authors ===
authors = authors.drop_duplicates(subset=["author_id", "source_id"])
first_journal = max(authors["source_id"], key=list(authors["source_id"]).count)
journal_path = [first_journal]
authors_seen = list(authors[authors["source_id"] == first_journal]["author_id"])
nr_authors_path = [len(authors_seen)]
unexplored = list(set(authors["source_id"]))
unexplored.remove(first_journal)

# === Build journal-author map ===
journal_authors = {
    journal: list(authors[authors["source_id"] == journal]["author_id"])
    for journal in set(authors["source_id"])
}

def not_in_common(authors1, journal2):
    return len(set(journal_authors[journal2]) - set(authors1))

while unexplored:
    best_journal = ""
    best_author_nr = 0

    for j in unexplored:
        new_blood = not_in_common(authors_seen, j)
        if new_blood > best_author_nr:
            best_author_nr = new_blood
            best_journal = j

    if best_author_nr == 0:
        break

    authors_seen.extend(journal_authors[best_journal])
    journal_path.append(best_journal)
    nr_authors_path.append(best_author_nr)
    #print("Next best:", best_journal)
    unexplored.remove(best_journal)

# === Plot cumulative bar chart ===
fig, ax = plt.subplots(figsize=(7.5, 5))
cumulative_path = np.cumsum(nr_authors_path)
plt.bar(range(1, len(journal_path) + 1), cumulative_path, width=1.0, align="center")
ax.set_xlabel("Number of Journals", fontsize=16)
ax.set_ylabel("Number of Authors (thousands)", fontsize=16)

max_y = cumulative_path[-1]
tick_interval = max_y // 5
ax.set_yticks(np.arange(0, max_y + tick_interval, tick_interval))
ax.set_yticklabels([f"{int(y / 1000)}k" for y in ax.get_yticks()], fontsize=14)
ax.tick_params(axis="x", labelsize=14)

# Add 95% reference line
value_95 = cumulative_path[-1] * 0.95
plt.axhline(y=value_95, color="red", label="95%")
ax.text(len(journal_path) - 0.5, value_95 + 1000, "95%", color="red", fontsize=14)

# === Save figure ===
reports_dir.mkdir(parents=True, exist_ok=True)
(plt.savefig(reports_dir / "FigS1.png", format="png", dpi=300, bbox_inches="tight"))
(plt.savefig(reports_dir / "FigS1.tif", format="tiff", dpi=300, bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"}))
plt.show()

print(f"Graph saved as:\nPNG: {reports_dir / 'FigS1.png'}\nTIFF: {reports_dir / 'FigS1.tif'}")
print(f"Figure S1: The cumulative frequency curve of newly discovered authors using {len(journal_path)} journals after author deduplication (see methods).")

# === Save journal names in order ===
journal_id_names = authors[["source_display_name", "source_id"]].drop_duplicates().set_index("source_id")
output_txt_path = interim_dir / "journals_cumulative_path.txt"

with open(output_txt_path, "w", encoding="utf-8") as f:
    f.write("Path Journals:\n")
    for journal_id in journal_path:
        journal_name = journal_id_names.loc[journal_id]
        f.write(journal_name.iloc[0] + "\n")
    f.write("\nUnexplored Journals:\n")
    for journal_id in unexplored:
        journal_name = journal_id_names.loc[journal_id]
        f.write(journal_name.iloc[0] + "\n")
