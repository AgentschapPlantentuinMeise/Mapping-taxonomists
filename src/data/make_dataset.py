import pandas as pd
import os
import glob

# check if these directories exist, or create them
if not os.path.exists("../../data/external/backbone/Taxon.tsv"):
    os.makedirs("../../data/external/backbone")
    print("Download the GBIF taxonomic backbone and put it in data/external/backbone.")
    exit()

if not os.path.exists("../../data/raw/articles"): os.makedirs("../../data/raw/articles")
if not os.path.exists("../../data/interim/eu_keywords-filtered_articles"):
    os.makedirs("../../data/interim/eu_keywords-filtered_articles")
if not os.path.exists("../../data/processed"): os.makedirs("../../data/processed")

# clear directory
files = glob.glob("../../data/raw/articles/*")
files.extend(glob.glob("../../data/interim/eu_keyword-filtered_articles/*"))
for f in files:
    os.remove(f)

# run scripts consecutively  
with open("list_journals.py") as f:
    exec(f.read())

with open("get_articles.py") as f:
    exec(f.read())

with open("parse_taxonomy.py") as f:
    exec(f.read())
    
with open("get_authors.py") as f:
    exec(f.read())
