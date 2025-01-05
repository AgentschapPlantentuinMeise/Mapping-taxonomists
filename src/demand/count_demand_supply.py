import pandas as pd
import numpy as np
import pickle

## BACKBONE

backbone = pd.read_csv("../../data/external/backbone/Taxon.tsv", sep="\t", on_bad_lines='skip', low_memory=False)
backbone = backbone[backbone["taxonRank"]=="species"]

# Check for trailing or leading spaces
backbone["canonicalName"] = backbone["canonicalName"].str.strip()

# drop species with no canonical name
backbone = backbone.dropna(subset="canonicalName").set_index("canonicalName")

# or no full taxonomic lineage to the family
#backbone = backbone.dropna(subset=['kingdom', 'phylum', 'class', 'order', 'family'])

# Retain only necessary columns
backbone = backbone[[ 'taxonomicStatus', 'kingdom', 'phylum', 'class', 'order']]

# Create the lineage column
backbone['lineage'] = (
    'Root;' +
    'k__' + backbone['kingdom'].fillna('') + ';' +
    'p__' + backbone['phylum'].fillna('') + ';' +
    'c__' + backbone['class'].fillna('') + ';' +
    'o__' + backbone['order'].fillna('')
)

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

redlist = pd.read_csv("../../data/external/IUCN_eu_region_tax_research_needed/assessments.csv")
redlist["scientificName"] = redlist["scientificName"].str.strip()

cwr = pd.read_excel("../../data/external/crop wild relatives europe.xlsx", skiprows=1)
horizon = pd.read_csv("../../data/external/IAS_horizon_scanning.tsv", sep="\t")
birdDir = pd.read_csv("../../data/external/birds_directive_annexi+gbif.csv", sep=",")
habitatsDir = pd.read_csv("../../data/external/habitats_directive_art_17_checklis+gbif.csv", sep=",")
marineDir = pd.read_csv("../../data/external/MSFD_descriptor1+worms.csv", sep=",")
iasListConcern = pd.read_csv("../../data/external/IAS_list_union_concern+gbif.csv", sep=",")
pollinators = pd.read_csv("../../data/external/pollinators_sps_list_Reverte_et_al_insect_conservation&diversity_2023.csv", sep=",")
redlistFull = pd.read_csv("../../data/external/european_red_list_2017_december.csv", sep=",")

# 1. Convert NaN to empty strings in 'scientificName' 
redlistFull["scientificName"] = redlistFull["scientificName"].fillna("")

# 2. Create a mask for rows where 'scientificName' is empty
mask_empty = redlistFull["scientificName"].eq("")

# 3. Only overwrite 'scientificName' for those empty rows
redlistFull.loc[mask_empty, "scientificName"] = (
    redlistFull.loc[mask_empty, "taxonomicRankGenus"] 
    + " " 
    + redlistFull.loc[mask_empty, "taxonomicRankSpecies"]
)

included_categories = ["VU", "EN", "CR", "CR (PE)", "EW", "EX"]

redlistFiltered = redlistFull[
    redlistFull["europeanRegionalRedListCategory"].isin(included_categories)
]

fullRedListUniq = redlistFiltered["scientificName"].unique()

# get canonical names
#redlist = redlist.rename(columns={"scientificName":"canonicalName"})
cwr["canonicalName"] = [" ".join(x.split()[:2]) for x in cwr["CROP WILD RELATIVE"]]
#horizon = horizon.rename(columns={"Species Name":"canonicalName"})


def count_species(backbone, species_list, countname):
    # Convert to set so duplicates are counted only once
    unique_species = set(species_list)
    available_species = set(backbone["canonicalName"])
    species_count = {}

    for species in unique_species:
        if species in available_species:
            if species not in species_count:
                species_count[species] =  1
            else:
                species_count[species] += 1
    #print(species_count.keys(), species_count.values())            
    count_df = pd.DataFrame(species_count.keys(), species_count.values()).reset_index()
    count_df.columns = [countname, "canonicalName"]
    count_df.set_index("canonicalName", inplace=True)
    
    backbone = backbone.merge(count_df, on="canonicalName", how="left")
    return backbone

backbone = count_species(backbone, redlist["scientificName"], "taxonomicResearchNeeded")
#backbone = count_species(backbone, cwr["canonicalName"], "cropWildRelatives")
backbone = count_species(backbone, horizon["Scientific name"], "horizonInvasives")

#backbone = count_species(backbone, birdDir["verbatimScientificName"], "birdDir")
backbone = count_species(backbone, habitatsDir["verbatimScientificName"], "habitatsDir")
backbone = count_species(backbone, marineDir["ScientificName_accepted"], "marineDir")
backbone = count_species(backbone, iasListConcern["canonicalName"], "iasListConcern")
#backbone = count_species(backbone, pollinators["GenusAndSpecies"], "pollinators")
backbone = count_species(backbone, fullRedListUniq, "redlistFull")

#To avoid homonyms
# Filter the backbone to Animalia only
backbone_animalia = backbone[backbone["kingdom"] == "Animalia"].copy()
# Filter the backbone to Plantae only
backbone_plantae = backbone[backbone["kingdom"] == "Plantae"].copy()

