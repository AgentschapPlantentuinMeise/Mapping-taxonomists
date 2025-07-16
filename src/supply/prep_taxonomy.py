import pandas as pd
import numpy as np
import re
from pathlib import Path 

# openAlex gives only inverted index of the abstract 
# the: 1, 12, 14; quick: 2, 10, 51; brown: 3; dog: 4, 15; ...
# convert into full text 
def inverted_index_to_text(aii):
    """
    Convert OpenAlex abstract_inverted_index to full abstract text.
    
    Parameters:
        aii (dict): Inverted index as returned by OpenAlex.
    
    Returns:
        str: Full abstract string reconstructed from index.
    """
    abstract = 50000 * [None,]

    for word, indices in aii.items():
        for i in indices:
            # put each word in the inverted index in its place in the abstract
            abstract[i] =  word
    
    # from list to text 
    abstract = [j for j in abstract if j is not None]
    abstract = " ".join(abstract)
    return abstract


# reduce size of backbone for easier searching
def preprocess_backbone(path=None, no_blanks=False):
    if path is None:
        this_dir = Path(__file__).resolve().parent
        root_dir = this_dir.parents[1]
        path = root_dir / "data" / "external" / "backbone" / "Taxon.tsv"
    # GBIF taxonomic bakcbone
    # backbone = pd.read_csv(path, sep="\t", on_bad_lines='skip')
    backbone = pd.read_csv(path, sep="\t", 
                       dtype={'scientificNameAuthorship': 'str', 
                              'infraspecificEpithet': 'str',
                              'canonicalName': 'str',
                              'genericName': 'str',
                              'specificEpithet': 'str',
                              'namePublishedIn': 'str',
                              'taxonomicStatus': 'str',
                              'taxonRank': 'str',
                              'taxonRemarks': 'str',
                              'kingdom': 'str',
                              'phylum': 'str',
                              'family': 'str',
                              'genus': 'str'},
                       on_bad_lines='skip')

    # only Eukarya
    backbone = backbone[(backbone["kingdom"]=="Animalia") | 
                        (backbone["kingdom"]=="Plantae") |
                        (backbone["kingdom"]=="Fungi")]
    # include non-accepted species (synonyms etc), but not blank canonical names 
    backbone = backbone[np.logical_not(backbone["canonicalName"].isnull())].reset_index(drop=True)
    
    if no_blanks:
        backbone = backbone[np.logical_not(backbone["genus"].isnull())].reset_index(drop=True)
        backbone = backbone[np.logical_not(backbone["family"].isnull())].reset_index(drop=True)
        backbone = backbone[np.logical_not(backbone["order"].isnull())].reset_index(drop=True)
        backbone = backbone[np.logical_not(backbone["class"].isnull())].reset_index(drop=True)
        backbone = backbone[np.logical_not(backbone["phylum"].isnull())].reset_index(drop=True)
        backbone = backbone[np.logical_not(backbone["kingdom"].isnull())].reset_index(drop=True)

    backbone = backbone.drop_duplicates(ignore_index=True)
    return backbone


# look for canonical species names in article titles and abstracts
def parse_for_taxonomy(articles, backbone):
    all_names = set(backbone["canonicalName"])
    all_found_taxa = []
    
    for article in articles[["id", "title", "abstract_full_text"]].itertuples():
        found = False
        taxa_list = []

        # IN TITLE
        # find full species name
        if article.title:
            candidates = re.findall("[A-Z][a-z]+ [a-z]+", article.title) # anything that looks like "Abcd efg"
            for candidate in candidates:
                # check if Abcd efg matches a known species name
                if candidate not in taxa_list and candidate in all_names:
                    taxa_list.append(candidate); found = True

        if found:
            all_found_taxa.append(taxa_list)
            # find "G. species"
            for taxon in taxa_list:
                # search for first letter of already found genus + probable species name
                #candidates = re.findall(taxon[0]+"\. [a-z]+", article.title)
                candidates = re.findall(rf"{taxon[0]}\. [a-z]+", article.title)

                for candidate in candidates:
                    candidate = taxon.split()[0] + " " + candidate[3:]
                    # check if string is a species
                    if candidate not in taxa_list and candidate in all_names:
                        taxa_list.append(candidate)
            # do not check abstract if title has results
            continue

        # IN ABSTRACT
        # find full species name
        if article.abstract_full_text:
            candidates = re.findall("[A-Z][a-z]+ [a-z]+", article.abstract_full_text) 
            for candidate in candidates:
                if candidate not in taxa_list and candidate in all_names:
                    taxa_list.append(candidate); found = True

        # find "G. species"
        if found:
            for taxon in taxa_list:
                # search for first letter of already found genus + probable species name 
                #candidates.extend(re.findall(taxon[0]+"\. [a-z]+", article.abstract_full_text))
                candidates.extend(re.findall(rf"{taxon[0]}\. [a-z]+", article.abstract_full_text))

                for candidate in candidates:
                    candidate = taxon.split()[0] + " " + candidate[3:]
                    # check if string is a species
                    if candidate not in taxa_list and candidate in all_names:
                        taxa_list.append(candidate); found = True

        all_found_taxa.append(taxa_list)

    articles["species_subject"] = all_found_taxa 
    return articles


def species_to_tree(df, backbone):
    # make dictionary of genus, family, order, class, phylum, kingdom for every species
    seen_species = {}

    for species in backbone.itertuples():
        if species.canonicalName not in seen_species:
            seen_species[species.canonicalName] = list(species)[2:]
    
    # associate the full tree with a certain author or article
    genera, families, orders, classes, phyla, kingdoms, lineages = [], [], [], [], [], [], []

    for row in df.itertuples():
        genus, family, order, tclass, phylum, kingdom, lineage = [], [], [], [], [], [], []
                            # python won't allow class as a variable name

        for species in row.species_subject:
            if species in seen_species:
                genus.append(seen_species[species][-1])
                family.append(seen_species[species][-2])
                order.append(seen_species[species][-3])
                tclass.append(seen_species[species][-4])
                phylum.append(seen_species[species][-5])
                kingdom.append(seen_species[species][-6])
                
                lineage.append(seen_species[species][-6:])

        genera.append(set(genus))
        families.append(set(family))
        orders.append(set(order))
        classes.append(set(tclass))
        phyla.append(set(phylum))
        kingdoms.append(set(kingdom))
        lineages.append(lineage)

    df["genera_subjects"] = genera
    df["families_subjects"] = families
    df["orders_subjects"] = orders
    df["classes_subjects"] = classes
    df["phyla_subjects"] = phyla
    df["kingdoms_subjects"] = kingdoms
    df["lineages_subjects"] = lineages
    
    return df
