# FUNCTIONS TO FILTER AND PREPROCESS ARTICLES FROM OPENALEX 
import pandas as pd
import glob
import prep_taxonomy
import re
import unicodedata
import json
from pathlib import Path

def load_config(config_path=None):
    """
    Load the JSON configuration file.

    Parameters:
        config_path (str or Path): Path to the JSON config file. If None, use default.

    Returns:
        dict: Parsed configuration.
    """
    if config_path is None:
        # Resolve the default path relative to this script's location
        this_dir = Path(__file__).resolve().parent
        config_path = this_dir.parents[1] / "config" / "config.json"

    config_path = Path(config_path)  # Ensure it's a Path object

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

def filter_keywords(articles, config=None):
    # Load and validate config
    if config is None:
        try:
            config = load_config()
            validate_config(config)
        except Exception as e:
            print(f"[CRITICAL] Configuration loading/validation failed: {e}")
            return pd.DataFrame()
    else:
        try:
            validate_config(config)
        except Exception as e:
            print(f"[CRITICAL] Configuration validation failed: {e}")
            return pd.DataFrame()

    # Prepare keyword lists
    single_words = config["keywords"]["single_word"]
    two_words = config["keywords"]["two_word"]
    concept_ids = set(config["concepts"])

    # Ensure we work on a copy
    articles = articles.copy()

    # Normalize display_name (title)
    articles["display_name_norm"] = articles["display_name"].fillna("").apply(normalize_text)

    # Compile title pattern (single + two-word + nov.)
    title_keywords = single_words + two_words + ["nov."]
    title_pattern = "|".join(re.escape(k) for k in title_keywords)
    mask_title = articles["display_name_norm"].str.contains(title_pattern, na=False)

    # Process abstract_inverted_index to flat text
    articles["abstract_text"] = articles["abstract_inverted_index"].apply(
        lambda x: normalize_text(prep_taxonomy.inverted_index_to_text(x)) if isinstance(x, dict) else ""
    )

    # Compile abstract pattern
    two_word_patterns = [
        rf"\b{re.escape(w.split()[0])}\b(?:\s+\S+)?\s+\b{re.escape(w.split()[1])}\b"
        for w in two_words if len(w.split()) == 2
    ]
    abstract_pattern = "|".join(two_word_patterns + [re.escape(k) for k in single_words + ["nov."]])
    mask_abstract = articles["abstract_text"].str.contains(abstract_pattern, regex=True, na=False)

    # Check concept IDs
    mask_concepts = articles["concepts"].apply(
        lambda c: any(con.get("id") in concept_ids for con in c) if isinstance(c, list) else False
    )

    # Combine all matches
    combined_mask = mask_title | mask_abstract | mask_concepts
    filtered = articles[combined_mask].drop_duplicates(subset="id", ignore_index=True)

    # Debug output
    print(f"[DEBUG] Matched on title: {mask_title.sum()}")
    print(f"[DEBUG] Matched on abstract: {mask_abstract.sum()}")
    print(f"[DEBUG] Matched on concepts: {mask_concepts.sum()}")
    print(f"[DEBUG] Total unique matches: {len(filtered)}")

    return filtered


def filter_keywords_to_delete(articles, config=None):
    print(f"[DEBUG] Starting filter_keywords with {len(articles)} articles", flush=True)

    # Load and validate configuration
    if config is None:
        try:
            config = load_config()
            validate_config(config)
        except Exception as e:
            print(f"[CRITICAL] Configuration loading/validation failed: {e}", flush=True)
            return None
    else:
        try:
            validate_config(config)
        except Exception as e:
            print(f"[CRITICAL] Configuration validation failed: {e}", flush=True)
            return None

    queries1 = config['keywords']['single_word']
    queries2 = config['keywords']['two_word']
    concepts = config['concepts']

    print(f"[DEBUG] Keywords: {len(queries1)} single-word, {len(queries2)} two-word | {len(concepts)} concepts", flush=True)

    keep = []

    for idx, article in enumerate(articles.itertuples()):
        cont = False
        if idx % 100 == 0:
            print(f"[DEBUG] Processing article {idx + 1}/{len(articles)}", flush=True)

        # === 1) SEARCH TITLE ===
        if article.display_name is not None:
            display_name_norm = normalize_text(article.display_name)

            for query in queries1 + queries2 + ["nov."]:
                query_norm = normalize_text(query)
                if query_norm in display_name_norm:
                    keep.append(article)
                    cont = True
                    #print(f"[MATCH] Title match: '{query}' in article {article.id}", flush=True)
                    break
            if cont:
                continue

        # === 2) SEARCH ABSTRACT ===
        if article.abstract_inverted_index is not None:
            abstract_words_norm = [
                normalize_text(x).strip(",;.?!'()-]") 
                for x in article.abstract_inverted_index.keys()
            ]

            if "nov." in article.abstract_inverted_index:
                keep.append(article)
                #print(f"[MATCH] Abstract contains 'nov.': article {article.id}", flush=True)
                continue

            for query in queries1:
                query_norm = normalize_text(query)
                if query_norm in abstract_words_norm:
                    keep.append(article)
                    #print(f"[MATCH] Abstract single-word: '{query}' in article {article.id}", flush=True)
                    cont = True
                    break
            if cont:
                continue

            abstract_full_text = prep_taxonomy.inverted_index_to_text(article.abstract_inverted_index)
            abstract_full_text_norm = normalize_text(abstract_full_text)

            for query in queries2:
                query_norm = normalize_text(query)
                words = query_norm.split()
                if len(words) == 2:
                    pattern = rf"\b{re.escape(words[0])}\b(?:\s+\S+)?\s+\b{re.escape(words[1])}\b"
                    if re.search(pattern, abstract_full_text_norm, re.IGNORECASE):
                        keep.append(article)
                        #print(f"[MATCH] Abstract two-word: '{query}' in article {article.id}", flush=True)
                        cont = True
                        break
            if cont:
                continue

        # === 3) SEARCH CONCEPTS ===
        if article.concepts:
            conc_ids = [art_conc["id"] for art_conc in article.concepts]
            for concept in concepts:
                if concept in conc_ids:
                    keep.append(article)
                    #print(f"[MATCH] Concept match: '{concept}' in article {article.id}", flush=True)
                    break

    df = pd.DataFrame(keep).drop_duplicates(subset="id", ignore_index=True).iloc[:, 1:]
    print(f"[DEBUG] Completed filtering: {len(df)} articles matched", flush=True)
    return df



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
