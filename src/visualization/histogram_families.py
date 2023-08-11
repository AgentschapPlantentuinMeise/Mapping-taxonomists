import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


articles = pd.read_pickle("../../data/processed/european_taxonomic_articles_with_subjects.pkl")
backbone = pd.read_csv("../../data/external/backbone/Taxon.tsv", sep="\t", on_bad_lines='skip')

# reduce size of backbone for easier searching
backbone = backbone[backbone["taxonomicStatus"]!="doubtful"]
backbone = backbone[["canonicalName", "family"]]
# remove taxa with no known species name or family
backbone = backbone.dropna().drop_duplicates(ignore_index=True).reset_index(drop=True)

## LINK ARTICLES TO BACKBONE
# start with empty list for every taxonomic level 
articles["families"] = [list() for _ in range(len(articles.index))]

seen_species = {}

for species in backbone.itertuples():
    if species.canonicalName not in seen_species:
        seen_species[species.canonicalName] = species.family
        
# for every author, break down every species they study into different taxonomic levels
for i, article in articles.iterrows():
    for species in article["species_subject"]:
        if species in seen_species:
            # get family name according to GBIF
            family_name = seen_species[species]
            # add this family (families) to the list of genera studied by the author (no duplicates)
            if family_name not in article["families"]:
                articles.loc[i, "families"].append(family_name)
                
family_counts = dict()

for fam_list in articles["families"]:
    for family in fam_list:
        if family in family_counts:
            family_counts[family] += 1
        else:
            family_counts[family] = 0
            
plt.hist(family_counts.values(), bins=50, range=(0,50))
plt.xlabel("# articles")
plt.ylabel("# families")
plt.title("Histogram of articles per family")
plt.savefig("../../reports/figures/histogram_families.png")
