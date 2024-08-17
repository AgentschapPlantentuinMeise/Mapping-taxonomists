# TETTRIs-mapping-taxonomists
TETTRIs WP3, task 3.2: automatic mapping of taxonomic expertise

Before starting you need to download the GBIF taxonomic backbone, unzip it and put the contents in the folder data/external/backbone

The backbone DOI should be cited in any resulting publication. An example citation is below, but consider that the backbone is rebuilt periodically. 

> GBIF Secretariat (2023). GBIF Backbone Taxonomy. Checklist dataset https://doi.org/10.15468/39omei accessed via GBIF.org on 2024-08-14.

You may also need to install SPARQLWrapper to your Python installation.

i.e. using `pip install SPARQLWrapper`

The countries included in the analysis are listed by there two-letter ISO code (ISO 3166-1) in file `included_countries.txt`, in directory `.\src\data`.

This analysis can be replicated by copying the repository and running `make_dataset.py` from the `src` folder. This file runs, in order, the following files:
1.  `list_journals.py` which finds possible taxonomic journals through WikiData and OpenAlex
2.  `get_articles.py` which extracts the articles from these journals and filters out articles about taxonomy, as well as filtering out  
3.  `parse_taxonomy.py` which parses the abstracts of these articles for species names
4.  `get_authors.py` which extracts the authors from these articles
5.  `disambiguate.py` which disambiguates said authors

