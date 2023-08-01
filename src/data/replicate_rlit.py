# replicating WoS queries
import numpy as np
import pandas as pd
import pickle
import download
import prep_articles
import prep_authors
import time


email = input("Enter e-mail address for OpenAlex API: ")

# search every insect order listed in the RLIT
insect_orders = ["Coleoptera", "Hemiptera", "Diptera", "Lepidoptera", "Orthoptera", 
                 "Odonata", "Blattodea", "Ephemeroptera", "Psocodea", "Grylloblattodea", 
                 "Neuroptera", "Mecoptera", "Trichoptera", "Plecoptera", "Dermaptera", 
                 "Mantodea", "Siphonaptera", "Strepsiptera", "Embioptera", "Hymenoptera",
                 "Phasmida", "Raphidioptera", "Isoptera", "Megaloptera", "Thysanoptera",
                 "Zygentoma", "Mantophasmatodea", "Archaeognatha", "Zoraptera"]
insect_articles = pd.DataFrame()

for order in insect_orders:
    start = time.time()
    results = []
    
    # search each of the WoS search terms in abstract or title or concepts
    # the order must also be found in abstract or title (only some orders exist as concepts)
    # OpenAlex OR function in search not useable because it excludes results with both search terms
    
    # Plecoptera AND
    for query in ["title.search:"+order+",title.search:%22new species%22", # OR "new species"
                  "title.search:"+order+",abstract.search:new species",
                  "title.search:%22new species%22,abstract.search:"+order,
                  "abstract.search:"+order+" new species", 

                  "title.search:"+order+" AND %22novel species%22", # OR "novel species"
                  "title.search:"+order+",abstract.search:novel species",
                  "title.search:%22novel species%22,abstract.search:"+order,
                  "abstract.search:"+order+" novel species",

                  "title.search:"+order+" AND %22new genus%22", # OR "new genus"
                  "title.search:"+order+",abstract.search:new genus",
                  "title.search:%22new genus%22,abstract.search:"+order,
                  "abstract.search:"+order+" new genus",

                  "title.search:"+order+" AND %22new genera%22", # OR "new genera"
                  "title.search:"+order+",abstract.search:new genera",
                  "title.search:%22new genera%22,abstract.search:"+order,
                  "abstract.search:"+order+" new genera",

                  "title.search:"+order+" AND checklist", # OR "checklist"
                  "title.search:"+order+",abstract.search:checklist",
                  "title.search:checklist,abstract.search:"+order,
                  "abstract.search:"+order+" checklist",

                  "title.search:"+order+" AND taxonomy", # taxonom* (OpenAlex automatically stems)
                  "title.search:"+order+",abstract.search:taxonomy",
                  "title.search:taxonomy,abstract.search:"+order,
                  "abstract.search:"+order+" taxonomy",

                  # concepts
                  "title.search:"+order+",concepts.id:C58642233", # taxonomy
                  "abstract.search:"+order+",concepts.id:C58642233",

                  "title.search:"+order+",concepts.id:C71640776", # taxon
                  "abstract.search:"+order+",concepts.id:C71640776",

                  "title.search:"+order+",concepts.id:C2779356329", # checklist
                  "abstract.search:"+order+",concepts.id:C2779356329",
                 ]:
            articles = download.request_works(query, email,
                                              from_date="2011-01-01", to_date="2020-12-31",
                                              print_number=False)
            results.append(articles)
    
    # combine results and remove duplicates
    order_articles = pd.concat(results, ignore_index=True).drop_duplicates(subset="id", ignore_index=True)
    order_articles["order"] = order
    insect_articles = pd.concat([insect_articles, order_articles])
    
    end=time.time()
    print(order + " done in "+str(end-start)+" seconds")

insect_articles.to_pickle("../../data/raw/rlit/openalex_articles.pkl")

#insect_articles = prep_articles.flatten_works(insect_articles)
#authors_insects = prep_authors.get_authors(insect_articles)
#singles_insects = prep_authors.get_single_authors(authors_insects)

#authors_insects.to_pickle("./data/rlit/all_authors.pkl")
#singles_insects.to_pickle("./data/rlit/authors_no_duplicates.pkl")


insect_eu_articles = prep_articles.filter_eu_articles(insect_articles, eu27=True)
insect_eu_articles.to_pickle("../../data/interim/rlit/openalex_EU27_articles.pkl")

#eu_insect_articles = prep_articles.flatten_works(eu_insect_articles)
#eu_insect_authors = prep_authors.get_authors(eu_insect_articles)
#only_eu_insect_authors = prep_authors.get_eu_authors(eu_insect_authors, pan_europe=False)
#eu_single_insect_authors = prep_authors.get_single_authors(only_eu_insect_authors)

#only_eu_insect_authors.to_pickle("../../data/rlit/EU27_all_authors.pkl")
#eu_single_insect_authors.to_pickle("../../data/rlit/EU27_authors_no_duplicates.pkl")
