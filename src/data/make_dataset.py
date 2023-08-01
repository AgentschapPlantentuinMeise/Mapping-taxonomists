# get all European taxonomic articles from taxonomic journals
import pandas as pd
import glob
import os

# custom
import download
import prep_articles
import taxonomy


# run make_list_journals.py first
# list of journals found in /data/processed
journals = pd.read_csv("../../data/processed/journals.csv")

# ask OpenAlex (nicely) for all articles from these journals from 2013-2022
# can only use journals that have OpenAlex IDs and that are not dissolved
oaids = list(set(journals[journals["dissolved"]!=True]["openAlexID"]))

# clear directory
files = glob.glob("../../data/raw/articles/*")
files.extend(glob.glob("../../data/interim/eu_keyword-filtered_articles/*"))
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

eu_articles = pd.concat(eu_articles, ignore_index=True)
eu_articles.to_pickle("../../data/interim/eu_filtered_articles.pkl")
eu_articles.to_csv("../../data/interim/eu_filtered_articles.tsv", sep="\t")             

eu_articles = pd.read_pickle("../../data/interim/eu_filtered_articles.pkl")

# parse articles for taxonomic information

# convert abstract to text for every article
abstracts = []
# convert abstract to text for every article
for article in eu_articles.itertuples():
    if article.abstract_inverted_index: # check if abstract is indexed
        abstract_full_text = taxonomy.inverted_index_to_text(article.abstract_inverted_index)
        abstracts.append(abstract_full_text)
    else:
        abstracts.append(None)

eu_articles["abstract_full_text"] = pd.DataFrame(abstracts)
print("Abstract inverted indices converted to texts")

backbone = taxonomy.preprocess_backbone()
eu_articles = taxonomy.parse_for_taxonomy(eu_articles, backbone)
eu_articles = prep_articles.flatten_works(eu_articles)

eu_articles.to_pickle("../../data/processed/european_taxonomic_articles.pkl")
eu_articles.to_csv("../../data/processed/european_taxonomic_articles.tsv", sep="\t")
print("European taxonomic articles filtered and parsed. Results in /data/processed.")
