# TETTRIs-mapping-taxonomists
TETTRIs WP3, task 3.2: automatic mapping of taxonomic expertise

Before starting you need to download the GBIF taxonomic backbone, unzip it and put the contents in the folder data/external/backbone

The backbone DOI should be cited in any resulting publication. An example citation is below, but consider that the backbone is rebuilt periodically. 

> GBIF Secretariat (2023). GBIF Backbone Taxonomy. Checklist dataset https://doi.org/10.15468/39omei accessed via GBIF.org on 2024-08-14.

You may also need to install SPARQLWrapper, geopandas and fiona to your Python installation.

i.e. using `pip install SPARQLWrapper`

The countries included in the analysis are listed by there two-letter ISO code (ISO 3166-1) in file `included_countries.txt`, in directory `.\src\data`.

This analysis can be replicated by copying the repository and running `make_dataset.py` from the `src` folder. This file runs, in order, the following files:
1.  `list_journals.py` which finds possible taxonomic journals through WikiData and OpenAlex

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

2.  `get_articles.py` which extracts the articles from these journals and filters out articles about taxonomy, as well as filtering out  
3.  `parse_taxonomy.py` which parses the abstracts of these articles for species names
4.  `get_authors.py` which extracts the authors from these articles
5.  `disambiguate.py` which disambiguates said authors

