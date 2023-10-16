import pandas as pd
import numpy as np
import pickle
#import prep_taxonomy


backbone = pd.read_csv("../../data/external/backbone/Taxon.tsv", sep="\t", on_bad_lines='skip')
backbone = backbone[backbone["taxonRank"]=="species"]
# drop species with no canonical name
backbone = backbone.dropna(subset="canonicalName").set_index("canonicalName")
# and no full taxonomic lineage to the family
#backbone = backbone.dropna(subset=['kingdom', 'phylum', 'class', 'order', 'family'])
backbone = backbone[['taxonomicStatus', 'taxonID', 'acceptedNameUsageID',
                     'kingdom', 'phylum', 'class', 'order', 'family', 'genus']]

backbone["numberOfAuthors"] = [0,]*len(backbone.index)


# get disambiguated, European authors of taxonomic articles
authors = pd.read_pickle("../../data/processed/european_authors_disambiguated_truncated.pkl")

# link the author's expertise to the taxonomic backbone
available_species = set(backbone.index)

for subjects in authors["species_subject"]:
    if len(subjects) != 0: 
        for species in subjects:
            if species in available_species:
                backbone.loc[species, "numberOfAuthors"] += 1

# propagate synonyms
for row in backbone.itertuples():
    if row.taxonomicStatus == "synonym":
        backbone.loc[backbone["taxonID"]==row.acceptedNameUsageID,"numberOfAuthors"] += row.numberOfAuthors
        backbone.drop(index=row.Index)

backbone.to_pickle("../../data/processed/backbone_with_author_counts.pkl")
backbone.to_csv("../../data/processed/backbone_with_author_counts.tsv", sep="\t")
