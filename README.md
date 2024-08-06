# TETTRIs-mapping-taxonomists
TETTRIs WP3, task 3.2: automatic mapping of taxonomic expertise 

This analysis can be replicated by copying the repository and running `make_dataset.py` from the `src` folder. This file runs, in order, the following files:
1.  `list_journals.py` which finds possible taxonomic journals through WikiData and OpenAlex
2.  `get_articles.py` which extracts the articles from these journals and filters out articles about taxonomy, as well as filtering out  
3.  `parse_taxonomy.py` which parses the abstracts of these articles for species names
4.  `get_authors.py` which extracts the authors from these articles
5.  `disambiguate.py` which disambiguates said authors

