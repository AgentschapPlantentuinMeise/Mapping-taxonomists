import pandas as pd
import download
import json
from datetime import datetime

# Load configuration
with open("../../config.json", "r") as config_file:
    config = json.load(config_file)

# Extract dates
from_date = config.get("from_date", "2014-01-01")  # Default to 2014-01-01 if not provided

from_date_year = datetime.strptime(from_date, "%Y-%m-%d").year-1

# wikidata objects of countries often have a ISO 3166-1 alpha-2 code (P297): 
# use this unambiguous code instead of the wikidata ID, just like OpenALex
def get_country_codes():
    query = """SELECT DISTINCT ?item ?itemLabel ?twoLetterCode WHERE {
  ?item wdt:P297 ?twoLetterCode
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE]". }
  {
    SELECT DISTINCT ?item WHERE {
      ?item p:P31 ?statement0.
      ?statement0 (ps:P31/(wdt:P279*)) wd:Q6256.
      ?item p:P297 ?statement1.
      ?statement1 (ps:P297) _:anyValueP297.
    }
  }
}"""
    results = download.get_sparql_results(query)
    
    countries = {}
    for country in results.itertuples():
        try:
            countries[country.item["value"]] = country.twoLetterCode["value"]
        except KeyError as e:
            print(f"KeyError while processing country data: {e}")
    return countries

# Wikidata query results are tables with most values locked in dictionaries: get them out 
def get_values_wikidata(df):
    # get two-letter country code for every country
    countries = get_country_codes()
    # replace every column with the values locked inside it
    for column in df.columns:
        values = []
        for x in df[column]:
            # first some exceptions:
            if column == "dissolved":
                if x==x: # if there is a "dissolved" value,
                    # get only the year of dissolvement, not entire date
                    values.append(x["value"][:4])
                else:
                    values.append(None)
            
            elif column == "openAlexID":
                if x==x: # update OpenAlexID from their old "venue" IDs to new "source" IDs
                    # e.g. V123 becomes S123
                    values.append("S"+x["value"][1:])
                else:
                    values.append(None)
                    
            elif column == "country":
                if x==x and x["value"] in countries: # replace country with two-letter code
                    values.append(countries[x["value"]])
                else:
                    values.append(None)
            
            elif column == "source":
                values = df.source 
                
            # for most columns: just get the value out of the dictionary
            elif x==x:
                values.append(x["value"])
            else:
                values.append(None)
                
        # replace old column with its true values
        df[column] = values
        

# homogenize OpenAlex table with Wikidata tables
def homogenize_openalex(df):
    df["dissolved"] = None
    df["IPNIpubID"] = None
    df["ZooBankPubID"] = None
    
    for i, journal in df.iterrows():
        # OpenAlex ID should be just the S-number, not the URL
        df.loc[i, "openAlexID"] = journal["id"].split("/")[-1]
        # getting wikidata ID if available
        if "wikidata" in journal["ids"]:
            df.loc[i, "item"] = journal["ids"]["wikidata"]
            
        # finding the latest year when they published articles
        found = False
        # start at most recent year
        n = 0
        while not found:
            # if no data is provided...
            if len(journal.counts_by_year) == 0:
                found = True
            # if they never published more than zero articles...
            elif n >= len(journal.counts_by_year):
                df.loc[i, "dissolved"] = "before "+str(journal.counts_by_year[n-1]["year"])
                found = True
            # record most recent year when there were more than zero articles
            elif journal.counts_by_year[n]["works_count"] != 0:
                df.loc[i, "dissolved"] = journal.counts_by_year[n]["year"]
                found = True
            # try next year
            else:
                n += 1
    
    # select and rename columns analogous to wikidata
    df = df[["item", "openAlexID", "issn_l", "issn", "country_code",
             "display_name", "IPNIpubID", "ZooBankPubID", "dissolved", "source"]]
    df.columns = ["item", "openAlexID", "issnL", "issn", "country",
                  "itemLabel", "IPNIpubID", "ZooBankPubID", "dissolved", "source"]
    return df


def dissolved_bool(journals):
    dissolveds = []

    for journal in journals.itertuples():
        if journal.dissolvedYear == None:
            dissolveds.append(None)
        # if year of dissolvement is 2013 or later, the journal has not been dissolved
        elif isinstance(journal.dissolvedYear, int): 
            if journal.dissolvedYear >= from_date_year:
                dissolveds.append(False)
            else:
                dissolveds.append(True)

        elif isinstance(journal.dissolvedYear, str):
            # "before ..."
            if journal.dissolvedYear[:6] == "before":
                # if it was dissolved before 2013, it is unavailable in the last 10 years
                if int(journal.dissolvedYear[-4:]) <= from_date_year:
                    dissolveds.append(True)
                else: # if it was dissolved before e.g. 2017, we don't know
                    dissolveds.append(None)
            # if value is a string but should be an integer
            elif int(journal.dissolvedYear) >= from_date_year:
                dissolveds.append(False)
            elif int(journal.dissolvedYear) < from_date_year:
                dissolveds.append(True)
            else:
                dissolveds.append(None)

    journals["dissolved"] = dissolveds
    return journals
