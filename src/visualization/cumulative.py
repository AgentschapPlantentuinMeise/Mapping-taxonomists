import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pickle


authors = pd.read_pickle("../../data/interim/all_authors_of_european_taxonomic_articles.pkl")
# get unique authors per journal
authors = authors.drop_duplicates(subset=["author_id", "source_display_name"])
"""
# count number of authors per journal
article_counts = authors[["article_id", 
                          "source_display_name"]].groupby(["source_display_name"]) \
                                                 .count() \
                                                 .reset_index() \
                                                 .sort_values(["article_id"], ascending=False)
article_counts.columns = ["journalName", "numberOfArticles"]
article_counts.to_csv("../../data/processed/european_authors_counts_per_journal.csv")
"""
# start with Zootaxa (has most authors)
nr_authors_path = [len(authors[authors["source_display_name"]=="Zootaxa"]),] 
journal_path = ["Zootaxa",]
unexplored = list(set(authors["source_display_name"]))
unexplored.remove("Zootaxa")
authors_seen = list(authors[authors["source_display_name"]=="Zootaxa"]["author_id"])

# dictionary with journal name and author ids in that journal
journal_authors = {}
for journal in set(authors["source_display_name"]):
    journal_authors[journal] = list(authors[authors["source_display_name"]==journal]["author_id"])

# find out how many of the authors in a proposed journal have already been seen
def not_in_common(authors1, journal2):
    authors2 = journal_authors[journal2]
    # get number of authors in journal2 not in total author list so far
    n = 0
    for author in authors2:
        if author not in authors1:
            n += 1
    return n

nr_journals = len(set(authors["source_display_name"]))

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
    
    if best_author_nr == 0:
        break
        
    # add to path
    authors_seen.extend(journal_authors[best_journal])
    journal_path.append(best_journal)
    nr_authors_path.append(best_author_nr)
    print("Next best: "+journal_path[-1])
    
    unexplored.remove(best_journal)


# plot path through journals with most new authors, cumulatively
fig, ax = plt.subplots()
cumulative_path = np.cumsum(nr_authors_path)

plt.bar(x=journal_path, height=cumulative_path)
plt.xticks(rotation=90, ha="center", fontsize=4)
ax.set_title("Number of European authors published in journals (cumulative)")

# add 95% line
value_95 = cumulative_path[-1]*0.95
plt.axhline(y=value_95, color="red", label="95%")
ax.text(0.5, value_95+200,"95%", color="red")
plt.show()

plt.savefig("../../reports/figures/cumulative_graph_european_authors_in_journals.png")

len(journal_path)
