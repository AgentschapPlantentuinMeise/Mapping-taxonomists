# FUNCTIONS TO FILTER AND PREPROCESS ARTICLES FROM OPENALEX 
import pandas as pd


# release information locked in dictionaries inside the dataframe: open access, host (journal)
def flatten_works(df_input): # input: articles straight from openalex
    newcols = ["location_is_oa", "location_landing_page_url", "location_pdf_url", 
               "location_source", "location_license", "location_version", 
               "source_id", "source_display_name", "source_issn_l", "source_issn", 
               "source_is_oa", "source_is_in_doaj",
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
            
            # not all sources have "is_oa" and "is_in_doaj" provided
            if "is_oa" not in article.primary_location["source"]:
                l_source.insert(4, "unknown")
            if "is_in_doaj" not in article.primary_location["source"]:
                l_source.insert(5, "unknown")

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


# filter all articles: at least one of the institutions associated with one of the authors, must be EU
def filter_eu_articles(df_input, eu27 = False):
    # two-letter country codes of all European countries
    # from map: https://en.wikipedia.org/wiki/Europe#Contemporary_definition
    eu_codes = ["IS", "SV", "FO", "NO", "FI", "SE", "DK", # Scandinavia
                "EE", "LV", "LT", # Baltic countries
                "IE", "IM", "GB", "GI", # Great Britain
                "NL", "BE", "LU", # Benelux
                "ES", "PT", "MT", "FR", "IT", "GR", # mediterranean
                "BA", "HR", "SI", "ME", "RS", "MK", "AL", # balkan
                "DE", "CZ", "CH", "AT", "SK", "PL", "HU", # central
                "BY", "UA", "MD", "RO", "BG" # eastern
                "SM", "VA", "LI", "AD", "MC"] # micronations
    if eu27:
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


# query list of articles for specific words and concepts to filter out irrelevant articles
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


# put together separate files with articles
def merge_pkls(directory):
    articles = []

    files = glob.glob(directory+"*")
    for f in files:
        if f[-4:]==".pkl":
            articles.append(pd.read_pickle(f))
    
    return pd.concat(articles, ignore_index=True)
