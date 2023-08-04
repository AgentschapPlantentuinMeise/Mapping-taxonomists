import pandas as pd
import pickle
import numpy as np
import time


cropwild = pd.read_excel("../../data/external/crop wild relatives.xlsx", header=1)
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

no_specialists = []

for crop in cropwild.itertuples():
    name = " ".join(crop._3.split()[0:2])
    if name in specialists.keys():
        no_specialists.append(len(specialists[name]))
    else:
        no_specialists.append(0)

cropwild["NUMBER OF SPECIALISTS"] = no_specialists


originalcrops = set(cropwild["CROP"])
ogcropspecialists = {}

for crop in originalcrops:
    ogcropspecialists[crop] = sum(cropwild[cropwild["CROP"]==crop]["NUMBER OF SPECIALISTS"])


cropwildgenera = {}

for species in cropwild["CROP WILD RELATIVE"]:
    cropwildgenera[species.split()[0]] = 0
for species in cropwild.itertuples():
    cropwildgenera[species._3.split()[0]] += species._9
    
genera["nr_cropwildrelatives"] = 0

for genus, nr_genera in cropwildgenera.items(): 
    genera.loc[genera["genus"]==genus, "nr_cropwildrelatives"] = nr_genera

genera.loc[genera["kingdom"]!="Plantae", "nr_cropwildrelatives"] = 0

genera[(genera["nr_cropwildrelatives"]>0) & 
       (genera["author_count"]<=5)].to_csv("../../data/processed/crop_wild_relatives.csv")
