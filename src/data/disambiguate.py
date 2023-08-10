import pandas as pd
import numpy as np
import time


# PREPROCESSING

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
levels = ["genus", "family", "order", "class", "phylum", "kingdom"]
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
# get everyone whose truncated name occurs more than once
#duplicates = authors[authors.duplicated(subset="author_display_name", keep=False)]
duplicates = authors[authors.duplicated(subset=["truncatedName"], keep=False)]


# emergency meeting: go over every duplicated name
true_people = []

#for name in set(duplicates["author_display_name"]): 
for name in set(duplicates["truncatedName"]):
    # get all trund names that are exact string matches to this name
    #same_names = duplicates[duplicates["author_display_name"]==name]
    same_names = duplicates[duplicates["truncatedName"]==name]
    
    for person in same_names.itertuples():
        # check institution first
        # this way, even authors without known expertise can be disambiguated first
        person_ids = [person.Index,]
        orders = person.order.copy()
        institutions = [person.inst_id,]
        
        for cousin in same_names.itertuples():
            # if they work at the same institution, they're probably the same person
            if cousin.inst_id in institutions:
                person_ids.append(cousin.Index)
                orders.extend(cousin.order)
                institutions.append(cousin.inst_id)
                
                # try if anyone else looks like this person
                for second_cousin in same_names.itertuples():
                    if second_cousin.inst_id in institutions:
                        person_ids.append(second_cousin.Index)
                        orders.extend(second_cousin.order)    
                        institutions.append(second_cousin.inst_id)
                        # we could go on...
        
        # check institutions and taxonomic expertise second, simultaneously
        if person.species_subject != list():
            for cousin in same_names.itertuples():
                if len(set(orders).intersection(set(cousin.order))) > 0 or cousin.inst_id in institutions:
                    person_ids.append(cousin.Index)
                    orders.extend(cousin.order)
                    institutions.append(cousin.inst_id)
                    # try if anyone else looks like this person
                    for second_cousin in same_names.itertuples():
                        if len(set(orders).intersection(second_cousin.order)) > 0 \
    or second_cousin.inst_id in institutions:
                            person_ids.append(second_cousin.Index)
                            orders.extend(second_cousin.order)    
                            institutions.append(second_cousin.inst_id)
                            # we could go on...
        
        person_ids = set(person_ids)
        if person_ids not in true_people:
            true_people.append(person_ids)
            

#true_authors = authors[-(authors.duplicated(subset="author_display_name", keep=False))].reset_index()
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
