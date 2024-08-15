import pandas as pd
import sys
import os
import glob

# Define paths
backbone_dir = os.path.join("..", "..", "data", "external", "backbone")
backbone_file = os.path.join(backbone_dir, "Taxon.tsv")

# check if these directories exist, or create them

# Ensure necessary directories and files exist
if not os.path.exists(backbone_file):
    if not os.path.exists(backbone_dir):
        os.makedirs(backbone_dir)
    print("Download the GBIF taxonomic backbone and put it in data/external/backbone.")
    sys.exit()

if not os.path.exists("../../data/raw/articles"): os.makedirs("../../data/raw/articles")
if not os.path.exists("../../data/interim/keyword-filtered_articles"):
    os.makedirs("../../data/interim/keyword-filtered_articles")
if not os.path.exists("../../data/processed"): os.makedirs("../../data/processed")

# clear directory
files = glob.glob("../../data/raw/articles/*")
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

with open("disambiguate.py") as f:
    exec(f.read())

