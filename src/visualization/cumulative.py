import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

authors = pd.read_pickle("../../data/interim/country_authors_with_all_taxonomic_articles.pkl")
# get unique authors per journal
authors = authors.drop_duplicates(subset=["author_id", "source_id"])

# disambiguate

# start with journal that has most authors
first_journal = max(authors["source_id"],key=list(authors["source_id"]).count)
journal_path = [first_journal,]

authors_seen = list(authors[authors["source_id"]==first_journal]["author_id"])
nr_authors_path = [len(authors_seen),]

unexplored = list(set(authors["source_id"]))
unexplored.remove(first_journal)

# dictionary with journal name and author ids per journal
journal_authors = {}
for journal in set(authors["source_id"]):
    journal_authors[journal] = list(authors[authors["source_id"]==journal]["author_id"])

# find out how many of the authors in a proposed journal have already been seen
def not_in_common(authors1, journal2):
    authors2 = set(journal_authors[journal2])  # Convert to set for faster lookups
    return len(authors2 - set(authors1))  # Subtract authors already seen


# find path of least resistance through journals
while unexplored != None:
    best_journal = ""
    best_author_nr = 0

    # go over every unexplored journal to find out if they're the best
    for j in unexplored:
        new_blood = not_in_common(authors_seen, j)
        # save best journal
        if new_blood > best_author_nr:
            best_author_nr = new_blood
            best_journal = j
    
    # if none of the journals add new authors, stop
    if best_author_nr == 0:
        break
        
    # add to path
    authors_seen.extend(journal_authors[best_journal])
    journal_path.append(best_journal)
    nr_authors_path.append(best_author_nr)
    print("Next best: "+journal_path[-1])
    
    unexplored.remove(best_journal)


# plot path through journals with most new authors, cumulatively
fig, ax = plt.subplots(figsize=(7.5, 5))
cumulative_path = np.cumsum(nr_authors_path)

# Ensure bars fill the space completely
plt.bar(x=range(1, len(journal_path) + 1), height=cumulative_path, width=1.0, align='center')


# Set x and y axis labels
ax.set_xlabel("Number of Journals", fontsize=16)
ax.set_ylabel("Number of Authors (thousands)", fontsize=16)

# Adjust y tick labels to reduce clutter and display in thousands
max_y = cumulative_path[-1]
tick_interval = max_y // 5  # Divide into 5 intervals for cleaner ticks
ax.set_yticks(np.arange(0, max_y + tick_interval, tick_interval))
ax.set_yticklabels([f"{int(y / 1000)}k" for y in ax.get_yticks()], fontsize=14)

# Adjust x tick labels font size
ax.tick_params(axis="x", labelsize=14)

# add 95% line
value_95 = cumulative_path[-1] * 0.95
plt.axhline(y=value_95, color="red", label="95%")
ax.text(len(journal_path) - 0.5, value_95 + 1000, "95%", color="red", fontsize=14)

# Ensure output directory exists
output_dir = "../../reports/figures/"
os.makedirs(output_dir, exist_ok=True)

# Save as PNG and TIFF
png_path = os.path.join(output_dir, "FigS1.png")
tiff_path = os.path.join(output_dir, "FigS1.tif")

plt.savefig(png_path, format="png", dpi=300, bbox_inches="tight")
plt.savefig(tiff_path, format="tiff", dpi=300, bbox_inches="tight", pil_kwargs={"compression": "tiff_lzw"})

plt.show()

print(f"Graph saved as:\nPNG: {png_path}\nTIFF: {tiff_path}")

# Print the figure legend
total_journals = len(journal_path)
print(f"Figure S1: The cumulative frequency curve of newly discovered authors using {total_journals} journals after author deduplication (see methods).")


# Save the path to a text file
journal_id_names = authors[["source_display_name", "source_id"]].drop_duplicates().set_index("source_id")

with open("../../data/interim/journals_cumulative_path.txt", "w", encoding="utf-8") as f:
    f.write("Path Journals:\n")
    for journal_id in journal_path:
        journal_name = journal_id_names.loc[journal_id]
        f.write(journal_name.iloc[0] + "\n")  # Updated to use .iloc
    f.write("\nUnexplored Journals:\n")
    for journal_id in unexplored:
        journal_name = journal_id_names.loc[journal_id]
        f.write(journal_name.iloc[0] + "\n")  # Updated to use .iloc
