import pandas as pd
import glob
import os
# custom packages
import prep_taxonomy

from pathlib import Path
import pandas as pd

# Resolve absolute paths
this_dir = Path(__file__).resolve().parent
root_dir = this_dir.parents[1]
interim_dir = root_dir / "data" / "interim" / "keyword-filtered_articles"

# Full path to filtered_articles.pkl
filtered_articles_path = interim_dir / "filtered_articles.pkl"

# PARSE ARTICLES FOR TAXONOMIC SUBJECTS
articles = pd.read_pickle(filtered_articles_path)

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

# >>> CLEAN UP CARRIAGE RETURNS AND NEWLINES HERE <<<
articles["abstract_full_text"] = (
    articles["abstract_full_text"]
    .astype(str)                            # ensure string type
    .str.replace(r"[\r\n]+", " ", regex=True)  # replace any \r or \n with a space
    .str.strip()                                # remove leading/trailing spaces
)

# parse every article abstract and title for mentions of recorded species
backbone = prep_taxonomy.preprocess_backbone() # GBIF taxonomic backbone
articles = prep_taxonomy.parse_for_taxonomy(articles, backbone)

processed_dir = root_dir / "data" / "processed"
processed_dir.mkdir(parents=True, exist_ok=True)  # make sure directory exists

articles.to_pickle(processed_dir / "taxonomic_articles_with_subjects.pkl")
articles.to_csv(processed_dir / "taxonomic_articles_with_subjects.tsv", sep="\t")
print("Taxonomic articles parsed for taxonomic subjects. Results in data/processed/taxonomic_articles_with_subjects.tsv.")
 