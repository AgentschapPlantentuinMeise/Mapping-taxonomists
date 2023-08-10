import pandas as pd
import glob
import os
# custom packages
import taxonomy


# PARSE ARTICLES FOR TAXONOMIC SUBJECTS
eu_articles = pd.read_pickle("../../data/interim/eu_filtered_articles.pkl")

# convert abstract to text for every article
abstracts = []

for article in eu_articles.itertuples():
    if article.abstract_inverted_index: # check if abstract is indexed
        abstract_full_text = taxonomy.inverted_index_to_text(article.abstract_inverted_index)
        abstracts.append(abstract_full_text)
    else:
        abstracts.append(None)

eu_articles["abstract_full_text"] = pd.DataFrame(abstracts)
print("Abstract inverted indices converted to texts")

# parse every article abstract and title for mentions of recorded species
backbone = taxonomy.preprocess_backbone() # GBIF taxonomic backbone
eu_articles = taxonomy.parse_for_taxonomy(eu_articles, backbone)

eu_articles.to_pickle("../../data/processed/european_taxonomic_articles_with_subjects.pkl")
eu_articles.to_csv("../../data/processed/european_taxonomic_articles_with_subjects.tsv", sep="\t")
print("European taxonomic articles parsed for taxonomic subjects. Results in data/processed/european_taxonomic_articles.tsv.")
 