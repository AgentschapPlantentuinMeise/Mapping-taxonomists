import requests
import numpy as np
import pandas as pd
import pickle
import sys
from SPARQLWrapper import SPARQLWrapper, JSON
import time


# RETRIEVE ALL RECENT ARTICLES WITH ONE FILTER
# formerly request_works_openalex
def request_works(filter_string, from_date="2013-01-01", to_date=None, print_number = True):
    # build query
    query = "https://api.openalex.org/works?per-page=200&filter="+filter_string+",from_publication_date:"+from_date
        
    if to_date != None:
        query += ",to_publication_date:"+to_date
        
    # open persistent session to shorten processing time between requests
    s = requests.Session()
    # FIRST PAGE
    publications = s.get(query+"&cursor=*")
    if print_number:
        print("Number of publications for "+filter_string+": "+str(publications.json()["meta"]["count"]))
    
    next_pubs = publications.json()
    next_cursor = next_pubs["meta"]["next_cursor"]

    publications_results = next_pubs["results"]
    
    # RETRIEVE ALL PAGES
    while next_pubs["meta"]["next_cursor"] != None:
        # get next page
        next_pubs = s.get(query+"&cursor="+next_cursor)

        next_pubs = next_pubs.json()
        next_cursor = next_pubs["meta"]["next_cursor"] # remember next cursor

        publications_results.extend(next_pubs["results"])
    
    publications_df = pd.DataFrame.from_dict(publications_results)
    return publications_df


# GET RESULTS OF SPARQLE QUERIES (code from WikiData's query service)
endpoint_url = "https://query.wikidata.org/sparql"

def get_sparql_results(query, endpoint_url=endpoint_url):
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    # TODO adjust user agent; see https://w.wiki/CX6
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return pd.DataFrame.from_dict(results["results"]["bindings"])

# BUILD SPARQL QUERIES FOR MULTIPLE
# formerly build_query_subjects
def build_sparql_query(list):
    # first, it must be an instance of (P31) a scientific journal (Q5633421) or academic journal (Q737498)
    query = """SELECT DISTINCT ?item ?itemLabel ?issn ?issn_l WHERE {
    ?item wdt:P236 ?issn.
    ?item wdt:P7363 ?issn_l.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE]". }
  {
    SELECT DISTINCT ?item WHERE {
      {
        ?item p:P31 ?statement0.
        ?statement0 (ps:P31/(wdt:P279*)) wd:Q5633421.
      }
      UNION
      {
        ?item p:P31 ?statement1.
        ?statement1 (ps:P31/(wdt:P279*)) wd:Q737498.
      }"""
    
    # add specific requirements (taxonomy, phylogeny,...) for field of work (P101) or main subject (P921)
    for i, subject in enumerate(list):
        i = 2 + i*2
        addition = """\n      {
        ?item p:P921 ?statement""" + str(i) + """.
        ?statement""" + str(i) + """ (ps:P921/(wdt:P279*)) wd:""" + subject + """.
      }
      UNION
      {
        ?item p:P101 ?statement""" + str(i+1) + """.
        ?statement""" + str(i+1) + """ (ps:P101/(wdt:P279*)) wd:""" + subject + """.
      }"""
        if i != 2:
            addition = "\n      UNION" + addition
        
        query += addition
    
    query += """\n    }
  }
}"""
    return query


# filter all articles: at least one of the institutions associated with one of the authors, must be EU
def filter_eu_articles(df_input):
    # two-letter country codes of all EU27 countries
    eu_codes = ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", # EU
                "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"] # EU

    eu_articles = []

    for article in df_input.itertuples():
        # check every author
        for author in article.authorships:
            stop = False
            # check every affiliated institute
            for institute in author["institutions"]:
                if institute:
                    country = institute["country_code"]
                    # european?
                    if country in eu_codes:
                        eu_articles.append(list(article))
                        stop=True # each article should only be included once
                        break # stop going over institutes of this author

            if stop:
                break # stop going over authors of this article

    eu_articles = pd.DataFrame(eu_articles)
    eu_articles = eu_articles.iloc[:,1:]
    eu_articles.columns = df_input.columns
    
    return eu_articles


