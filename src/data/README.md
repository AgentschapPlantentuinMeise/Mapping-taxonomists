## Building the datasets

The following scripts are packages:
 - `download.py` contains functions for downloading data from OpenAlex or Wikidata, for both journals and articles.
 - `prep_journals.py` contains functions for preprocessing the list of journals. This mainly involves homogenizing the data so that OpenAlex and Wikidata journals are comparable, as well as functions to e.g. decide whether a journal is recently dissolved or not.
 - `prep_articles.py` contains functions for preprocessing articles downloaded from OpenAlex, primarily to extract European articles and articles containing keywords like "new species", "taxonomy", etc. 
- `prep_authors.py` contains functions for extracting (European) authors from the articles previously downloaded and deduplicate them.

 The other scripts execute the above functions. They are run automatically by `make_dataset.py` in the following order:
 1. `list_journals.py` makes a final list of relevant taxonomic journals, which is saved as data/processed/journals.csv
 2. `get_articles.py` downloads all recent (10 years) articles from the above journals via the OpenAlex API. The results are saved in separate chunks in data/raw/articles. It filters these articles for certain taxonomic keywords and word groups and filters out any articles without European authors. 
 3. `parse_taxonomy.py` infers taxonomic subjects from the articles' titles and abstracts (results in data/processed). 
 4. `get_authors.py` extracts the authors from these articles and keeps European authors, linked to their most recent article (results in data/interim and data/processed).

`replicate_rlit.py` runs a different analysis, more analogous to the methodology used for the Red List of Insect Taxonomists (https://cloud.pensoft.net/s/mGpyQYUPQOMPs8C). This can be run independently from the other scripts. 
 
 "European" is defined as coming from the countries in black on this map:
 
![European countries, according to https://en.wikipedia.org/wiki/Europe#Contemporary_definition](./Screenshot_Wikipedia_Europe_contemporary_definition_2023-08-01.png?raw=true "Countries of Europe")
  