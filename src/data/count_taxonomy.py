import pandas as pd
import numpy as np
import pickle

backbone = pd.read_csv("../../data/external/backbone/Taxon.tsv", sep="\t", on_bad_lines='skip')
# drop species with no canonical name
backbone = backbone[np.logical_not(backbone["canonicalName"].isnull())].set_index("canonicalName")

articles = pd.read_pickle("../../data/processed/european_taxonomic_articles_with_subjects.pkl")

# count number of articles per species name
species_count = {}

for subjects in articles["species_subject"]:
    if len(subjects) != 0: 
        for species in subjects:
            if species in species_count:
                species_count[species] += 1
            else:
                species_count[species] = 1

df = pd.DataFrame({"canonicalName" : species_count.keys(), 
                   "numberOfArticles" : species_count.values()}).set_index("canonicalName")
# link counts to taxonomic backbone
output = df.join(backbone[["acceptedNameUsageID", "taxonomicStatus",
                           "kingdom", "phylum", "class", "order", "family", "genus"]])
"""
# propagating counts from synonyms to accepted names
for synonym in output[output["taxonomicStatus"]=="synonym"].itertuples():
    # acceptedNameUsageID points to the accepted taxon ID for a synonym
    print(synonym.index)
    accepted_name = backbone[backbone["taxonID"]==synonym.acceptedNameUsageID].index
    nr_articles = output.loc[synonym.index, "numberOfArticles"]
    
    if accepted_name in output.index:
        # add synonym count to existing accepted name if available
        output.loc[output["canonicalName"]==accepted_name, "numberOfArticles"] += nr_articles
        output.drop(synonym.index)
    else:
        # change synonym name to accepted name if unavailable
        output.rename(index={synonym.index:accepted_name}, inplace=True)
"""
output.to_pickle("../../data/processed/article_counts_per_taxon.pkl")
output.to_csv("../../data/processed/article_counts_per_taxon.tsv", sep="\t")
