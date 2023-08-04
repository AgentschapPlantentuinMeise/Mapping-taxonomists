import pandas as pd
import pickle


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

# get all IUCN redlist species
allspecies = pd.read_csv("../../data/external/iucn-2022-1/distribution.txt", sep="\t", header=None)
allspecies_tax = pd.read_csv("../../data/external/iucn-2022-1/taxon.txt", sep="\t", header=None)

allspecies = allspecies[[0,3,4,5,6]] # leave out NaN columns
allspecies.columns = ["internalTaxonId", "redlistCategory", "authority", "scopes", "present"]
allspecies["internalTaxonId"] = allspecies["internalTaxonId"].astype("str") # convert internalTaxonId to strings
# allspecies_taxon["internalTaxonId"] is a column of string values (synonyms have IDs like 133722_1) 

allspecies_tax.columns = ["internalTaxonId", "scientificName", "kingdomName", "phylumName",
                          "orderName", "className", "familyName", "genusName", "speciesName",
                          "infraName", "infraType", "infraAuthority", "taxonStatus", "taxonIdAgain",
                          "authority_tax", "link"]

allspecies = pd.merge(allspecies, allspecies_tax, on="internalTaxonId") # provide redlist species with taxonomy
allspecies

# get species labelled as "taxonomic research needed"
taxresearch = pd.read_csv("../../data/external/IUCN_eu_region_tax_research_needed/assessments.csv")
taxresearch_tax = pd.read_csv("../../data/external/IUCN_eu_region_tax_research_needed/taxonomy.csv")

taxresearch = pd.merge(taxresearch, taxresearch_tax, on="internalTaxonId")
taxresearch

canonicalnames = []

for species in taxresearch.itertuples():
    if species.genusName == species.genusName and species.speciesName == species.speciesName:
        name = species.genusName + " " + species.speciesName
        canonicalnames.append(name)
    else:
        canonicalnames.append("")

taxresearch["canonicalName"] = canonicalnames

# count specialists per species (taxonomic research needed)
taxresearch["author_count"] = 0

for species, n_authors in specialists.items():
    if not taxresearch[taxresearch["canonicalName"]==species].empty:
        taxresearch.loc[taxresearch["canonicalName"]==species, "author_count"] = len(n_authors)

# match to gbif backbone
#gbif_taxonomy = pd.read_csv("../../data/external/backbone/Taxon.tsv", sep="\t", on_bad_lines='skip')

families = taxresearch[["kingdomName", "phylumName", "className", "orderName", 
                        "familyName"]].drop_duplicates(ignore_index=True)
families = families.dropna(subset="familyName").reset_index(drop=True)

families["needsResearch"] = 0
families["numberAuthors"] = 0

for species in taxresearch.itertuples():
    if str(species.familyName) == "nan" or str(species.genusName) == "nan":
        continue
    
    families.loc[(families["kingdomName"] == species.kingdomName) &
             (families["phylumName"] == species.phylumName) &
             (families["className"] == species.className) &
             (families["orderName"] == species.orderName) &
             (families["familyName"] == species.familyName),"needsResearch"] += 1
    
    families.loc[(families["kingdomName"] == species.kingdomName) &
             (families["phylumName"] == species.phylumName) &
             (families["className"] == species.className) &
             (families["orderName"] == species.orderName) &
             (families["familyName"] == species.familyName),"numberAuthors"] += species.author_count

families[["kingdomName", "needsResearch", "numberAuthors", 
          "phylumName", "className", "orderName", "familyName"]].to_excel("../../data/processed/krona_IUCN_redlist_needsresearch_authors.xlsx")
