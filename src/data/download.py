# Functions to download data from OpenAlex (using API) and from Wikidata (using SPARQL queries) 
import requests
import numpy as np
import pandas as pd
import pickle
import sys
from SPARQLWrapper import SPARQLWrapper, JSON
import time


# BUILD SPARQL QUERIES TO FIND JOURNALS WITH ONE OF MANY TAXONOMIC SUBJECTS
def build_sparql_query(subjects):
    # instance of (P31) scientific (Q5633421) or academic journal (Q737498)
    query = """SELECT DISTINCT ?item ?itemLabel ?openAlexID ?issnL ?issn 
    ?IPNIpubID ?ZooBankPubID ?IndexFungorumID ?dissolved ?country
WHERE {
    VALUES ?journaltype {wd:Q5633421 wd:Q737498}
    ?item wdt:P31/wdt:P279* ?journaltype .""" 
    
    # add specified subjects (taxonomy,...) for field of work (P101) or main subject (P921)
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
        
        query += addition
    
    # include, if available: OpenAlex, IPNI and ZooBank Publication IDs, ISSN and ISSN-Ls, 
    # when (if ever) the journal was dissolved, and country of publication
    query += """
    OPTIONAL{?item wdt:P10283 ?openAlexID}
    OPTIONAL{?item wdt:P7363 ?issnL}
    OPTIONAL{?item wdt:P236 ?issn}
    OPTIONAL{?item wdt:P2008 ?IPNIpubID}
    OPTIONAL{?item wdt:P2007 ?ZooBankPubID}
    OPTIONAL{?item wdt:P576 ?dissolved}
    OPTIONAL{?item wdt:P495 ?country}
    
    SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}"""
    
    return query


# GET RESULTS OF SPARQLE QUERY (code from WikiData's query service)
def get_sparql_results(query):
    endpoint_url = "https://query.wikidata.org/sparql"
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    
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
        # get next page with cursor
        next_sources = s.get(query+"&cursor="+next_cursor)
        next_sources = next_sources.json()
        next_cursor = next_sources["meta"]["next_cursor"] # remember next cursor
        if next_sources["results"]:
            sources_results.extend(next_sources["results"])
    
    sources_df = pd.DataFrame.from_dict(sources_results)
    return sources_df


# INSERT DELAY AFTER FAILED REQUEST
def pitstop(df_request, query, timeout):
    # if the server timed out
    if str(df_request) != "<Response [200]>":
        print("pitstop")
        # wait a few seconds
        time.sleep(timeout)
        # and try again
        s = requests.Session()
        df_request = s.get(query+"&cursor=*")
    
    return df_request


with open("included_countries.txt", "r") as file:
    countries = [line[:-1] for line in file]
    countries = "|".join(map(str, countries))


# RETRIEVE ALL RECENT ARTICLES WITH A FILTER
def request_works(filter_string, email, from_date="2014-01-01", to_date=None, print_number=True):
    # build query
    query = "https://api.openalex.org/works?per-page=200&filter=authorships.countries:"+countries+","+filter_string+",from_publication_date:"+from_date
    if to_date != None:
        query += ",to_publication_date:"+to_date+"&mailto="+email
    else:
        query += "&mailto="+email
        
    # open persistent session to shorten processing time between requests
    s = requests.Session()
    
    # FIRST PAGE
    publications = s.get(query+"&cursor=*")
    # if the server timed out, wait 20 seconds and try again
    publications = pitstop(publications, query, 20)
    publications = pitstop(publications, query, 200) # 200 seconds if 20 wasn't enough
    
    if print_number:
        print("Number of publications for "+filter_string+": "+str(publications.json()["meta"]["count"]))
    
    next_pubs = publications.json()
    next_cursor = next_pubs["meta"]["next_cursor"]
    publications_results = next_pubs["results"]
    
    # RETRIEVE ALL PAGES
    while next_pubs["meta"]["next_cursor"] != None:
        # get next page with cursor
        next_pubs = s.get(query+"&cursor="+next_cursor)
        next_pubs = pitstop(next_pubs, query, 20)
        next_pubs = pitstop(next_pubs, query, 200)

        next_pubs = next_pubs.json()
        next_cursor = next_pubs["meta"]["next_cursor"] # remember next cursor
        publications_results.extend(next_pubs["results"])
    
    publications_df = pd.DataFrame.from_dict(publications_results)
    return publications_df
