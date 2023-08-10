import pandas as pd
import numpy as np
import time


# PREPROCESSING
levels = ["genus", "family", "order", "class", "phylum", "kingdom"]

## AUTHORS
authors = pd.read_pickle("../../data/interim/european_taxonomic_authors_no_duplicates.pkl")
# less columns and author ID as index quicken processing
authors = authors[["author_id", "author_display_name", "orcid",
                   "inst_id", "inst_display_name",  "species_subject"]]
authors = authors.set_index("author_id")

# get initial first name + last name for every author
truncated_names = []

for author in authors.itertuples():
    first_initial = author.author_display_name[0]
    last_name = author.author_display_name.split(" ")[-1]
    truncated_names.append(first_initial + " " + last_name)
    
authors["truncatedName"] = truncated_names


## GBIF TAXONOMIC BACKBONE
backbone = pd.read_csv("../../data/external/backbone/Taxon.tsv", sep="\t", on_bad_lines='skip')
# reduce size of backbone for easier searching
backbone = backbone[backbone["taxonomicStatus"]!="doubtful"]
backbone = backbone[["canonicalName",] + levels]
# remove taxa with no known species name, genus, family,...
backbone = backbone.dropna().drop_duplicates(ignore_index=True).reset_index(drop=True)

# backbone to dictionary for quicker processing
seen_species = {}

for species in backbone.itertuples():
    if species.canonicalName not in seen_species:
        seen_species[species.canonicalName] = list(species)[2:]


## LINK AUTHORS TO BACKBONE
# start with empty list for every taxonomic level 
for level in levels:
    authors[level] = [list() for x in range(len(authors.index))]
    
# for every author, break down every species they study into different taxonomic levels
for i, author in authors.iterrows():
    for species in author["species_subject"]:
        if species in seen_species:
            for l, level in enumerate(levels):
                # get genus (or family, order,...) name according to GBIF
                taxon_name = seen_species[species][l]
                # add this genus (etc) to the list of genera studied by the author (no duplicates)
                if taxon_name not in author[level]:
                    authors.loc[i, level].append(taxon_name)
                    

# DISAMBIGUATE
def match(a, b):
    same = False
    # if no known orders for one of them, just use institution 
    if a.order == [] or b.order == []:
        if a.inst_id == b.inst_id:
            same = True
    # if both have known orders, orders and institution must match
    else:
        if a.inst_id == b.inst_id and len(set(a.order).intersection(set(b.order))) > 0:
            same = True
    
    return same


def cluster(matches):
    clusters = []
    
    for match in matches:
        # check if it matches any existing groups
        match_with_groups = []
        for i, group in enumerate(clusters):
            if len(set(match).intersection(set(group))) > 0:
                match_with_groups.append(i)
        
        # if it fits with no existing group, add it by itself
        if len(match_with_groups) == 0:
            clusters.append(match)
        # if it fits with one existing group, add it to that group
        elif len(match_with_groups) == 1:
            clusters[match_with_groups[0]].extend(match)
        # if it fits with multiple groups, mash those groups together
        else:
            print(clusters) # apparently this never happens
            supergroup = []
            # remove each group and add its contents to the new supergroup
            for j in match_with_groups.sort(reverse=True):
                supergroup.extend(clusters.pop(j))
            supergroup.extend(match)
            clusters.append(supergroup)
            print(clusters)
    
    # turn into a list of sets to get unique values
    clusters = [set(x) for x in clusters] 
    return clusters


# emergency meeting: go over every duplicated name
true_people = []
duplicates = authors[authors.duplicated(subset=["truncatedName"], keep=False)]

for name in set(duplicates["truncatedName"]):
    # get all trund names that are exact string matches to this name
    #same_names = duplicates[duplicates["author_display_name"]==name]
    same_names = duplicates[duplicates["truncatedName"]==name]
    matches = []
    
    for person_a in same_names.itertuples():
        aliases = [person_a.Index,]
        
        for person_b in same_names.itertuples():
            if match(person_a, person_b) and person_a.Index!=person_b.Index:
                aliases.append(person_b.Index)
                
        matches.append(aliases)

    true_people.extend(cluster(matches))


true_authors = authors[-(authors.duplicated(subset="truncatedName", keep=False))].reset_index()

merged_people = []
m = 1

def collect_values(df, person_ids, column):
    if len(person_ids) > 0:
        values = []
        
        for duplicate in person_ids:
            imposter = df.loc[duplicate]
            if imposter[column] not in values and imposter[column] != None:
                if column in levels or column == "species_subject":
                    values.extend(imposter[column])
                else:
                    values.append(imposter[column])
                
    else:
        values = df.loc[person_ids, column]

    values = set(values)
    if len(values)==1:
        values = list(values)[0]
        
    return values

person_ids = []
m = 1

for person in true_people:
    row = [person,]
    for column in true_authors.columns[1:]:
        answer = collect_values(authors, person, column)
        row.append(answer)
        
    merged_people.append(authors.loc[list(person)].reset_index())
    merged_people[-1]["groupNr"] = m
    m += 1
    
    true_authors.loc[len(true_authors)] = row
    
    
merged_df = pd.concat(merged_people, ignore_index=True)        
merged_df.to_csv("../../data/interim/merged_people_truncated.csv")

true_authors.to_pickle("../../data/processed/european_authors_disambiguated_truncated.pkl")
true_authors.to_csv("../../data/processed/european_authors_disambiguated_truncated.tsv", sep="\t")
