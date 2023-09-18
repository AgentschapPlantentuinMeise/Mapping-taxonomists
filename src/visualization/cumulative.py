import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


authors = pd.read_pickle("../../data/interim/european_authors_with_all_taxonomic_articles.pkl")
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
    authors2 = journal_authors[journal2]
    # get number of authors in journal2 not in total author list so far
    n = 0
    for author in authors2:
        if author not in authors1:
            n += 1
    return n

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
fig, ax = plt.subplots()
cumulative_path = np.cumsum(nr_authors_path)

plt.bar(x=range(1,len(journal_path)+1), height=cumulative_path, width=1.0)
ax.set_title("Number of European authors published in journals (cumulative)")

# add 95% line
value_95 = cumulative_path[-1]*0.95
plt.axhline(y=value_95, color="red", label="95%")
ax.text(0.5, value_95+400,"95%", color="red")

plt.savefig("../../reports/figures/cumulative_graph_european_authors_in_journals.png")

# save the path we took
journal_id_names = authors[["source_display_name", "source_id"]].drop_duplicates()
journal_id_names = journal_id_names.set_index("source_id")

with open("../../data/interim/journals_cumulative_path.txt", "w", encoding="utf-8") as f:
    for journal_id in journal_path:
        # write each item on a new line
        journal_name = journal_id_names.loc[journal_id]
        f.write(journal_name[0]+"\n")
    # add last journals too
    for journal_id in unexplored:
        journal_name = journal_id_names.loc[journal_id]
        f.write(journal_name[0]+"\n")
