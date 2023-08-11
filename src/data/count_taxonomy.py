import pandas as pd
import numpy as np
import pickle


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
                backbone.loc[species] += 1

# propagate synonyms
for i, row in backbone.itertuples(index=True):
    if row.taxonomicStatus == "synonym":
        backbone.loc[backbone["taxonID"]==row.acceptedNameUsageID,"numberOfAuthors"] += row.numberOfAuthors
        backbone.drop(index=i)

backbone.to_pickle("../../data/processed/backbone_with_author_counts.pkl")
backbone.to_csv("../../data/processed/backbone_with_author_counts.tsv", sep="\t")

        
"""
df = pd.DataFrame({"canonicalName" : species_count.keys(), 
                   "numberOfAuthors" : species_count.values()}).set_index("canonicalName")
# link counts to taxonomic backbone
output = df.join(backbone[["acceptedNameUsageID", "taxonomicStatus",
                           "kingdom", "phylum", "class", "order", "family", "genus"]])

accepted_output

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

output.to_pickle("../../data/processed/article_counts_per_taxon.pkl")
output.to_csv("../../data/processed/article_counts_per_taxon.tsv", sep="\t")
"""