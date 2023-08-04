import pandas as pd
import numpy as np
import time


# we have articles with the species 
eu_authors = pd.read_csv("../../data/processed/european_taxonomic_authors_no_duplicates.tsv", sep="\t")

authors_taxa = eu_authors[["author_id", 
                           "author_display_name",
                           "orcid"]].drop_duplicates(subset="author_id", ignore_index=True)
authors_taxa = authors_taxa.set_index("author_id")
authors_taxa["species_subjects"] = [list() for x in range(len(authors_taxa.index))]

for author_article in eu_authors.itertuples():
    authors_taxa.loc[author_article.author_id, "species_subjects"].extend(author_article.species_subject)

authors_taxa['species_subjects'] = authors_taxa.apply(lambda row: set(row['species_subjects']), axis=1)


# GBIF taxonomic backbone
backbone = pd.read_csv("../../data/external/backbone/Taxon.tsv", sep="\t", on_bad_lines='skip')

# reduce size of backbone for easier searching
backbone = backbone[backbone["taxonomicStatus"]!="doubtful"]
backbone = backbone[["canonicalName", "genus", "family", "order", "class", "phylum", "kingdom"]]
# remove taxa with no known species name, genus, family, or kingdom
backbone = backbone[np.logical_not(backbone["canonicalName"].isnull())].reset_index(drop=True)
backbone = backbone[np.logical_not(backbone["genus"].isnull())].reset_index(drop=True)
backbone = backbone[np.logical_not(backbone["family"].isnull())].reset_index(drop=True)
backbone = backbone[np.logical_not(backbone["kingdom"].isnull())].reset_index(drop=True)

backbone = backbone.drop_duplicates(ignore_index=True)


seen_species = {}

for species in backbone.itertuples():
    if species.canonicalName not in seen_species:
        seen_species[species.canonicalName] = list(species)[2:]
    

genera = []
families = []
orders = []
classes = []
phyla = []
kingdoms = []

for author in authors_taxa.itertuples():
    genus, family, order, classb, phylum, kingdom = [], [], [], [], [], []
    
    for species in author.species_subjects:
        if species in seen_species:
            genus.append(seen_species[species][0])
            family.append(seen_species[species][1])
            order.append(seen_species[species][2])
            classb.append(seen_species[species][3])
            phylum.append(seen_species[species][4])
            kingdom.append(seen_species[species][5])
    
    genera.append(set(genus))
    families.append(set(family))
    orders.append(set(order))
    classes.append(set(classb))
    phyla.append(set(phylum))
    kingdoms.append(set(kingdom))
        
authors_taxa["genera_subjects"] = genera
authors_taxa["families_subjects"] = families
authors_taxa["orders_subjects"] = orders
authors_taxa["classes_subjects"] = classes
authors_taxa["phyla_subjects"] = phyla
authors_taxa["kingdoms_subjects"] = kingdoms


authors_id = eu_authors.set_index("author_id")

# get all duplicated authors (keep=False)
duplicated = authors_taxa[authors_taxa.duplicated(subset="author_display_name", keep=False)]
true_people = []

# emergency meeting: go over every name
for name in set(duplicated["author_display_name"]):
    # get all names that are exact string matches
    same_names = duplicated[duplicated["author_display_name"]==name]
    
    for person in same_names.itertuples():
        # check institution first
        person_ids = {person.Index,}
        orders = set(person.orders_subjects)
        institution = authors_id.loc[person.Index, "inst_display_name"]
        
        for cousin in same_names.itertuples():
            # if they have worked at the same institution
            if len(set(institution).intersection(set(authors_id.loc[cousin.Index, "inst_display_name"]))) > 0:
                person_ids.add(cousin.Index)
                orders.update(cousin.orders_subjects)
                # try if anyone else looks like this person
                for second_cousin in same_names.itertuples():
                    if len(set(institution).intersection(set(authors_id.loc[second_cousin.Index, "inst_display_name"]))) > 0:
                        person_ids.add(second_cousin.Index)
                        orders.update(second_cousin.orders_subjects)                    
                        # we could go on...
                        
        if person.species_subjects != set():
            # check taxonomic focus next
            for cousin in same_names.itertuples():
                if len(orders.intersection(cousin.orders_subjects)) > 0 \
    or len(set(institution).intersection(set(authors_id.loc[cousin.Index, "inst_display_name"]))) > 0:
                    person_ids.add(cousin.Index)
                    orders.update(cousin.orders_subjects)
                    # try if anyone else looks like this person
                    for second_cousin in same_names.itertuples():
                        if len(orders.intersection(second_cousin.orders_subjects)) > 0 \
    or len(set(institution).intersection(set(authors_id.loc[second_cousin.Index, "inst_display_name"]))) > 0:
                            person_ids.add(second_cousin.Index)
                            orders.update(second_cousin.orders_subjects)                    
                            # we could go on...

        if person_ids not in true_people:
            true_people.append(person_ids)

                
true_authors = authors_taxa[-(authors_taxa.duplicated(subset="author_display_name", keep=False))].reset_index()

for person in true_people:
    if len(person) > 0:
        orcids = []
        species_subjects = set()
        genera_subjects = set()
        families_subjects = set()
        orders_subjects = set()
        classes_subjects = set()
        phyla_subjects = set()
        kingdoms_subjects = set()
        
        for duplicate in person:
            data = authors_taxa.loc[duplicate]
            orcids.append(data["orcid"])
            species_subjects.update(data["species_subjects"])
            genera_subjects.update(data["genera_subjects"])
            families_subjects.update(data["families_subjects"])
            orders_subjects.update(data["orders_subjects"])
            classes_subjects.update(data["classes_subjects"])
            phyla_subjects.update(data["phyla_subjects"])
            kingdoms_subjects.update(data["kingdoms_subjects"])
        
        if len(orcids) ==1:
            orcids = orcids[0]
        elif all(x is None for x in orcids):
            orcids = None
        else:
            orcids = [x for x in orcids if x is not None]
            if len(orcids) == 1:
                orcids = orcids[0]
        
        true_authors.loc[len(true_authors)] = [person,
            authors_taxa.loc[list(person)[0], "author_display_name"],
                                    orcids,
                                    species_subjects,
                                    genera_subjects,
                                    families_subjects,
                                    orders_subjects,
                                    classes_subjects,
                                    phyla_subjects,
                                    kingdoms_subjects]

true_authors.to_pickle("../../data/processed/european_authors_disambiguated.pkl")
true_authors.to_csv("../../data/processed/european_authors_disambiguated.tsv", sep="\t")
