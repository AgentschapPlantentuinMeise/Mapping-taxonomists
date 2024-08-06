# get all European taxonomic articles from taxonomic journals
import pandas as pd
import glob
import os
# custom packages
import prep_authors


# GET AUTHORS
# global
articles = pd.read_pickle("../../data/processed/taxonomic_articles_with_subjects.pkl")
authors = prep_authors.get_authors(articles)
single_authors = prep_authors.get_single_authors(authors)

authors.to_pickle("../../data/interim/all_authors_of_taxonomic_articles.pkl")
single_authors.to_pickle("../../data/interim/single_authors_of_taxonomic_articles.pkl")

print("Authors extracted from articles. Results in data/processed/all_authors_of_taxonomic_articles.pkl and single_authors_of_taxonomic_articles.pkl.")


# european
#eu_articles = pd.read_pickle("../../data/processed/european_taxonomic_articles_with_subjects.pkl")

#authors = prep_authors.get_authors(eu_articles)
#single_authors = prep_authors.get_single_authors(authors)
country_authors = prep_authors.get_country_authors(authors)
single_eu_authors = prep_authors.get_single_authors(country_authors)

#authors.to_pickle("../../data/interim/all_authors_of_european_taxonomic_articles.pkl")
#single_authors.to_pickle("../../data/interim/single_authors_of_european_taxonomic_articles.pkl")

country_authors.to_pickle("../../data/interim/country_authors_with_all_taxonomic_articles.pkl")
single_eu_authors.to_pickle("../../data/interim/country_taxonomic_authors_no_duplicates.pkl")
single_eu_authors.to_csv("../../data/processed/country_taxonomic_authors_no_duplicates.tsv", sep="\t")

print("Authors extracted from articles from selected countries. Results in data/processed/country_taxonomic_authors_no_duplicates.tsv.")
