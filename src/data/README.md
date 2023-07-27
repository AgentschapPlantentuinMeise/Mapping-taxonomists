## Running the data source code

The following scripts are packages:
 - `download.py` contains functions for downloading data from OpenAlex or Wikidata, for both journals and articles.
 - `preprocessing_journals.py` contains functions for preprocessing the list of journals. This mainly involves homogenizing the data so that OpenAlex and Wikidata journals are comparable, as well as functions to e.g. decide whether a journal is recently dissolved or not.
 - `preprocessing_articles.py` contains functions for preprocessing articles downloaded from OpenAlex, primarily to extract (European) authors and deduplicate them. 
 
 The other scripts execute the above functions. They are best run in the following order:
 1. `list_journals.py` makes a final list of relevant taxonomic journals, which is saved as data/processed/journals.csv
 2. `make_dataset.py` downloads all recent (10 years) articles from the above journals via the OpenAlex API. The results are saved in separate chunks in data/raw/articles. It also filters these articles for certain taxonomic keywords and word groups and filters out any articles without European authors. This dataset is more manageable and is saved in its entirety in data/interim.
 3. 
 