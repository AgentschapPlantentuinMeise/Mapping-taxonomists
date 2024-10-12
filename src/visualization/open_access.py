import numpy as np
import pandas as pd
import matplotlib.pyplot as plt # version 3.5.2
import pickle
import operator
from itertools import groupby


articles = pd.read_pickle("../../data/processed/taxonomic_articles_with_subjects.pkl")

print(articles["oa_is_oa"].value_counts())

# get oa statuses of articles PER JOURNAL
data_plot = pd.DataFrame()

for j in set(articles["source_id"]):
    # select articles published in this journal
    journal_df = articles[articles["source_id"]==j]
    # get open access statuses of those articles
    oa_statuses = list(journal_df["oa_oa_status"].fillna("unknown"))
    oa_statuses = sorted(oa_statuses)
    
    # count frequency of oa statuses
    freqs_dict = {}
    for status in set(oa_statuses):
        freqs_dict[status] = oa_statuses.count(status)
    
    data_plot = pd.concat([data_plot, pd.DataFrame(freqs_dict, index=[j])]).fillna(0)

# removing journals with fewer than 20 relevant articles to simplify graph 
data_plot["sum"] = data_plot.sum(axis=1)
data_plot = data_plot[data_plot["sum"]>=20]
data_plot = data_plot.iloc[:,0:5]
data_plot

labels = list(data_plot.index)
fig, ax = plt.subplots()

#ax.bar(labels, data_plot["unknown"], NO UNKNOWNS IN NEWER DATA
#       label="unknown", color="grey")
ax.bar(labels, data_plot["closed"],
       label="closed", color="red")
ax.bar(labels, data_plot["hybrid"], bottom=data_plot["closed"],
       label="hybrid", color="blue")
ax.bar(labels, data_plot["bronze"], bottom=data_plot["closed"]+data_plot["hybrid"],
       label="bronze", color="brown")
ax.bar(labels, data_plot["green"], 
       bottom=data_plot["closed"]+data_plot["hybrid"]+data_plot["bronze"],
       label="green", color="green")
ax.bar(labels, data_plot["gold"], 
       bottom=data_plot["closed"]+data_plot["hybrid"]+data_plot["bronze"]+data_plot["green"],
       label="gold", color="gold")
ax.legend()

plt.xticks(rotation=90, ha="center", fontsize=8)
plt.savefig("../../reports/figures/absolute_oa_status_journals.png")

percentages_oa = pd.DataFrame()

for _, journal in data_plot.iterrows():
    percentages_oa = pd.concat([percentages_oa, journal / sum(journal)], axis=1)

percentages_oa = percentages_oa.transpose()

fig, ax = plt.subplots()

ax.bar(labels, percentages_oa["closed"],
       label="closed", color="red")
ax.bar(labels, percentages_oa["hybrid"], 
       bottom=percentages_oa["closed"],
       label="hybrid", color="blue")
ax.bar(labels, percentages_oa["bronze"], 
       bottom=percentages_oa["closed"]+percentages_oa["hybrid"],
       label="bronze", color="brown")
ax.bar(labels, percentages_oa["green"], 
       bottom=percentages_oa["closed"]+percentages_oa["hybrid"]+percentages_oa["bronze"],
       label="green", color="green")
ax.bar(labels, percentages_oa["gold"], 
       bottom=percentages_oa["closed"]+percentages_oa["hybrid"]+percentages_oa["bronze"]+percentages_oa["green"],
       label="gold", color="gold")
ax.legend()

plt.xticks(rotation=90, ha="center", fontsize=8)
plt.savefig("../../reports/figures/relative_oa_status_journals.png")


# pie chart of total percentages of each status
labels = ["closed","hybrid","bronze","green","gold"]
total = np.array([sum(data_plot["closed"]),
                  sum(data_plot["hybrid"]),
                  sum(data_plot["bronze"]),
                  sum(data_plot["green"]),
                  sum(data_plot["gold"])])
colors= ["red","blue","brown","green","gold"]

plt.pie(total,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%')
plt.savefig("../../reports/figures/pie_chart_oa_status.png")

