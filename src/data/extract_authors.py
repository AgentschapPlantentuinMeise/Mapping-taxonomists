import pandas as pd
import pickle
import glob


articles = []

files = glob.glob("../../data/interim/eu_keyword-filtered_articles/*")
for f in files:
    if f[-4:]==".pkl":
        articles.append(pd.read_pickle(f))
        
articles = pd.concat(articles, ignore_index=True)
articles.to_pickle("../../data/interim/eu_filtered_articles.pkl")
articles.to_csv("../../data/interim/eu_filtered_articles.tsv", sep="\t")

# do some taxonomy first...
# GBIF taxonomic backbone
backbone = pd.read_csv("./backbone/Taxon.tsv", sep="\t", on_bad_lines='skip')

# openAlex gives only inverted index of the abstract 
# the: 1, 12, 14; quick: 2, 10, 51; brown: 3; dog: 4, 15; ...
# convert into full text 
def inverted_index_to_text(aii):
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
backbone = backbone[backbone["taxonomicStatus"]!="doubtful"]
backbone = backbone[["canonicalName", "genus", "family", "order", "class", "phylum", "kingdom"]]
# remove taxa with no known species name, genus, family, or kingdom
backbone = backbone[np.logical_not(backbone["canonicalName"].isnull())].reset_index(drop=True)
backbone = backbone[np.logical_not(backbone["genus"].isnull())].reset_index(drop=True)
backbone = backbone[np.logical_not(backbone["family"].isnull())].reset_index(drop=True)
backbone = backbone[np.logical_not(backbone["kingdom"].isnull())].reset_index(drop=True)

backbone = backbone.drop_duplicates(ignore_index=True)
backbone


seen_species = {}

for species in backbone.itertuples():
    if species.canonicalName not in seen_species:
        seen_species[species.canonicalName] = list(species)[2:]
    
seen_species


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



eu_tax_articles = openalex.flatten_works(eu_tax_articles)

authors_eu_tax = openalex.get_authors(eu_tax_articles)

only_eu_authors = openalex.get_eu_authors(authors_eu_tax)

single_eu_authors = openalex.get_single_authors(only_eu_authors).reset_index(drop=True)

only_eu_authors.to_pickle("./data/EU27_authors_with_all_taxonomic_articles.pkl")
single_eu_authors.to_pickle("./data/EU27_authors_taxonomic_articles_no_duplicates.pkl")
