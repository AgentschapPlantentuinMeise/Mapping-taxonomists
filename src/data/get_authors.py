# get all European taxonomic articles from taxonomic journals
import pandas as pd
import glob
import os
# custom packages
import prep_authors


# GET AUTHORS
eu_articles = pd.read_pickle("../../data/processed/european_taxonomic_articles_with_subjects.pkl")

authors = prep_authors.get_authors(eu_articles)
eu_authors = prep_authors.get_eu_authors(authors)
single_eu_authors = prep_authors.get_single_authors(eu_authors)

authors.to_pickle("../../data/interim/authors_of_european_taxonomic_articles.pkl")
eu_authors.to_pickle("../../data/interim/european_authors_with_all_taxonomic_articles.pkl")
single_eu_authors.to_pickle("../../data/interim/european_taxonomic_authors_no_duplicates.pkl")
single_eu_authors.to_csv("../../data/processed/european_taxonomic_authors_no_duplicates.tsv", sep="\t")

print("European authors extracted from articles. Results in data/processed/european_taxonomic_authors_no_duplicates.tsv.")