# QUERY GIVEN LIST OF ARTICLES FOR SPECIFIC WORDS AND CONCEPTS TO FILTER OUT IRRELEVANT ARTICLES
# formerly query_articles
def filter_keywords(articles):
    queries1 = ["taxonomy", "taxonomic", "taxon", "checklist"] # one-word queries
    queries2 = ["new species", "novel species", "new genus", "new genera"] # two-word queries
    concepts = ["C58642233", "C71640776", "C2779356329"] # OpenAlex IDs of concepts
                                                         # taxonomy, taxon, checklist
    
    keep = []
    
    for article in articles.itertuples():
        cont = False
        # SEARCH TITLE
        if article.display_name != None:
            # single-word queries
            for query in queries1 + queries2 + ["nov.",]:
                if query in article.display_name.lower():
                    keep.append(article)
                    cont = True
                    break # stop querying
            if cont:
                continue # move on to next article

        # SEARCH ABSTRACT
        # get list of words from the abstract without distracting characters or uppercase
        if article.abstract_inverted_index != None:
            abstract_words = article.abstract_inverted_index.keys()
            abstract_words = [x.lower().strip(",;.?!\'()-]") for x in abstract_words]
        
            # search "nov." without stripping abstract of period
            if "nov." in article.abstract_inverted_index.keys():
                keep.append(article)
                continue
            if cont:
                continue # move on to next article
            
            # one-word queries
            for query in queries1:
                if query in abstract_words:
                    keep.append(article)
                    cont = True
                    break
            if cont:
                continue # move on to next article
                    
            # two-word queries
            for query in queries2:
                if query.split()[0] in abstract_words and query.split()[1] in abstract_words:
                    keep.append(article)
                    cont = True
                    break
            if cont:
                continue # move on to next article
            
        # SEARCH CONCEPTS BY ID
        for concept in concepts:
            # make list of concepts (by OpenAlex ID) associated with the article
            conc_ids = []
            for art_conc in article.concepts:
                conc_ids.append(art_conc["id"])

            if concept in conc_ids:
                keep.append(article)
                break
    
    return pd.DataFrame(keep).drop_duplicates(subset="id", ignore_index=True).iloc[:,1:]


# information locked in dictionaries inside the dataframe: open access, host (journal)
# formerly called "get_dict_info"
def flatten_works(df_input): # input: articles straight from openalex
    newcols = ["location_is_oa", "location_landing_page_url", "location_pdf_url", 
               "location_source", "location_license", "location_version", 
               "source_id", "source_display_name", "source_issn_l", "source_issn", "is_in_doaj",
               "source_host_organization", "source_host_organization_name", 
               "source_host_organization_lineage", "source_host_organization_lineage_names", "source_type",
               "is_oa", "oa_status", "oa_url", "any_repository_has_fulltext"]
    
    new_rows = []
    
    for article in df_input.itertuples():
        # get host (journal) info
        # if there is a list within the dictionary, pandas will turn it into two rows
        if article.primary_location["source"] != None:
            if article.primary_location["source"]["issn"] != None and len(article.primary_location["source"]["issn"]) != 1:
                article.primary_location["source"]["issn"] = '\n'.join(article.primary_location["source"]["issn"])
            l_source = list(article.primary_location["source"].values())
            if len(l_source) == 9: # if no "is_in_doaj" provided
                l_source.insert(4, "unknown")
        else:
            l_source = [None,] * 10
            
        l_location = list(article.primary_location.values())
        l_oa = list(article.open_access.values())
        # unite open access and journal info from this article and previous articles
        l_new = l_location + l_source + l_oa
        new_rows.append(l_new)
    # unite data in dictionaries with accessible data
    new_df = pd.DataFrame(new_rows, columns=newcols)
    return df_input.merge(new_df, left_index=True, right_index=True)


# get authorship information from raw dataframe WITH all other data

def get_authors(df_input): # input: articles after get_dict_info
    # create empty dataframe with all authorship attributes
    df = pd.DataFrame()
    authors_list = []
    
    for article in df_input.itertuples():
        authors = pd.DataFrame(article.authorships)
        
        if len(authors) != 0:
            # disassemble author info
            for author in authors.itertuples():
                new_info = [article.id]+[author.author_position]+list(author.author.values())+[author.raw_affiliation_string]
                
                # add institution info
                if len(author.institutions) != 0:
                    new_info += list(author.institutions[0].values()) 
                else:
                    # no institution, no info
                    new_info += [None, None, None, None, None]
                authors_list.append(new_info) 
    
    new_df = pd.DataFrame(authors_list, 
                          columns=["article_id", "author_position", "author_id", "author_display_name", "orcid",
                                   "raw_affiliation_string", 
                                   "inst_id", "inst_display_name", "ror", "inst_country_code", "inst_type"])
    df = pd.concat([df, new_df])
    
    return pd.merge(df, df_input, left_on="article_id", right_on="id")


# keep most recent publication per author

def get_single_authors(df_input): # input: authors with doubles
    keep = []
    
    for author in set(df_input["author_id"]):
        # get all rows that match author
        publications = df_input[df_input["author_id"]==author]
        # get most recent one
        most_recent = publications["publication_date"].max()
        keep += publications[publications["publication_date"]==most_recent].values.tolist()
    
    keep_df = pd.DataFrame(keep,
                           columns = df_input.columns)
    
    # drop duplicates because some articles may have been found twice through different queries 
    # and some authors have published multiple relevant articles on the same day
    return keep_df.drop_duplicates(subset=["author_id"])


# filter a list of authors for authors who are asscociated with at least one European institution
# formerly "get european authors"
def get_eu_authors(df_input, pan_europe=False): # input: authors
    keep = []
    
    eu_codes = ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", # EU
                "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"] # EU
    paneu_codes = ["IS", "LI", "NO", "CH", "AL", "ME", "MK", "RS", "TR", "AD", "BY", "BA", # pan-Europe
                   "MD", "MC", "RU", "SM", "UA", "GB", "VA", "GE", "AM", "AZ"] # pan-Europe
    
    for author in df_input.itertuples():
        # check every affiliated institute
        if author.inst_country_code in eu_codes:
            keep.append(author)
        elif pan_europe and author.inst_country_code in paneu_codes:
            keep.append(author)
    
    return pd.DataFrame(keep)