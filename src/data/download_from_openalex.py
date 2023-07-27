import requests
import numpy as np
import pandas as pd
import pickle
import sys
from SPARQLWrapper import SPARQLWrapper, JSON
import time


# RETRIEVE ALL RECENT ARTICLES WITH ONE FILTER
# formerly request_works_openalex
def request_works(filter_string, email, from_date="2013-01-01", to_date=None, print_number=True):
    # build query
    query = "https://api.openalex.org/works?per-page=200&filter="+filter_string+",from_publication_date:"+from_date
        
    if to_date != None:
        query += ",to_publication_date:"+to_date+"&mailto="+email
    else:
        query += "&mailto="+email
        
    # open persistent session to shorten processing time between requests
    s = requests.Session()
    # FIRST PAGE
    publications = s.get(query+"&cursor=*")
    if str(publications) != "<Response [200]>":
        print("pitstop")
        time.sleep(20)
        s = requests.Session()
        publications = s.get(query+"&cursor=*")
        # and again
        if str(publications) != "<Response [200]>":
            print("long pitstop")
            time.sleep(200)
            s = requests.Session()
            publications = s.get(query+"&cursor=*")
    if print_number:
        print("Number of publications for "+filter_string+": "+str(publications.json()["meta"]["count"]))
    
    next_pubs = publications.json()
    next_cursor = next_pubs["meta"]["next_cursor"]

    publications_results = next_pubs["results"]
    
    # RETRIEVE ALL PAGES
    n = 1
    while next_pubs["meta"]["next_cursor"] != None:
        #if n%3==0: 
        #    time.sleep(5) 
        #    s = requests.Session()
        #n += 1
        # get next page
        next_pubs = s.get(query+"&cursor="+next_cursor)
        # if at first you don't succeed, wait and try again
        if str(next_pubs) != "<Response [200]>":
            print("pitstop")
            time.sleep(20)
            s = requests.Session()
            next_pubs = s.get(query+"&cursor="+next_cursor)
            # and again
            if str(next_pubs) != "<Response [200]>":
                print("long pitstop")
                time.sleep(200)
                s = requests.Session()
                next_pubs = s.get(query+"&cursor="+next_cursor)

        next_pubs = next_pubs.json()
        next_cursor = next_pubs["meta"]["next_cursor"] # remember next cursor

        publications_results.extend(next_pubs["results"])
    
    publications_df = pd.DataFrame.from_dict(publications_results)
    return publications_df

