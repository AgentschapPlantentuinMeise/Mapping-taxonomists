import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import operator
from itertools import groupby

# ── PATH SETUP ─────────────────────────────────────────────
this_file = Path(__file__).resolve()
root_dir = this_file.parents[2]
data_dir = root_dir / "data"
figures_dir = root_dir / "reports" / "figures"
figures_dir.mkdir(parents=True, exist_ok=True)

articles_path = data_dir / "processed" / "taxonomic_articles_with_subjects.pkl"

# ── LOAD DATA ──────────────────────────────────────────────
print("Processing input data...")
articles = pd.read_pickle(articles_path)

# ── AGGREGATE OPEN ACCESS STATUSES ─────────────────────────
data_plot = pd.DataFrame()

for j in set(articles["source_id"]):
    journal_df = articles[articles["source_id"] == j]
    oa_statuses = sorted(journal_df["oa_oa_status"].fillna("unknown"))
    
    freqs_dict = {status: oa_statuses.count(status) for status in set(oa_statuses)}
    data_plot = pd.concat([data_plot, pd.DataFrame(freqs_dict, index=[j])]).fillna(0)

# Keep only journals with ≥20 articles and selected OA types
oa_cols = ["closed", "hybrid", "bronze", "green", "gold", "diamond"]
data_plot = data_plot[oa_cols]
data_plot["sum"] = data_plot.sum(axis=1)
data_plot = data_plot[data_plot["sum"] >= 20]

# ── ABSOLUTE BAR CHART ─────────────────────────────────────
print("Drawing bar plot of open access statuses per journal...")

data_plot = data_plot.sort_values(by=["closed"], ascending=False)
labels = list(data_plot.index)
fig, ax = plt.subplots()

# Draw stacked bars
bottom = np.zeros(len(data_plot))
colors = ["red", "grey", "brown", "green", "gold", "blue"]

for col, color in zip(oa_cols, colors):
    ax.bar(labels, data_plot[col], label=col, bottom=bottom, color=color)
    bottom += data_plot[col].values

ax.set_xticklabels([])
ax.set_xticks([])
ax.set_ylabel("Number of articles")
ax.set_xlabel("Journals")
ax.legend()
plt.savefig(figures_dir / "absolute_oa_status_journals.jpg", dpi=1200)
plt.close()

# ── PERCENTUAL BAR CHART ───────────────────────────────────
percentages_oa = pd.DataFrame()

for _, journal in data_plot[oa_cols].iterrows():
    percentages_oa = pd.concat([percentages_oa, journal / sum(journal)], axis=1)

percentages_oa = percentages_oa.transpose()
percentages_oa = percentages_oa.sort_values(by=["closed", "diamond", "gold", "green"], ascending=[False, True, True, True])
percentages_oa *= 100

print("Drawing percentual bar plot of open access statuses per journal...")

fig, ax = plt.subplots()
bottom = np.zeros(len(percentages_oa))
cb_colors = ["#AD1831", "#A087FF", "#B7803E", "#72C352", "#FFDE7A", "#98CFFF"]

for col, color in zip(oa_cols, cb_colors):
    ax.bar(labels, percentages_oa[col], width=1.0, label=col, bottom=bottom, color=color)
    bottom += percentages_oa[col].values

ax.set_xticklabels([])
ax.set_xticks([])
ax.set_ylabel("Articles (%)", fontsize=20)
ax.set_xlabel("Journals", fontsize=20)
ax.tick_params(axis='y', labelsize=14)
ax.legend(loc="lower left", fontsize=16)
plt.savefig(figures_dir / "relative_oa_status_journals.jpg", dpi=1200)
plt.close()

# ── PIE CHART OF TOTAL OA TYPES ────────────────────────────
labels = oa_cols
total = np.array(articles["oa_oa_status"].value_counts()[labels])
colors = cb_colors

plt.pie(total, labels=labels, colors=colors, autopct='%1.1f%%')
plt.savefig(figures_dir / "pie_chart_oa_status.jpg", dpi=1200)
plt.close()

print("Script has run. Resulting figures can be found in /reports/figures/.")
