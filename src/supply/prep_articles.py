# FUNCTIONS TO FILTER AND PREPROCESS ARTICLES FROM OPENALEX 
import pandas as pd
import glob
import prep_taxonomy
import re

# release information locked in dictionaries inside the dataframe: open access, host (journal)
def flatten_works(df_input): # input: articles straight from openalex
    # find an example row to infer column names from
    i = 0
    example_row = None
    while example_row is None:
        row = df_input.iloc[i]
        # needs to have an available source with all expected fields
        if row["primary_location"]["source"] != None:
            if "is_oa" in row["primary_location"]["source"] \
            and "is_in_doaj" in row["primary_location"]["source"]:
                example_row = row
                length_source = len(row["primary_location"]["source"])
        else:
            i += 1
            
    new_cols = ["location_" + x for x in example_row["primary_location"].keys()] + \
               ["source_" + x for x in example_row["primary_location"]["source"].keys()] + \
               ["oa_" + x for x in example_row["open_access"].keys()] 
    new_rows = []
    
    for article in df_input.itertuples():
        # get host (journal) info
        # if there is a list within the dictionary, pandas will turn it into two rows
        # LOCATION
        l_location = list(article.primary_location.values())
        
        # SOURCE
        if article.primary_location["source"] != None:
            if article.primary_location["source"]["issn"] != None and len(article.primary_location["source"]["issn"]) != 1:
                # get everything about source
                article.primary_location["source"]["issn"] = '\n'.join(article.primary_location["source"]["issn"])
            l_source = list(article.primary_location["source"].values())
            
            # not all sources have "is_oa" and "is_in_doaj" provided
            if "is_oa" not in article.primary_location["source"]:
                l_source.insert(4, "unknown")
            if "is_in_doaj" not in article.primary_location["source"]:
                l_source.insert(5, "unknown")

        else:
            l_source = [None,] * length_source
        
        # OPEN ACCESS
        l_oa = list(article.open_access.values())
        
        # UNITE
        l_new = l_location + l_source + l_oa
        new_rows.append(l_new)
        
    # unite data in dictionaries with accessible data
    new_df = pd.DataFrame(new_rows, columns=new_cols)
    return df_input.merge(new_df, left_index=True, right_index=True)


# filter all articles: at least one of the institutions associated with one of the authors, must be EU
# def filter_eu_articles(df_input):
#     # two-letter country codes of all European countries
#     # from map: https://en.wikipedia.org/wiki/Europe#Contemporary_definition
#     eu_codes = ["IS", "SE", "FO", "NO", "FI", "SE", "DK", # Nordic
#                 "EE", "LV", "LT", # Baltic 
#                 "IE", "IM", "GB", "GI", # Great Britain
#                 "NL", "BE", "LU", # Benelux
#                 "ES", "PT", "MT", "FR", "IT", "GR", "CY", "TR", # Mediterranean
#                 "BA", "HR", "SI", "ME", "RS", "MK", "AL", "XK", # Balkan
#                 "DE", "CZ", "CH", "AT", "SK", "PL", "HU", # Central
#                 "UA", "MD", "RO", "BG", # Eastern
#                 "SM", "VA", "LI", "AD", "MC", # Micronations
#                 "GG", "JE", "SJ", "AX", # Dependencies
#                 "AZ", "GE", "AM", # Caucasus
#                 "FK", "VG", "GS", "TC", "SH", "IO", "MS", "BM", "KY", "AI", "PN", # UK overseas territories
#                 "MQ", "GP", "RE", "PM", "MF", "GF", "PF", "WF", "BL", "YT", "NC", # French overseas territories
#                 "GL", "FO", # Denmark affiliated
#                 "AW", "CW", "SX", "BQ"] # Dutch overseas territories

#     eu_articles = []

#     for article in df_input.itertuples():
#         # check every author
#         for author in article.authorships:
#             stop = False
#             # check every affiliated institute
#             for institute in author["institutions"]:
#                 if institute:
#                     country = institute["country_code"]
#                     # european?
#                     if country in eu_codes:
#                         eu_articles.append(list(article))
#                         stop=True # each article should only be included once
#                         break # stop going over institutes of this author

#             if stop:
#                 break # stop going over authors of this article

#     eu_articles = pd.DataFrame(eu_articles)
#     eu_articles = eu_articles.iloc[:,1:]
#     eu_articles.columns = df_input.columns
    
#     return eu_articles


# query list of articles for specific words and concepts to filter out irrelevant articles
def filter_keywords(articles):
    queries1 = ["taxonomic", "taxon", "lectotype", "paratype", "neotype"] # one-word queries, checklist was removed as it led to too many errors
    queries2 = ["new species", "novel species", "new genus", "new genera",
                "Holotype Specimen","Taxonomic Revision","Species Delimitation",
                "Taxonomic Key","Phylogenetic Tree","Type Locality",
                "Type Specimen","Taxonomic Rank","Species Epithet",
                "Type Designation"] # two-word queries
    concepts = ["https://openalex.org/C58642233", "https://openalex.org/C71640776"] # OpenAlex IDs of concepts
                                                         # taxonomy, taxon
    
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
            abstract_full_text = prep_taxonomy.inverted_index_to_text(article.abstract_inverted_index)
            # for query in queries2:
            #     # match query to article abstract
            #     if abstract_full_text.find(query) != -1:
            #         keep.append(article)
            #         cont = True
            #         break
            # if cont:
            #     continue # move on to next article
            # for query in queries2:
            #     if re.search(rf"\b{re.escape(query)}\b", abstract_full_text):  # Match the exact phrase
            #         keep.append(article)
            #         cont = True
            #         break
            # if cont:
            #      continue # move on to next article

            for query in queries2:
                # Create a regex pattern for the exact two-word phrase with whole-word matching
                words = query.split()
                pattern = rf"\b{re.escape(words[0])}\b\s+\b{re.escape(words[1])}\b"
                
                # Search for the pattern in the abstract
                if re.search(pattern, abstract_full_text, re.IGNORECASE):  # Case-insensitive search
                    print(f"Matched query: {query}")
                else:
                    print(f"No match for query: {query}")
            
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
