import pandas as pd
import pickle
import numpy as np


invasives = pd.read_csv("../../data/external/invasive horizon species europe.tsv", sep="\t")
gbif_taxonomy = pd.read_csv("../../data/external/backbone/Taxon.tsv", sep="\t", on_bad_lines='skip')

eu_authors = pd.read_csv("../../data/processed/european_taxonomic_authors_no_duplicates.tsv", sep="\t")

# get authors that are specialized per species
specialists = {}
all_species = [species for sublist in eu_authors["species_subject"] for species in sublist]
for species in set(all_species):
    specialists[species] = []

for author in eu_authors.itertuples():
    for species in author.species_subject:
        if author.author_id not in specialists[species]:
            specialists[species].append(author.author_id)
# synonyms?

invasives
no_specialists = []
for species in invasives["Species Name "]:
    if species[:-1] in specialists.keys():
        no_specialists.append(len(specialists[species[:-1]]))
    else:
        no_specialists.append(0)
        
invasives["Number of Specialists "] = no_specialists

genera = gbif_taxonomy[["kingdom", "phylum", "class", "order", "family", 
                        "genus"]].dropna().drop_duplicates(ignore_index=True)

genera["author_count"] = 0

for species, n_authors in specialists.items():
    if not genera[genera["genus"]==species.split()[0]].empty:
        genera.loc[genera["genus"]==species.split()[0], "author_count"] += len(n_authors)

genera["nr_invasive"] = 0

for species in invasives.itertuples():
    genera.loc[genera["genus"] == species._1.split()[0],"nr_invasive"] += 1

genera[(genera["nr_invasive"]>0) & (genera["author_count"]==0)].to_csv("../../data/processed/horizon_invasives.csv")
