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
def get_sparql_results(query, retries=3, delay=5):
    """
    Fetch results from the Wikidata SPARQL endpoint with error handling and retry logic.

    Args:
        query (str): SPARQL query string.
        retries (int): Number of retry attempts for failed requests.
        delay (int): Delay in seconds between retries.

    Returns:
        pd.DataFrame: DataFrame containing the query results.
    """
    endpoint_url = "https://query.wikidata.org/sparql"
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    
    for attempt in range(retries):
        try:
            results = sparql.query().convert()
            return pd.DataFrame.from_dict(results["results"]["bindings"])
        except Exception as e:
            print(f"Attempt {attempt + 1}/{retries} failed with error: {e}")
            if attempt < retries - 1:
                time.sleep(delay)  # Wait before retrying
            else:
                print("Max retries reached. Returning an empty DataFrame.")
                return pd.DataFrame()

#############################################################################
# GET ALL SOURCES (JOURNALS) FROM OPENALEX API WITH SPECIFIED REQUIREMENTS
def request_sources(filter_string, email, retries=3, delay=5):
    """
    Fetch sources from OpenAlex API with error handling and retry logic.

    Args:
        filter_string (str): Filter string for the OpenAlex API.
        email (str): User's email for polite API requests.
        retries (int): Number of retry attempts for failed requests.
        delay (int): Delay in seconds between retries.

    Returns:
        pd.DataFrame: DataFrame containing the API results.
    """
    query = "https://api.openalex.org/sources?per-page=200&filter="+filter_string+"&mailto="+email
    
    session = requests.Session()
    all_results = []

    for attempt in range(retries):
        try:
            # First page
            response = session.get(query + "&cursor=*")
            response.raise_for_status()  # Raise HTTPError for bad responses
            data = response.json()
            all_results.extend(data["results"])

            # Pagination
            next_cursor = data["meta"].get("next_cursor")
            while next_cursor:
                response = session.get(query + f"&cursor={next_cursor}")
                response.raise_for_status()
                data = response.json()
                all_results.extend(data["results"])
                next_cursor = data["meta"].get("next_cursor")

            return pd.DataFrame.from_dict(all_results)

        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}/{retries} failed with error: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                print("Max retries reached. Returning an empty DataFrame.")
                return pd.DataFrame()

    return pd.DataFrame()


#######################################################################
# INSERT DELAY AFTER FAILED REQUEST
# def pitstop(df_request, query, timeout):
#     # if the server timed out
#     if str(df_request) != "<Response [200]>":
#         print("pitstop")
#         # wait a few seconds
#         time.sleep(timeout)
#         # and try again
#         s = requests.Session()
#         df_request = s.get(query+"&cursor=*")
    
#     return df_request


with open("included_countries.txt", "r") as file:
    countries = [line[:-1] for line in file]
    countries = "|".join(map(str, countries))

def make_request_with_retries(url, session=None, retries=3, backoff_factor=2):
    """
    Make a request with retries and exponential backoff.

    Args:
        url (str): URL for the API request.
        session (requests.Session): Persistent session object.
        retries (int): Number of retry attempts.
        backoff_factor (int): Factor for exponential backoff.

    Returns:
        requests.Response: Response object from the request.
    """
    if session is None:
        session = requests.Session()

    for attempt in range(retries):
        try:
            response = session.get(url)
            response.raise_for_status()  # Raise exception for HTTP errors
            return response
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                sleep_time = backoff_factor ** attempt
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                print("Max retries reached. Returning None.")
                return None

# RETRIEVE ALL RECENT ARTICLES WITH A FILTER
def request_works(filter_string, email, from_date="2014-01-01", to_date=None, print_number=True):
    """
    Retrieve recent articles from OpenAlex API with error handling and retries.

    Args:
        filter_string (str): Filter for API query.
        email (str): Email for polite API requests.
        from_date (str): Start date for publication filter.
        to_date (str): End date for publication filter.
        print_number (bool): Whether to print the total number of publications.

    Returns:
        pd.DataFrame: DataFrame containing the results.
    """
    # Build query
    base_query = (
        f"https://api.openalex.org/works?per-page=200&filter=authorships.countries:{countries},"
        f"{filter_string},from_publication_date:{from_date}"
    )
    if to_date:
        query = f"{base_query},to_publication_date:{to_date}&mailto={email}"
    else:
        query = f"{base_query}&mailto={email}"

    # Open persistent session
    session = requests.Session()

    # First page
    response = make_request_with_retries(query, session=session, retries=3)
    if response is None:
        print("Failed to fetch initial page. Returning empty DataFrame.")
        return pd.DataFrame()

    data = response.json()
    publications_results = data.get("results", [])
    next_cursor = data["meta"].get("next_cursor")

    if print_number:
        print(f"Number of publications for {filter_string}: {data['meta']['count']}")

    # Retrieve all pages
    while next_cursor:
        next_query = f"{query}&cursor={next_cursor}"
        response = make_request_with_retries(next_query, session=session, retries=3)
        if response is None:
            print("Failed to fetch additional pages. Returning partial results.")
            break

        data = response.json()
        publications_results.extend(data.get("results", []))
        next_cursor = data["meta"].get("next_cursor")

    return pd.DataFrame.from_dict(publications_results)

