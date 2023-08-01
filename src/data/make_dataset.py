# get all European taxonomic articles from taxonomic journals
import pandas as pd
import download_from_openalex
import prep_articles
import glob
import os

# run make_list_journals.py first
# list of journals found in /data/processed
journals = pd.read_csv("../../data/processed/journals.csv")

# ask OpenAlex (nicely) for all articles from these journals from 2013-2022
# can only use journals that have OpenAlex IDs and that are not dissolved
oaids = list(set(journals[journals["dissolved"]!=True]["openAlexID"]))

# clear directory
files = glob.glob("../../data/raw/articles/*")
files.extend(glob.glob("../../data/interim/eu_keyword-filtered_articles/*")
for f in files:
    os.remove(f)

# get all articles from taxonomic journals
email = input("Enter e-mail address for OpenAlex API: ")
articles = []
n = 0
m = 0

for oaid in oaids:
    if oaid != oaid: # check if nan
        continue
    if oaid == "S202381698": # deal with PLOS ONE separately
        continue # (returns ~240 000 articles)
    
    # search by confirmed OpenAlex ID (from OpenAlex itself or Wikidata) 
    journal_articles = download.request_works("primary_location.source.id:"+oaid, email, to_date="2022-12-31")
    n += len(journal_articles)
    articles.append(journal_articles)
    
    # split the dataframe every 10 000 articles
    if n >= 10000:
        print("Another "+str(n)+" articles found")
        # save raw data
        articles_df = pd.concat(articles, ignore_index=True)
        articles_df.to_csv("../../data/raw/articles/articles"+str(m)+".tsv", sep="\t")
        
        # save European, keyword-filtered articles
        filtered_articles = prep_articles.filter_keywords(articles_df)
        eu_articles = prep_articles.filter_eu_articles(filtered_articles)
        
        eu_articles.to_pickle("../../data/interim/eu_keyword-filtered_articles/eu_articles"+str(m)+".pkl")
        #eu_articles.to_csv("../../data/interim/eu_keyword-filtered_articles/eu_articles"+str(m)+".tsv", sep="\t")
        
        articles = []
        n = 0
        m += 1
        
articles_df = pd.concat(articles, ignore_index=True)
articles_df.to_csv("../../data/raw/articles/articles"+str(m)+".tsv", sep="\t")

filtered_articles = prep_articles.filter_keywords(articles_df)
eu_articles = prep_articles.filter_eu_articles(filtered_articles)
eu_articles.to_pickle("../../data/interim/eu_keyword-filtered_articles/eu_articles"+str(m)+".pkl")
#eu_articles.to_csv("../../data/interim/eu_keyword-filtered_articles/eu_articles"+str(m)+".tsv", sep="\t")

