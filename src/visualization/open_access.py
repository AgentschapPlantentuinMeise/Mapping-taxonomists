import numpy as np
import pandas as pd
import matplotlib.pyplot as plt # version 3.5.2
import pickle
import operator
from itertools import groupby


print("Processing input data...")
articles = pd.read_pickle("../../data/processed/taxonomic_articles_with_subjects.pkl")

#print(articles["oa_oa_status"].value_counts())

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

# remove journals with fewer than 20 relevant articles to simplify graph 
data_plot = data_plot[["closed", "hybrid", "bronze", "green", "gold", "diamond"]] # remove False and True
data_plot["sum"] = data_plot.sum(axis=1)
data_plot = data_plot[data_plot["sum"]>=20]


# drawing bar chart (absolute)
print("Drawing bar plot of open access statuses per journal...")

data_plot = data_plot.sort_values(by=["closed"], ascending=False)

labels = list(data_plot.index)
fig, ax = plt.subplots()

ax.bar(labels, data_plot["closed"],
       label="closed", color="red")
ax.bar(labels, data_plot["hybrid"], bottom=data_plot["closed"],
       label="hybrid", color="grey")
ax.bar(labels, data_plot["bronze"], 
       bottom=data_plot["closed"]+data_plot["hybrid"],
       label="bronze", color="brown")
ax.bar(labels, data_plot["green"], 
       bottom=data_plot["closed"]+data_plot["hybrid"]+data_plot["bronze"],
       label="green", color="green")
ax.bar(labels, data_plot["gold"], 
       bottom=data_plot["closed"]+data_plot["hybrid"]+data_plot["bronze"]+data_plot["green"],
       label="gold", color="gold")
ax.bar(labels, data_plot["diamond"], 
       bottom=data_plot["closed"]+data_plot["hybrid"]+data_plot["bronze"]+data_plot["green"]+data_plot["gold"],
       label="diamond", color="blue")

ax.set_xticklabels([])
ax.set_xticks([])

ax.set_ylabel("Number of articles")
ax.set_xlabel("Journals")

ax.legend()

plt.savefig("../../reports/figures/absolute_oa_status_journals.jpg", dpi=1200)
plt.figure()


# drawing percentual bar chart
percentages_oa = pd.DataFrame()

for _, journal in data_plot.loc[:, data_plot.columns != "sum"].iterrows():
    percentages_oa = pd.concat([percentages_oa, journal / sum(journal)], axis=1)

percentages_oa = percentages_oa.transpose()
percentages_oa = percentages_oa.sort_values(by=["closed", "diamond", "gold", "green"], ascending=[False,True, True, True])
percentages_oa = percentages_oa * 100

print("Drawing percentual bar plot of open access statuses per journal...")

fig, ax = plt.subplots()

ax.bar(labels, percentages_oa["closed"], 1,
       label="closed", color="#AD1831")
ax.bar(labels, percentages_oa["hybrid"], 1,
       bottom=percentages_oa["closed"],
       label="hybrid", color="#A087FF")
ax.bar(labels, percentages_oa["bronze"], 1,
       bottom=percentages_oa["closed"]+percentages_oa["hybrid"],
       label="bronze", color="#B7803E")
ax.bar(labels, percentages_oa["green"], 1,
       bottom=percentages_oa["closed"]+percentages_oa["hybrid"]+percentages_oa["bronze"],
       label="green", color="#72C352")
ax.bar(labels, percentages_oa["gold"], 1,
       bottom=percentages_oa["closed"]+percentages_oa["hybrid"]+percentages_oa["bronze"]+percentages_oa["green"],
       label="gold", color="#FFDE7A")
ax.bar(labels, percentages_oa["diamond"], 1,
       bottom=percentages_oa["closed"]+percentages_oa["hybrid"]+percentages_oa["bronze"]+percentages_oa["green"]+percentages_oa["gold"],
       label="diamond", color="#98CFFF")

ax.set_xticklabels([])
ax.set_xticks([])

ax.set_ylabel("Articles (%)", fontsize=20)
ax.set_xlabel("Journals", fontsize=20)
ax.tick_params(axis='y', labelsize=14)

ax.legend(loc="lower left", fontsize=16)

plt.savefig("../../reports/figures/relative_oa_status_journals.jpg", dpi=1200)
plt.figure()


# pie chart of total percentages of each status
#print("Drawing pie chart of open access statuses of articles...")

labels = ["closed","hybrid","bronze","green","gold","diamond"]
total = np.array(articles["oa_oa_status"].value_counts()[labels])
colors= ["#AD1831","#A087FF","#B7803E","#72C352","#FFDE7A","#98CFFF"]

plt.pie(total,
        labels=labels,
        colors=colors,
        autopct='%1.1f%%')

plt.savefig("../../reports/figures/pie_chart_oa_status.jpg", dpi=1200)
plt.figure()


print("Script has run. Resulting figures can be found in /reports/figures/.")

