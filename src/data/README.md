## Running the data source code

The following scripts are packages:
 - `download.py` contains functions for downloading data from OpenAlex or Wikidata, for both journals and articles.
 - `prep_journals.py` contains functions for preprocessing the list of journals. This mainly involves homogenizing the data so that OpenAlex and Wikidata journals are comparable, as well as functions to e.g. decide whether a journal is recently dissolved or not.
 - `prep_articles.py` contains functions for preprocessing articles downloaded from OpenAlex, primarily to extract European articles and articles containing keywords like "new species", "taxonomy", etc. 
- `prep_authors.py` contains functions for extracting (European) authors from the articles previously downloaded and deduplicate them.

 The other scripts execute the above functions. They are best run in the following order:
 1. `list_journals.py` makes a final list of relevant taxonomic journals, which is saved as data/processed/journals.csv
 2. `make_dataset.py` downloads all recent (10 years) articles from the above journals via the OpenAlex API. The results are saved in separate chunks in data/raw/articles. It also filters these articles for certain taxonomic keywords and word groups and filters out any articles without European authors. This dataset is more manageable and is saved in its entirety in data/interim.
 3. `extract_authors.py` extracts the authors from these articles and keeps European authors, linked to their most recent article. Each of these intermediate datasets (all authors/European authors/deduplicated authors/...) is saved in data/interim. 
 ?.  Finally, `replicate_rlit.py` runs a different analysis, more analogous to the methodology used for the Red List of Insect Taxonomists (https://cloud.pensoft.net/s/mGpyQYUPQOMPs8C).
 
 "European" is defined as coming from the countries in black on this map:
 
![European countries, according to https://en.wikipedia.org/wiki/Europe#Contemporary_definition] (./Screenshot_Wikipedia_Europe_contemporary_definition_2023-08-01.png ?raw=true "Title")
  