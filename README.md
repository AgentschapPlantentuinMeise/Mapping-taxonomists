# TETTRIs-mapping-taxonomists
TETTRIs WP3, task 3.2: automatic mapping of taxonomic expertise

Before starting you need to download the GBIF taxonomic backbone, unzip it and put the contents in the folder data/external/backbone

The backbone DOI should be cited in any resulting publication. An example citation is below, but consider that the backbone is rebuilt periodically. 

> GBIF Secretariat (2023). GBIF Backbone Taxonomy. Checklist dataset https://doi.org/10.15468/39omei accessed via GBIF.org on 2024-08-14.

You may also need to install SPARQLWrapper, geopandas and fiona to your Python installation.

i.e. using `pip install SPARQLWrapper`

The countries included in the analysis are listed by there two-letter ISO code (ISO 3166-1) in file `included_countries.txt`, in directory `.\src\data`.

This analysis can be replicated by copying the repository and running `make_dataset.py` from the `src` folder. This file runs, in order, the following files:
## 1.  `list_journals.py` which finds possible taxonomic journals through WikiData and OpenAlex

### Data Retrieval
We employed a two-fold approach to gather taxonomic journals:
Wikidata Query for Taxonomic Subjects: Using the SPARQL query language, we constructed queries to retrieve journals from Wikidata associated with taxonomy-related concepts. These concepts were identified by their respective Wikidata identifiers, including taxonomy (Q8269924), biological classification (Q11398), plant taxonomy (Q1138178), animal taxonomy (Q1469725), and several others. Due to the complexity of the query and data size, the query was split into two parts to accommodate additional concepts such as systematics (Q3516404) and phylogenetics (Q171184).
Wikidata Query for IPNI and ZooBank Identifiers: In addition to subject-based searches, we queried Wikidata for journals that possess an International Plant Names Index (IPNI) or ZooBank publication identifier. These identifiers are pivotal in the field of taxonomy for the formal naming of plants and animals. The query extracted relevant metadata, such as journal titles, ISSN numbers, and geographical information, as well as IPNI and ZooBank IDs.

OpenAlex Query for Taxonomy-Related Journals: We accessed the OpenAlex API to retrieve journals associated with the taxonomy concept (concepts.id). The results were filtered to include only sources categorized as journals, excluding non-journal entities like e-book platforms. The OpenAlex data added another valuable dimension to the dataset by linking additional open-access sources of taxonomic literature.

### Data Homogenization
To ensure consistency across data from different sources, we applied a series of preprocessing steps:

Wikidata Value Extraction: Metadata from the Wikidata results, such as journal URLs, ISSN-L, and publication IDs, were often nested in dictionaries. We extracted these values using a custom function to flatten the structure and standardize column names.

OpenAlex ID Standardization: The OpenAlex data was processed to update older ID formats (e.g., V123 to S123) and align these with the Wikidata format. This step ensured uniformity across sources when cross-referencing journal identifiers.

Handling Dissolved Journals: Journals marked as dissolved in the metadata were flagged and a boolean column was added to indicate whether a journal had ceased publication before 2013, a key year for our study's scope.

### Data Integration and Deduplication
Following the extraction and homogenization of data from both Wikidata and OpenAlex, the datasets were concatenated into a unified dataframe. We retained essential columns such as journal title, ISSN-L, IPNI and ZooBank publication IDs, OpenAlex IDs, and dissolution status.

To prevent redundancy, we performed deduplication based on unique combinations of Wikidata and OpenAlex identifiers. The resulting dataset provides a robust list of taxonomic journals, capturing diverse metadata and identifiers crucial for further bibliometric analyses.

The final dataset was saved in two formats: a complete list and a deduplicated list, ensuring a clean and comprehensive repository of taxonomic journals.

## 2.  `get_articles.py` which extracts the articles from these journals and filters out articles about taxonomy, as well as filtering out  