backbone_else = backbone[
    ~backbone["kingdom"].isin(["Animalia", "Plantae"])
].copy()

# For birds and pollinators, we only want to count them on the Animalia subset:
backbone_animalia = count_species(backbone_animalia, birdDir["verbatimScientificName"], "birdDir")
backbone_animalia = count_species(backbone_animalia, pollinators["GenusAndSpecies"], "pollinators")

# For Crop Wild Relatives, we only want to count them on the Plantae subset:
backbone_plantae = count_species(backbone_plantae, cwr["canonicalName"], "cropWildRelatives")

backbone.head()

# Now combine the updated Animalia and Plantae subset back into the main backbone
# The easiest is to re-merge them by index or columns (depending on your setup).
# Since you set `canonicalName` as the index earlier, let's do it by that index:
backbone_animalia.reset_index(inplace=True)
backbone_plantae.reset_index(inplace=True)
backbone_else.reset_index(inplace=True)

# Combine (stack) them back up:
backbone_updated = pd.concat([backbone_animalia, backbone_plantae, backbone_else], 
                             axis=0, ignore_index=True)

# Restore the index (canonicalName) if desired:
backbone_updated.set_index("canonicalName", inplace=True)

# Now this is your final backbone, with pollinator/bird counts in Animalia,
# cwr counts in Plantae, and everything else remains the same.
backbone = backbone_updated
backbone_updated.columns
## COUNT ON ORDER LEVEL

order = backbone[["lineage", "kingdom", "phylum", "class", "order"]]
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

order["birdDir"] = [0.0,]*len(order)
for row in backbone[backbone["birdDir"]==backbone["birdDir"]].itertuples():
    order.loc[order["order"]==row.order,"birdDir"] += row.birdDir
    
order["habitatsDir"] = [0.0,]*len(order)
for row in backbone[backbone["habitatsDir"]==backbone["habitatsDir"]].itertuples():
    order.loc[order["order"]==row.order,"habitatsDir"] += row.habitatsDir
    
order["marineDir"] = [0.0,]*len(order)
for row in backbone[backbone["marineDir"]==backbone["marineDir"]].itertuples():
    order.loc[order["order"]==row.order,"marineDir"] += row.marineDir
    
order["iasListConcern"] = [0.0,]*len(order)
for row in backbone[backbone["iasListConcern"]==backbone["iasListConcern"]].itertuples():
    order.loc[order["order"]==row.order,"iasListConcern"] += row.iasListConcern
    
order["pollinators"] = [0.0,]*len(order)
for row in backbone[backbone["pollinators"]==backbone["pollinators"]].itertuples():
    order.loc[order["order"]==row.order,"pollinators"] += row.pollinators
    
order["redlistFull"] = [0.0,]*len(order)
for row in backbone[backbone["redlistFull"]==backbone["redlistFull"]].itertuples():
    order.loc[order["order"]==row.order,"redlistFull"] += row.redlistFull

order.to_pickle("../../data/processed/supply_and_demand_order_level.pkl")
order.to_csv("../../data/processed/supply_and_demand_order_level.tsv", sep="\t")


# 1. Select only the columns you need
final_df = backbone[['lineage', 'kingdom', 'phylum', 'class', 'order']].copy()
final_df = final_df[final_df["kingdom"]!="Bacteria"]
final_df = final_df[final_df["kingdom"]!="Archaea"].drop_duplicates(ignore_index=True)

# 2. Add a fixed Confidence column
final_df['Confidence'] = 1

# 3. Rename columns in final_df (lineage -> taxonomy only)
final_df.columns = [
    'taxonomy',   # was lineage
    'kingdom',
    'phylum',
    'class',
    'order',
    'Confidence'
]

# 4. Add a sequential index for otuid
final_df["OTU_ID"] = range(1, len(final_df) + 1)

# 5. Reorder columns so otuid is first
final_df = final_df[[
    'OTU_ID',       # new numeric ID
    'taxonomy',    # lineage
    'kingdom',
    'phylum',
    'class',
    'order',
    'Confidence'
]]

# 6. Write the file
final_df.to_csv("taxAssignments.txt", sep="\t", index=False)

#creating the matrix that links numbers of species to the orders and policies

# Merge on the shared taxonomic columns
merged_df = final_df.merge(
    order[
        [
            'kingdom', 'phylum', 'class', 'order',
            'nr_authors', 'taxonomicResearchNeeded',
            'cropWildRelatives', 'horizonInvasives',
            'habitatsDir', 'marineDir', 'iasListConcern',
            'redlistFull', 'birdDir', 'pollinators'
        ]
    ],
    on=['kingdom', 'phylum', 'class', 'order'],  # the join keys
    how='left'
)

matrix_df = merged_df[[
    'OTU_ID',
    'nr_authors',
    'taxonomicResearchNeeded',
    'cropWildRelatives',
    'horizonInvasives',
    'habitatsDir',
    'marineDir',
    'iasListConcern',
    'redlistFull',
    'birdDir',
    'pollinators'
]].copy()

matrix_df.set_index('OTU_ID', inplace=True)

# (Optional) Fill NaNs with 0, if desired:
matrix_df.fillna(0, inplace=True)

# Save to file (as tab-separated)
matrix_df.to_csv("otutable.tsv", sep="\t")