# FUNCTIONS TO FILTER AND PREPROCESS ARTICLES FROM OPENALEX 
import pandas as pd
import glob
import prep_taxonomy
import re
import unicodedata
import json

def load_config(config_path="../../config.json"):
    """
    Load the JSON configuration file.

    Parameters:
        config_path (str): Path to the JSON config file.

    Returns:
        dict: Parsed configuration.
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = json.load(file)
        print(f"Configuration loaded from '{config_path}'.")
        return config
    except FileNotFoundError:
        print(f"ERROR: Configuration file '{config_path}' not found.")
        raise
    except json.JSONDecodeError as e:
        print(f"ERROR: Error parsing JSON configuration: {e}")
        raise

def validate_config(config):
    """
    Validate the presence and structure of required sections in the config.

    Parameters:
        config (dict): Configuration dictionary.

    Raises:
        ValueError: If required sections or keys are missing.
    """
    required_sections = ['from_date', 'to_date', 'keywords', 'concepts']
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing '{section}' section in configuration.")

    if 'single_word' not in config['keywords'] or 'two_word' not in config['keywords']:
        raise ValueError("Configuration must include 'single_word' and 'two_word' under 'keywords'.")

    if not isinstance(config['keywords']['single_word'], list) or not isinstance(config['keywords']['two_word'], list):
        raise ValueError("'single_word' and 'two_word' under 'keywords' must be lists.")

    if not isinstance(config['concepts'], list):
        raise ValueError("'concepts' should be a list.")

    print("Configuration validation passed.")

def normalize_text(s):
    """
    Normalize the string to NFC (Canonical Composition) and lowercase it.
    This helps ensure that accented or Cyrillic characters are consistently
    represented for matching.
    """
    if not s:
        return ""
    return unicodedata.normalize("NFC", s).lower()

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
                article.primary_location["source"]["issn"] = ','.join(article.primary_location["source"]["issn"])
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


def filter_keywords(articles):
    # Load and validate configuration
    try:
        config = load_config("../../config.json")  # Ensure the path is correct
        validate_config(config)
    except Exception as e:
        print(f"CRITICAL: Configuration loading/validation failed: {e}")
        return
    
    queries1 = config['keywords']['single_word']
    queries2 = config['keywords']['two_word']
    concepts = config['concepts']

    keep = []

    for article in articles.itertuples():
        cont = False

        #--------------------
        # 1) SEARCH TITLE
        #--------------------
        if article.display_name is not None:
            # Normalize the display name
            display_name_norm = normalize_text(article.display_name)

            # single-word queries + "nov."
            for query in queries1 + queries2 + ["nov."]:
                query_norm = normalize_text(query)
                if query_norm in display_name_norm:
                    keep.append(article)
                    cont = True
                    break  # Found match in title -> keep article, stop searching
            if cont:
                continue  # move on to next article

        #-----------------------
        # 2) SEARCH ABSTRACT
        #-----------------------
        # If there's an abstract, we want to check the inverted index
        if article.abstract_inverted_index is not None:
            # Normalize each token in the abstract keys
            abstract_words_norm = [
                normalize_text(x).strip(",;.?!'()-]")  # strip punctuation on top of normalization
                for x in article.abstract_inverted_index.keys()
            ]

            # (a) Check if "nov." is directly in the abstract tokens
            if "nov." in article.abstract_inverted_index:
                # If the original key "nov." is present
                keep.append(article)
                continue

            # single-word queries in the abstract tokens
            for query in queries1:
                query_norm = normalize_text(query)
                if query_norm in abstract_words_norm:
                    keep.append(article)
                    cont = True
                    break
            if cont:
                continue

            # two-word queries in the full abstract text
            # convert the entire abstract to a normalized string
            # (assuming you have a utility like prep_taxonomy.inverted_index_to_text)
            abstract_full_text = prep_taxonomy.inverted_index_to_text(article.abstract_inverted_index)
            abstract_full_text_norm = normalize_text(abstract_full_text)

            for query in queries2:
                query_norm = normalize_text(query)
                # split into two words
                words = query_norm.split()
                if len(words) == 2:
                    # Build a pattern that matches these two words as separate tokens
                    # \b ensures word boundaries, re.escape avoids regex special chars
                    pattern = rf"\b{re.escape(words[0])}\b(?:\s+\S+)?\s+\b{re.escape(words[1])}\b"
                    if re.search(pattern, abstract_full_text_norm, re.IGNORECASE):
                        keep.append(article)
                        cont = True
                        break
                else:
                    # If query is more or fewer than 2 words, you can handle differently
                    continue

            if cont:
                continue  # Move on to next article

        #---------------------------------
        # 3) SEARCH CONCEPTS BY ID
        #---------------------------------
        # Convert each concept ID in the article to a list, and if
        # any match the "concepts" list, keep the article
        if article.concepts:
            conc_ids = [art_conc["id"] for art_conc in article.concepts]
            for concept in concepts:
                if concept in conc_ids:
                    keep.append(article)
                    break  # no need to check the other concepts

    # Finally, return a new DataFrame of kept articles
    return pd.DataFrame(keep).drop_duplicates(subset="id", ignore_index=True).iloc[:, 1:]


def filter_by_domain(articles_df, domain_id = "https://openalex.org/domains/1"):
    """
    Given a DataFrame of article records (after your main filter),
    return only those with the specified domain (e.g., https://openalex.org/domains/1).
    
    The function looks for the domain ID in both 'primary_topic' and 'topics'.
    """
    keep = []
    
    for article in articles_df.itertuples():
        # Convert namedtuple to dict for easier key-based access
        article_dict = article._asdict()
        
        # 1. Check 'primary_topic'
        primary_topic = article_dict.get("primary_topic")
        if primary_topic and "domain" in primary_topic:
            if primary_topic["domain"].get("id") == domain_id:
                keep.append(article)
                continue  # proceed to next article

        # 2. Check each topic in the 'topics' array
        topics = article_dict.get("topics", [])
        for t in topics:
            domain_info = t.get("domain")
            if domain_info and domain_info.get("id") == domain_id:
                keep.append(article)
                break  # no need to look at more topics for this article

    # Return a DataFrame of unique articles
    return pd.DataFrame(keep).drop_duplicates(subset="id", ignore_index=True)


# put together separate files with articles
def merge_pkls(directory):
    articles = []

    files = glob.glob(directory+"*")
    for f in files:
        if f[-4:]==".pkl":
            articles.append(pd.read_pickle(f))
    
    return pd.concat(articles, ignore_index=True)