### Data Collection
The process of obtaining taxonomic articles was divided into several steps:
1. Journals Data Preparation: We began by loading a previously curated dataset of taxonomic journals from Wikidata and OpenAlex. This dataset, stored in journals.csv, contained key metadata about journals, including their OpenAlex IDs and dissolution status. Only journals that had valid OpenAlex IDs and were still active during the study period (i.e., not dissolved) were included in the query process.
2. Directory Cleanup: To ensure that the new data collected was clean and not mixed with previous results, we cleared the directory containing raw article files by removing all files stored in the articles directory.
3. Querying OpenAlex for Journal Articles: The next step involved querying the OpenAlex API to obtain articles from each taxonomic journal. This was done for journals with valid OpenAlex IDs and for articles published between 2013 and 2022. We excluded PLOS ONE from the general search as it has a large number of taxonomic articles (~240,000) and handled it separately.
4. Handling PLOS ONE: Due to its high volume of taxonomic articles, PLOS ONE articles were retrieved first and filtered using a custom keyword filter to identify taxonomic articles that met specific criteria. These filtered articles were stored in intermediate files for further processing.
5. Downloading Articles in Batches: For each journal in the dataset, we queried OpenAlex for articles using the journal's OpenAlex ID. We kept track of the total number of articles downloaded in each batch, splitting the dataset every time 10,000 articles were retrieved. For each batch of articles:
* The raw data was saved.
* A keyword filter was applied to extract taxonomic articles based on predefined keywords.
* The keyword-filtered articles were stored in intermediate files.
6. Final Download and Processing: After downloading all articles from the selected journals, the final batch of articles was processed similarly by applying the keyword filter and saving the results. All keyword-filtered articles were merged to create a single unified dataset of taxonomic articles.

### Data Processing and Filtering
Once all articles had been downloaded and filtered, the following processing steps were applied:
1. Merging and Flattening: The keyword-filtered articles were merged into a single dataframe using the merge_pkls function from the prep_articles module. The resulting articles were then "flattened" to create a clean structure, ensuring that nested metadata was properly extracted and that the articles were formatted uniformly for analysis.
2. European Taxonomic Articles: Although not fully implemented in the provided code, a filter for European articles (filter_eu_articles) could be applied to isolate articles relevant to European taxonomic research. This step would involve filtering based on geographical information or institutional affiliations.

## 3.  `parse_taxonomy.py` which parses the abstracts of these articles for species names

### Data Preparation
1. Loading Filtered Articles: The dataset containing filtered taxonomic articles was loaded from a pre-processed pickle file (filtered_articles.pkl). This dataset includes articles that had already been filtered based on their relevance to taxonomy through a keyword-based process.

2. Abstract Conversion: The abstracts in the dataset were stored in an inverted index format, which is a structured and compressed representation of the text. To facilitate the parsing process, these indexed abstracts needed to be converted back into plain text. The script iterated over each article and checked if the abstract was available in an inverted index format.
* If the abstract was present, the `inverted_index_to_text` function from the `prep_taxonomy` package was used to reconstruct the full abstract text.
* If no abstract was available, a `None` value was assigned to that entry.
The converted abstracts were then added to the dataframe in a new column, `abstract_full_text`, providing easy access to the full text for subsequent processing.

### Taxonomic Subject Parsing
3. GBIF Taxonomic Backbone: The GBIF (Global Biodiversity Information Facility) taxonomic backbone was used as the reference for identifying taxonomic subjects within the articles. This backbone includes a comprehensive list of species names and higher taxa, which are crucial for determining if an article mentions a recognized species.

The backbone was pre-processed using the `preprocess_backbone` function from the `prep_taxonomy` package, ensuring that the data was clean and structured for efficient parsing.

4. Parsing Articles for Taxonomy: The core of the workflow involved parsing both the abstract and title of each article for mentions of species recorded in the GBIF taxonomic backbone. This was achieved through the `parse_for_taxonomy` function, which:

Searched each article's title and abstract for references to species or other taxonomic entities.
Cross-referenced these mentions with the GBIF backbone to confirm if the mentioned species or taxa were officially recognized.
The function added metadata to the articles, indicating which species or taxonomic subjects were identified in each article.

## 4.  `get_authors.py` which extracts the authors from these articles
## 5.  `disambiguate.py` which disambiguates said authors

