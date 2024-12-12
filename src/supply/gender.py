import pandas as pd
import glob
import os
# custom packages
import download
import prep_articles
import prep_authors


with open("../../data/interim/journals_cumulative_path.txt", "r", encoding="utf8") as journals_file:
    journals = journals_file.readlines()
journals = [x[:-1] for x in journals][1:101]

oaids = []
articles=pd.read_pickle("../../data/processed/taxonomic_articles_with_subjects.pkl")

for journal in journals:
    oaids.append(articles[articles["source_display_name"]==journal].iloc[0]["source_id"])

# clear directory
files = glob.glob("../../data/raw/articles_50_years/*")
files.extend(glob.glob("../../data/interim/eu_keyword-filtered_50_years/*"))
for f in files:
    os.remove(f)

# ask OpenAlex (nicely) for all articles from these journals from 2013-2022
# can only use journals that have OpenAlex IDs and that are not dissolved
email = input("Enter e-mail address for OpenAlex API: ")
articles = []
n = 0; m = 0

# download recent articles from every taxonomic journal
for oaid in oaids:
    # search by confirmed OpenAlex ID (from OpenAlex itself or Wikidata) 
    journal_articles = download.request_works("primary_location.source.id:"+oaid, email, 
                                              from_date="1973-01-01", to_date="2023-12-31")
    n += len(journal_articles)
    articles.append(journal_articles)
    
    # split the dataframe every 10 000 articles
    if n >= 10000:
        print("Another "+str(n)+" articles found")
        # save raw data
        articles_df = pd.concat(articles, ignore_index=True)
        
        # save (European) keyword-filtered articles
        filtered_articles = prep_articles.filter_keywords(articles_df)
        eu_articles = prep_articles.filter_eu_articles(filtered_articles)
        
        filtered_articles.to_pickle("../../data/interim/keyword-filtered_50_years/articles"+str(m)+".pkl")
        eu_articles.to_pickle("../../data/interim/eu_keyword-filtered_50_years/eu_articles"+str(m)+".pkl")
        
        articles = []
        n = 0; m += 1

# same procedure for last articles
articles_df = pd.concat(articles, ignore_index=True)

filtered_articles = prep_articles.filter_keywords(articles_df)
eu_articles = prep_articles.filter_eu_articles(filtered_articles)

filtered_articles.to_pickle("../../data/interim/keyword-filtered_50_years/articles"+str(m)+".pkl")
eu_articles.to_pickle("../../data/interim/eu_keyword-filtered_50_years/eu_articles"+str(m)+".pkl")

# putting it together
articles = prep_articles.merge_pkls("../../data/interim/keyword-filtered_50_years/")
eu_articles = prep_articles.merge_pkls("../../data/interim/eu_keyword-filtered_50_years/")

# preprocess
articles = prep_articles.flatten_works(articles)
eu_articles = prep_articles.flatten_works(eu_articles)

# save final version of all (European) keyword-filtered taxonomic articles together
articles.to_pickle("../../data/interim/filtered_articles_50_years.pkl")
articles.to_csv("../../data/interim/filtered_articles_50_years.tsv", sep="\t")

eu_articles.to_pickle("../../data/interim/eu_filtered_articles_50_years.pkl")
eu_articles.to_csv("../../data/interim/eu_filtered_articles_50_years.tsv", sep="\t")

print("European taxonomic articles filtered. Results in data/interim/eu_filtered_articles_50_years.tsv.")


# GET AUTHORS
# european
authors = prep_authors.get_authors(eu_articles)
single_authors = prep_authors.get_single_authors(authors)
eu_authors = prep_authors.get_eu_authors(authors)
single_eu_authors = prep_authors.get_single_authors(eu_authors)

authors.to_pickle("../../data/interim/all_authors_of_european_taxonomic_articles_50_years.pkl")
single_authors.to_pickle("../../data/interim/single_authors_of_european_taxonomic_articles_50_years.pkl")

eu_authors.to_pickle("../../data/interim/european_authors_with_all_taxonomic_articles_50_years.pkl")
single_eu_authors.to_pickle("../../data/processed/european_taxonomic_authors_no_duplicates_50_years.pkl")
single_eu_authors.to_csv("../../data/processed/european_taxonomic_authors_no_duplicates_50_years.tsv", sep="\t")

print("Authors extracted from European articles. Results in data/processed/european_taxonomic_authors_no_duplicates_50_years.tsv.")
