# Make a list of taxonomic journals from Wikidata and OpenAlex

import pandas as pd
import sys
import requests
from SPARQLWrapper import SPARQLWrapper, JSON


# GET DATA 

# BUILD SPARQL QUERIES FOR MULTIPLE SUBJECTS
def build_sparql_query(subjects):
    # instance of (P31) scientific (Q5633421) or academic journal (Q737498)
    query_begin = """SELECT DISTINCT ?item ?itemLabel ?openAlexID ?issnL ?issn 
    ?IPNIpubID ?ZooBankPubID ?dissolved ?country
WHERE {
    VALUES ?journaltype {wd:Q5633421 wd:Q737498}
    ?item wdt:P31/wdt:P279* ?journaltype .""" 
    
    # include, if available: OpenAlex, IPNI and ZooBank Publication IDs, ISSN and ISSN-Ls, 
    # when (if ever) the journal was dissolved, and country of publication
    query_end = """
    OPTIONAL{?item wdt:P10283 ?openAlexID}
    OPTIONAL{?item wdt:P7363 ?issnL}
    OPTIONAL{?item wdt:P236 ?issn}
    OPTIONAL{?item wdt:P2008 ?IPNIpubID}
    OPTIONAL{?item wdt:P2007 ?ZooBankPubID}
    OPTIONAL{?item wdt:P576 ?dissolved}
    OPTIONAL{?item wdt:P495 ?country}
    
    SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}"""
    
    # add specified requirements (taxonomy,...) for field of work (P101) or main subject (P921)
    for i, subject in enumerate(subjects):
        i = 2 + i*2
        addition = """
        {
        ?item p:P921 ?statement""" + str(i) + """.
        ?statement""" + str(i) + """ (ps:P921/(wdt:P279*)) wd:""" + subject + """.
      }
      UNION
      {
        ?item p:P101 ?statement""" + str(i+1) + """.
        ?statement""" + str(i+1) + """ (ps:P101/(wdt:P279*)) wd:""" + subject + """.
      }"""
        if i != 2:
            addition = """
      UNION""" + addition
        
        query_begin += addition
    
    # paste query together
    query = query_begin + query_end
    return query


# GET RESULTS OF SPARQLE QUERY (code from WikiData's query service)
endpoint_url = "https://query.wikidata.org/sparql"

def get_sparql_results(query, endpoint_url=endpoint_url):
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    # TODO adjust user agent; see https://w.wiki/CX6
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    
    results = sparql.query().convert()
    return pd.DataFrame.from_dict(results["results"]["bindings"])


# GET ALL SOURCES (JOURNALS) FROM OPENALEX API WITH SPECIFIED REQUIREMENTS
def request_sources(filter_string, email):
    # build query (e-mail included for "polite pool")
    query = "https://api.openalex.org/sources?per-page=200&filter="+filter_string+"&mailto="+email
            
    # open persistent session to shorten processing time between requests
    s = requests.Session()
    # FIRST PAGE
    sources = s.get(query+"&cursor=*")
    next_sources = sources.json()
    next_cursor = next_sources["meta"]["next_cursor"]
    sources_results = next_sources["results"]
    
    # RETRIEVE ALL PAGES
    while next_sources["meta"]["next_cursor"] != None:
        # get next page
        next_sources = s.get(query+"&cursor="+next_cursor)
        next_sources = next_sources.json()
        next_cursor = next_sources["meta"]["next_cursor"] # remember next cursor
        sources_results.extend(next_sources["results"])
    
    sources_df = pd.DataFrame.from_dict(sources_results)
    return sources_df


# PREPROCESSING 

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
    results = get_sparql_results(query)
    
    countries = {}
    for country in results.itertuples():
        countries[country.item["value"]] = country.twoLetterCode["value"]
    return countries

# Wikidata query results are tables with most values locked in dictionaries: get them out 
def get_values_wikidata(df):
    # get two-letter country code for each country
    countries = get_country_codes()
#    country_set = {x["value"] for x in df["country"] if x==x}
#    for country in country_set:
#        if country==country:
            # get wikidata Q-number from URL and retrieve the object's two-letter country code
#            countries[country] = get_country_code(country.split("/")[-1])

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
def homogenize_oa(df):
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
            if journal.dissolvedYear >= 2013:
                dissolveds.append(False)
            else:
                dissolveds.append(True)

        elif isinstance(journal.dissolvedYear, str):
            # "before ..."
            if journal.dissolvedYear[:6] == "before":
                # if it was dissolved before 2013, it is unavailable in the last 10 years
                if int(journal.dissolvedYear[-4:]) <= 2013:
                    dissolveds.append(True)
                else: # if it was dissolved before e.g. 2017, we don't know
                    dissolveds.append(None)
            # if value is a string but should be an integer
            elif int(journal.dissolvedYear) >= 2013:
                dissolveds.append(False)
            elif int(journal.dissolvedYear) < 2013:
                dissolveds.append(True)
            else:
                dissolveds.append(None)

    journals["dissolved"] = dissolveds
    return journals
