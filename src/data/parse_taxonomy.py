import pandas as pd
import glob
import os
# custom packages
import prep_taxonomy


# PARSE ARTICLES FOR TAXONOMIC SUBJECTS
articles = pd.read_pickle("../../data/interim/filtered_articles.pkl")

# convert abstract to text for every article
abstracts = []

for article in articles.itertuples():
    if article.abstract_inverted_index: # check if abstract is indexed
        abstract_full_text = prep_taxonomy.inverted_index_to_text(article.abstract_inverted_index)
        abstracts.append(abstract_full_text)
    else:
        abstracts.append(None)

articles["abstract_full_text"] = pd.DataFrame(abstracts)
print("Abstract inverted indices converted to texts")

# parse every article abstract and title for mentions of recorded species
backbone = prep_taxonomy.preprocess_backbone() # GBIF taxonomic backbone
articles = prep_taxonomy.parse_for_taxonomy(articles, backbone)

articles.to_pickle("../../data/processed/taxonomic_articles_with_subjects.pkl")
articles.to_csv("../../data/processed/taxonomic_articles_with_subjects.tsv", sep="\t")
print("Taxonomic articles parsed for taxonomic subjects. Results in data/processed/taxonomic_articles_with_subjects.tsv.")
 