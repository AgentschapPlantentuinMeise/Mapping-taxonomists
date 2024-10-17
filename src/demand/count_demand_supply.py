import pandas as pd
import numpy as np
import pickle

## BACKBONE

backbone = pd.read_csv("../../data/external/backbone/Taxon.tsv", sep="\t", on_bad_lines='skip')
backbone = backbone[backbone["taxonRank"]=="species"]
# drop species with no canonical name
backbone = backbone.dropna(subset="canonicalName").set_index("canonicalName")
# or no full taxonomic lineage to the family
#backbone = backbone.dropna(subset=['kingdom', 'phylum', 'class', 'order', 'family'])

backbone = backbone[['taxonomicStatus',
                     'kingdom', 'phylum', 'class', 'order']]


## AUTHOR COUNTS

# version with dictionary, faster
# get disambiguated, European authors of taxonomic articles
authors = pd.read_pickle("../../data/processed/authors_disambiguated_truncated.pkl")

# link the author's expertise to the taxonomic backbone
available_species = set(backbone.index)
species_authors = {}

for subjects in authors["species_subject"]:
    if len(subjects) != 0: 
        for species in subjects:
            if species in available_species:
                if species not in species_authors:
                    species_authors[species] =  1
                else:
                    species_authors[species] += 1


sp_authors_df = pd.DataFrame(species_authors.keys(), species_authors.values()).reset_index()
sp_authors_df.columns = ["nr_authors", "canonicalName"]
sp_authors_df.set_index("canonicalName")

backbone = backbone.merge(sp_authors_df, on="canonicalName", how="left")


## DEMAND COUNTS

redlist = pd.read_csv("../../data/external/redlist_species_data_europe_taxonomy_needed_oct_15/assessments.csv")
cwr = pd.read_excel("../../data/external/crop wild relatives europe.xlsx", skiprows=1)
horizon = pd.read_csv("../../data/external/IAS_horizon_scanning.tsv", sep="\t")

# get canonical names
#redlist = redlist.rename(columns={"scientificName":"canonicalName"})
cwr["canonicalName"] = [" ".join(x.split()[:2]) for x in cwr["CROP WILD RELATIVE"]]
#horizon = horizon.rename(columns={"Species Name":"canonicalName"})


def count_species(backbone, species_list, countname):
    available_species = set(backbone["canonicalName"])
    species_count = {}

    for species in species_list:
        if species in available_species:
            if species not in species_count:
                species_count[species] =  1
            else:
                species_count[species] += 1
                
    count_df = pd.DataFrame(species_count.keys(), species_count.values()).reset_index()
    count_df.columns = [countname, "canonicalName"]
    count_df.set_index("canonicalName")
    
    backbone = backbone.merge(count_df, on="canonicalName", how="left")
    return backbone


backbone = count_species(backbone, redlist["scientificName"], "taxonomicResearchNeeded")
backbone = count_species(backbone, cwr["canonicalName"], "cropWildRelatives")
backbone = count_species(backbone, horizon["Scientific name"], "horizonInvasives")


## COUNT ON ORDER LEVEL

order = backbone[["kingdom", "phylum", "class", "order"]]
order = order[order["kingdom"]!="Bacteria"]
order = order[order["kingdom"]!="Archaea"].drop_duplicates(ignore_index=True)
order["nr_authors"] = [0.0,]*len(order)

for row in backbone[backbone["nr_authors"]==backbone["nr_authors"]].itertuples():
    order.loc[order["order"]==row.order,"nr_authors"] += row.nr_authors

order["taxonomicResearchNeeded"] = [0.0,]*len(order)
for row in backbone[backbone["taxonomicResearchNeeded"]==backbone["taxonomicResearchNeeded"]].itertuples():
    order.loc[order["order"]==row.order,"taxonomicResearchNeeded"] += row.taxonomicResearchNeeded

order["cropWildRelatives"] = [0.0,]*len(order)
for row in backbone[backbone["cropWildRelatives"]==backbone["cropWildRelatives"]].itertuples():
    order.loc[order["order"]==row.order,"cropWildRelatives"] += row.cropWildRelatives

order["horizonInvasives"] = [0.0,]*len(order)
for row in backbone[backbone["horizonInvasives"]==backbone["horizonInvasives"]].itertuples():
    order.loc[order["order"]==row.order,"horizonInvasives"] += row.horizonInvasives


order.to_pickle("../../data/processed/supply_and_demand_order_level.pkl")
order.to_csv("../../data/processed/supply_and_demand_order_level.tsv", sep="\t")
