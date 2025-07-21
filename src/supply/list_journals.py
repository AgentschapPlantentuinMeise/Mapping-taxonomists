# Make a list of taxonomic journals from Wikidata and OpenAlex
import pandas as pd
import requests
import time
import download
import prep_journals
from pathlib import Path
import json

# Resolve path to config.json (relative to this script)
config_path = Path(__file__).resolve().parents[2] / "config" / "config.json"

if not config_path.exists():
    raise FileNotFoundError(f"Config file not found at {config_path}")

with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)
    
root_dir = Path(config["root_dir"])
processed_dir = root_dir / "data" / "processed"

# GET JOURNALS
# 1. wikidata: journals with taxonomy (and similar concepts) as subject

query = download.build_sparql_query(["Q8269924", 	# taxonomy
                                     "Q11398", 		# biological classification
                                     "Q1138178", 	# plant taxonomy
                                     "Q1469725", 	# animal taxonomy
                                     "Q522190", 	# biological nomenclature
                                     "Q3310776", 	# botanical nomenclature
                                     "Q3343211"]) 	# zoological nomenclature
# query is too long, split in two
query2 = download.build_sparql_query(["Q3516404", 	# systematics
                                      "Q171184", 	# phylogenetics
                                      "Q115135896"])# animal phylogeny
# get the results of the query
results = download.get_sparql_results(query)
results2 = download.get_sparql_results(query2)
wikidata_subjects_results = pd.concat([results, results2])
wikidata_subjects_results["source"] = "Wikidata taxonomic subject"

print("Wikidata journals by subject: done", flush=True)


# 2. wikidata: journals with any IPNI or ZooBank Publication ID

query3 = """SELECT DISTINCT ?item ?itemLabel ?openAlexID ?issnL ?issn ?IPNIpubID ?ZooBankPubID ?dissolved ?country
WHERE {
    VALUES ?journaltype {wd:Q5633421 wd:Q737498}
    ?item wdt:P31/wdt:P279* ?journaltype .	# must be academic or scientific journal 
    {
    ?item p:P2008 ?zooid.
    ?zooid (ps:P2008) _:anyValueP2007. 		# with any ZooBank publication ID 
    }
    UNION
    {
    ?item p:P2007 ?ipniid.
    ?ipniid (ps:P2007) _:anyValueP2008. 	# with any IPNI publication ID
    }
    OPTIONAL{?item wdt:P10283 ?openAlexID}  	# include these columns if available
    OPTIONAL{?item wdt:P7363 ?issnL}
    OPTIONAL{?item wdt:P236 ?issn}
    OPTIONAL{?item wdt:P2008 ?IPNIpubID}
    OPTIONAL{?item wdt:P2007 ?ZooBankPubID}
    OPTIONAL{?item wdt:P576 ?dissolved}
    OPTIONAL{?item wdt:P495 ?country}

    SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}"""

ipni_zoobank_results = download.get_sparql_results(query3)
ipni_zoobank_results["source"] = "IPNI or ZooBank ID"
print("Wikidata journals by IPNI or ZooBank ID: done", flush=True)


# 3. openalex: sources associated with the taxonomy concept

#email = input("Enter e-mail address for OpenAlex API: ")
email = config.get("email")
if not email:
    raise ValueError("Email address for OpenAlex API is missing in config.json")
    
# C58642233 = Taxonomy (biology) Concept
openalex_results = download.request_sources("concepts.id:C58642233", email)
# only journals, no e-book platforms etc
openalex_results = openalex_results[openalex_results["type"]=="journal"].reset_index(drop=True)
openalex_results["source"] =  "OpenAlex taxonomy concept"

print("OpenAlex journals by Taxonomy in concepts: done", flush=True)


# HOMOGENIZE JOURNALS
print("Preprocessing data... ", flush=True)
# we need the following columns:
# title, wikidataURL, ISSN-L, IPNIpubID, ZooBankPubID, openAlexID, dissolvedYear, dissolvedBefore2013

# wikidata values are hidden in dictionaries: get them out
# and convert country Q-number to two-letter code and update old OpenAlex-IDs (e.g. V123 to S123)
prep_journals.get_values_wikidata(wikidata_subjects_results)
prep_journals.get_values_wikidata(ipni_zoobank_results)

# OpenAlex IDs
openalex_results = prep_journals.homogenize_openalex(openalex_results)

print(wikidata_subjects_results.columns)
print(ipni_zoobank_results.columns)
print(openalex_results.columns)

print(openalex_results)
# putting it together
journals = pd.concat([wikidata_subjects_results, ipni_zoobank_results, openalex_results], 
                     ignore_index=True)

# Rename using actual column names to avoid misalignment
journals = journals.rename(columns={
    "item": "wikidataURL",
    "itemLabel": "title",
    "openAlexID": "openAlexID",
    "issnL": "ISSN-L",
    "issn": "ISSN",
    "ZooBankPubID": "ZooBankPubID",
    "country": "country",
    "IPNIpubID": "IPNIpubID",
    "dissolved": "dissolvedYear",
})
#journals.columns = ["wikidataURL", "openAlexID", "ISSN-L", "ISSN", 
#                    "ZooBankPubID", "country", "title", "IPNIpubID", "dissolvedYear", "source"]

journals = journals[["title", "wikidataURL", "ISSN-L", "IPNIpubID", "ZooBankPubID",
                     "openAlexID", "dissolvedYear", "source"]]

print(journals.head())

# translate dissolved year to True/False
journals = prep_journals.dissolved_bool(journals)
print("done!", flush=True)

journals[["title", "wikidataURL", "ISSN-L", "IPNIpubID", "ZooBankPubID", "openAlexID", "dissolvedYear", 
          "dissolved", "source"]].to_csv(processed_dir / "journals.csv", index=False)
# remove duplicates with same wikidata ID and OpenALex ID
journals[["title", "wikidataURL", "ISSN-L", "openAlexID", "IPNIpubID", "ZooBankPubID", "dissolvedYear", 
          "dissolved", "source"]].drop_duplicates(
              subset=["wikidataURL", "openAlexID"],
              ignore_index=True
          ).to_csv(processed_dir / "journals_deduplicated.csv", index=False)

print("Journals saved in data/processed/journals_deduplicated.csv", flush=True)
