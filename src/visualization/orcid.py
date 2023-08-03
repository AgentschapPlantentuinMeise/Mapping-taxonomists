import numpy as np
import pandas as pd
import matplotlib.pyplot as plt # version 3.5.2
import pickle
import operator
from itertools import groupby


authors = pd.read_csv("../../data/interim/all_authors_of_taxonomic_articles.tsv", sep="\t")

# get single author PER JOURNAL
journal_names = list()
nr_authors = list()
nr_orcid_authors = list()

for j in set(authors["source_id"]):
    # select authors published in this journal
    journal_df = authors[authors["source_id"]==j].drop_duplicates(subset="author_id", ignore_index=True)
    
    # removing journals with fewer than 20 taxonomists to simplify graph 
    if len(journal_df) >= 20:
        journal_names.append(journal_df.loc[0, "source_display_name"])
        # count authors and count authors with orcid
        nr_authors.append(len(journal_df))
        nr_orcid_authors.append(len(x is not None for x in df["orcid"]))

 
# plot the ORCID prevalence among authors per journal
nr_no_orcid = list(map(operator.sub, nr_authors, nr_orcid_authors)

fig, ax = plt.subplots()

ax.bar(journal_names, nr_orcid_authors,
       label="ORCID", color="green")
ax.bar(labels, nr_no_orcid, bottom=nr_orcid_authors,
       label="NO ORCID", color="red")
ax.legend()

plt.xticks(rotation=90, ha="center", fontsize=8)
plt.savefig("../../reports/figures/absolute_orcid_authors_journals.png")


# plot the ORCID prevalence among authors per journal, in percentages
perc_orcids = np.divide(nr_orcid_authors, nr_authors)
perc_no_orcids = 1 - perc_orcids

fig, ax = plt.subplots()

ax.bar(labels, perc_orcids,
       label="ORCID", color="green")
ax.bar(labels, perc_no_orcids, bottom=perc_orcids,
       label="NO ORCID", color="red")
ax.legend()

plt.xticks(rotation=90, ha="center", fontsize=8)
plt.savefig("../../reports/figures/relative_orcid_authors_journals.png")
