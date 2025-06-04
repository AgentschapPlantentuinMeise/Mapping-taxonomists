# TETTRIs WP3, task 3.2: automatic mapping of taxonomic expertise
This repository contains the scripts used to find European authors of taxonomic articles, identify the species they study, and compare their taxa of expertise to some demands for taxonomic expertise.

## Prerequisites
Before starting you need to download the GBIF taxonomic backbone, unzip it and put the contents in the folder data/external/backbone

You may also need to install SPARQLWrapper, geopandas and fiona to your Python installation, i.e. using `pip install SPARQLWrapper`

## Configuration
The dates between which the workflow will extract publications is set within the config.json file.
The one and two word "keywords" are also set within the config file.
The OpenAlex concept values are set within config.json
The two letter country codes (ISO 3166-1 alpha-2) on which to conduct the analyis are listed in file included_countries.txt within the ./src/supply/ directory

To reuse or repurpose this script these configutations may need changing. However, if the script is to be repurposed for a subject other than biological taxonomy then list_journals.py would need rewriting or replacing, because it is focused on taxonomic journals.

## "Supply" of taxonomic expertise
This analysis can be replicated by running `make_dataset.py` from the `src` folder. This file runs, in order, the following files:

### 1.  `list_journals.py` finds taxonomic journals through WikiData and OpenAlex

#### Data Retrieval
We employed a three-fold approach to gather taxonomic journals:

- **Wikidata query for journals with taxonomic subjects:** using the SPARQL query language, we constructed queries to retrieve scientific journals (Q5633421) or academic journals (Q737498) from Wikidata with main subjects (P921) or fields of work (P101) related to taxonomy. These subjects could be one of the following concepts: taxonomy (Q8269924); biological classification (Q11398); plant taxonomy (Q1138178) and animal taxonomy (Q1469725); biological (Q522190), botanical (Q3310776) and zoological (Q3343211) nomenclature; systematics (Q3516404), phylogenetics (Q171184) and animal phylogeny (Q115135896).

- **Wikidata query for journals with IPNI or ZooBank publication IDs:** we queried Wikidata for journals (again Q5633421 or Q737498) that possess an International Plant Names Index (IPNI) or ZooBank publication ID. IPNI and ZooBank are pivotal in the field of taxonomy for the formal naming of plants and animals; any publication included in their databases is likely related to taxonomy. 

- **OpenAlex query for journals with taxonomic concepts:** We accessed the OpenAlex API to retrieve journals associated with the taxonomy concept (concepts.id:C58642233). The results were filtered to include only sources categorized as journals, excluding non-journal entities like e-book platforms. The OpenAlex data added another valuable dimension to the dataset by linking additional open-access sources of taxonomic literature.

These queries extracted relevant metadata, such as journal titles, ISSN numbers, OpenAlex IDs, country of publication, and whether or not the publication was dissolved.

#### Data Homogenization
To ensure consistency across data from different sources, we applied a series of preprocessing steps:

Wikidata: 
- Metadata from the Wikidata results, such as journal URLs, ISSN-L, and publication IDs, were often nested in dictionaries. We flattened this structure and standardized column names.
- **OpenAlex IDs** for journals were updated from the older ID format (e.g. V123 to S123). This step ensured uniformity across sources when cross-referencing journal identifiers.
- We replaced Wikidata **country** objects with more standardized two-letter codes (ISO 3166-1 alpha-2 code, e.g. BE). 

OpenAlex: 
- The columns of the data were aligned with the Wikidata columns, including adding empty columns for IPNI and ZooBank publication IDs (OpenAlex does not record these IDs).
- (Handling Dissolved Journals: Journals marked as dissolved in the metadata were flagged and a boolean column was added to indicate whether a journal had ceased publication before 2013, a key year for our study's scope.)

These datasets were concatenated into a unified dataframe. 

To prevent redundancy, we performed deduplication based on unique combinations of Wikidata and OpenAlex IDs. The resulting dataset provides a robust list of taxonomic journals.

The final dataset was saved in two formats: a complete list and a deduplicated list, ensuring a clean and comprehensive repository of taxonomic journals.


### 2.  `get_articles.py` extracts articles about taxonomy from these journals

show API URL!

#### Data Collection
We used the OpenAlex API to get articles published in the taxonomic journals found above. This query included several filters:
- `primary_location.source.id`: the source of the articles is one of the taxonomic journals, identified by OpenAlex ID. This meant that we could only use journals with an associated OpenAlex ID.
- `authorships.countries`: at least one of the authors is European. The list of countries included can be found in `src/supply/included_countries.txt`.
- `from_publication_date` and `to_publication_date`: the articles were published between 1 January 2014 and 31 December 2023.
- `mailto`: we required an email address to be included in the query since this is good practice, especially when downloading a large amount of data.

The articles were downloaded in batches, splitting the dataset every 10 000 articles. PLOS ONE was handled first and separately due to its high volume of taxonomic articles.

For each batch of articles, the raw data was saved, a keyword filter was applied and the keyword-filtered articles were stored in intermediate files.

This keyword filter kept the following articles:
- Articles with the words "taxonomy", "taxonomic", "taxon" or "checklist" in their title or abstract;
- Articles with the word "nov." in their abstract;
- Articles with the word groups "new species", "novel species", "new genus" or "new genera" in their title or abstract;
- And articles associated with one of the following concepts: taxonomy (C58642233), taxon (C71640776) or checklist (C2779356329).

Sidenote: the abstracts are stored on OpenAlex in an inverted index format, meaning the abstract is stored as a dictionary with each word in the text as a key and its positions (indices) in the text as values. 
Thus, each abstract was first reconstructed into a full text so word groups could be found. 

Any duplicate articles were dropped. Finally, all keyword-filtered articles were merged into a single dataframe. This dataframe was then "flattened" to create a clean structure, ensuring that nested metadata was properly extracted and that the articles were formatted uniformly for analysis.

### 3.  `parse_taxonomy.py` parses the abstracts of the articles for species names

The abstracts in the dataset were stored in an inverted index format, which is a structured and compressed representation of the text. To facilitate the parsing process, these indexed abstracts needed to be converted back into plain text.
The converted abstracts were then added to the dataframe in a new column, `abstract_full_text`, providing easy access to the full text for subsequent processing.

The GBIF (Global Biodiversity Information Facility) taxonomic backbone was used as the reference for identifying taxonomic subjects within the articles. This backbone includes a comprehensive list of species names and higher taxa, which are crucial for determining if an article mentions a recognized species.

We parsed both the abstract and title of each article for mentions of species recorded in the GBIF taxonomic backbone. This was done using regular expressions: scanning the text for any word groups capitalized like *Genus species*, matching candidates to the GBIF taxonomic backbone, and scanning the text again for further mentions of other species of the same genus, structured like *G. species*. 

This way, we added metadata to the articles, indicating which species or taxonomic subjects were identified in each article.

### 4.  `get_authors.py` which extracts the authors from these articles
#### Global Author Extraction
1. **Loading Taxonomic Articles**:  
   The script begins by loading a pre-processed dataset of taxonomic articles, which includes articles where taxonomic subjects, such as species, have been identified. This dataset is stored in the `taxonomic_articles_with_subjects.pkl` file and contains the necessary metadata, including author information.

2. **Extracting Authors**:
   The next step is to extract the **author information** from each article using the `get_authors` function from the custom `prep_authors` package. This function scans through the articles and compiles a list of all contributing authors.

3. **Isolating Single Authors**:  
   Once the complete list of authors is generated, we use the `get_single_authors` function to filter out instances where an author is listed multiple times across different articles. This function ensures that each author appears only once in the output, allowing us to obtain a unique list of taxonomic authors.

4. **Storing Global Author Data**:  
   The global author data is saved in two intermediate files:
   - **`all_authors_of_taxonomic_articles.pkl`**: This file contains the complete list of authors across all taxonomic articles.
   - **`single_authors_of_taxonomic_articles.pkl`**: This file contains the deduplicated list of authors, ensuring each author appears only once.

   These files are stored in the **`interim`** directory for further analysis or processing.

#### European Author Extraction
The countries included in the analysis are listed by there two-letter ISO code (ISO 3166-1) in file `included_countries.txt`, in directory `.\src\data`.

5. **Processing European Articles**:  
   Although the section processing European taxonomic articles is commented out, the intended steps are as follows:
   - A separate dataset of **European taxonomic articles** (stored in `european_taxonomic_articles_with_subjects.pkl`) would be loaded.
   - Similar to the global workflow, the authors of these articles would be extracted using the `get_authors` function, and single authors would be isolated using `get_single_authors`.

6. **Filtering by Country**:  
   The key feature of this section is the extraction of authors based on their country of affiliation. The **`get_country_authors`** function filters the global author dataset to retain only those authors associated with specific countries (likely European countries). This allows for a geographically-targeted analysis of taxonomic research.

7. **Deduplicating European Authors**:  
   The **`get_single_authors`** function is applied again, this time on the European dataset, to ensure that authors are uniquely represented. This deduplicated list of European authors is particularly valuable for generating insights into regional taxonomic research.

8. **Storing European Author Data**:  
   The results for the European authors are saved in the following files:
   - **`country_authors_with_all_taxonomic_articles.pkl`**: This file contains all the authors from selected countries.
   - **`country_taxonomic_authors_no_duplicates.pkl`**: This file contains the deduplicated list of country-specific authors.
   - **`country_taxonomic_authors_no_duplicates.tsv`**: The deduplicated list is also saved as a TSV file for easy sharing and inspection.

### 5.  `disambiguate.py` which disambiguates said authors

This script aims to disambiguate authors from taxonomic articles and link them to the GBIF taxonomic backbone. The workflow involves preprocessing author names, linking them to species they study, and resolving duplicates by matching authors based on their affiliations and taxonomic subjects. The process also involves clustering similar authors to eliminate redundant entries while retaining accurate information about their research.

#### Authors

1. **Loading and Simplifying the Dataset**:  
   The dataset containing taxonomic authors is loaded from the `country_taxonomic_authors_no_duplicates.pkl` file. Unnecessary columns are dropped, and the remaining columns include key fields like `author_id`, `author_display_name`, `author_orcid`, `inst_id` (institution ID), and `species_subject`.

2. **Generating Truncated and Stripped Names**:  
   For each author, the script generates two new forms of their name:
   - **Truncated Name**: This consists of the first initial and the last name.
   - **Stripped Name**: This is the author’s full name with spaces, periods, and hyphens removed, ensuring consistency across variations of the same name.
   
   These names help in matching authors with minor variations in name formatting.

#### GBIF Taxonomic Backbone

3. **Loading the Taxonomic Backbone**:  
   The GBIF taxonomic backbone, containing species names and taxonomic ranks, is loaded from the `Taxon.tsv` file. Unnecessary columns are dropped, and only species with non-ambiguous taxonomic statuses are retained.

4. **Building a Dictionary for Faster Lookup**:  
   A dictionary (`seen_species`) is created where species names are keys, and their taxonomic order or family is the value. This allows for efficient matching between species names and taxonomic orders in later steps.

5. **Linking Authors to Taxonomic Orders**:  
   Each author is linked to the taxonomic orders of the species they study. The script iterates over every author and, for each species they study, adds the corresponding taxonomic order (or family if no order is available) from the GBIF backbone. Duplicate taxonomic orders are avoided.

6. **Matching Authors**:  
   The `match` function compares two authors to determine if they are likely the same person. The matching criteria are:
   - If both authors have no taxonomic orders associated with them, they are considered the same only if their institution and full name match.
   - If both have known taxonomic orders, they are considered the same if they share both an institution and at least one taxonomic order.

7. **Clustering Similar Authors**:  
   The `cluster` function groups similar authors into clusters based on their names, institutions, and taxonomic orders. These clusters represent potential duplicates of the same author.

8. **Resolving Duplicates**:  
   The script identifies duplicate authors by checking for matching truncated names. For each set of duplicates, it uses the `match` function to determine which authors are the same and clusters them together.

9. **Merging Author Information**:  
   For each cluster of duplicate authors, the script merges the information into a single record. The `collect_values` function ensures that information from all duplicates is combined without redundancy, especially for taxonomic orders and species subjects.

10. **Saving the Results**:  
    - The **merged people** (authors identified as duplicates and merged) are stored in `merged_people_truncated.csv`.
    - The final, disambiguated list of authors is saved as:
      - `authors_disambiguated_truncated.pkl`
      - `authors_disambiguated_truncated.tsv`

#######################################################################################

## Demand for taxonomists

### Crop Wild Relatives

The crop wild relatives data where downloaded from the following dataset and placed in `data/external/crop wild relatives europe.xlsx`. These are public domain data, but are included here as a test dataset. We recommend anyone useing these scripts updates this file from source.

> USDA, Agricultural Research Service, National Plant Germplasm System. 2024. Germplasm Resources Information Network (GRIN Taxonomy). National Germplasm Resources Laboratory, Beltsville, Maryland. URL: https://npgsweb.ars-grin.gov/gringlobal/taxon/taxonomysearchcwr. Accessed 15 October 2024.

### IUCN Red List of Threatened Species

The "Research needed: taxonomy" data were downloaded from the IUCN Red List website as the file assessments.csv. These data are made available under the IUCN Red List Terms and Conditions for non-commercial use only, and redistribution is not permitted. Therefore, we cannot provide the input data directly here.

However, the data are used in their original format, as provided in the CSV file, with the following headers:
`assessmentId,internalTaxonId,scientificName,redlistCategory,redlistCriteria,yearPublished,assessmentDate,criteriaVersion,language,rationale,habitat,threats,population,populationTrend,range,useTrade,systems,conservationActions,realm,yearLastSeen,possiblyExtinct,possiblyExtinctInTheWild,scopes`

> IUCN. 2024. The IUCN Red List of Threatened Species. Version 2024-1. https://www.iucnredlist.org/. Accessed on [17 October 2024].

### Invasive alien species on the horizon in the European Union
Invasive species on the horizon were extracted from the supporting information table 7, titled "Preliminary species list 2: 120 species listed" . Accessed on [20 October 2024].

Roy HE, Bacher S, Essl F, et al. Developing a list of invasive alien species likely to threaten biodiversity and ecosystems in the European Union. *Glob Change Biol.* 2019; 25: 1032–1048. https://doi.org/10.1111/gcb.14527

### The Birds Directive
The file `birds_directive_annexi+gbif.csv` was used from https://github.com/linamaes/sps_taxonomy_plots_Task1d5 that were prepared for the report
Estupinan-Suarez, L. M., Groom, Q., Pereira, H., Preda, C., Rodrigues, A., Sica, Y., Teixeira, H., Yovcheva, N. & Fernandez, M. Alignment of B3 with European Biodiversity Initiative: Insights from EU policy.

### The Habitat Directive
The file `habitats_directive_art_17_checklis+gbif.csv` was used from https://github.com/linamaes/sps_taxonomy_plots_Task1d5 that were prepared for the report
Estupinan-Suarez, L. M., Groom, Q., Pereira, H., Preda, C., Rodrigues, A., Sica, Y., Teixeira, H., Yovcheva, N. & Fernandez, M. Alignment of B3 with European Biodiversity Initiative: Insights from EU policy.

### The EU Marine Strategy Framework Directive
The file `MSFD_descriptor1+worms.csv` was used from https://github.com/linamaes/sps_taxonomy_plots_Task1d5 that were prepared for the report
Estupinan-Suarez, L. M., Groom, Q., Pereira, H., Preda, C., Rodrigues, A., Sica, Y., Teixeira, H., Yovcheva, N. & Fernandez, M. Alignment of B3 with European Biodiversity Initiative: Insights from EU policy.

### The List of invasive alien species of Union concern
The file `IAS_list_union_concern+gbif.csv` was used from https://github.com/linamaes/sps_taxonomy_plots_Task1d5 that were prepared for the report
Estupinan-Suarez, L. M., Groom, Q., Pereira, H., Preda, C., Rodrigues, A., Sica, Y., Teixeira, H., Yovcheva, N. & Fernandez, M. Alignment of B3 with European Biodiversity Initiative: Insights from EU policy.

### The EU Pollinators Initiative
The file `pollinators_sps_list_Reverte_et_al_insect_conservation&diversity_2023.csv` was used from https://github.com/linamaes/sps_taxonomy_plots_Task1d5 that were prepared for the report
Estupinan-Suarez, L. M., Groom, Q., Pereira, H., Preda, C., Rodrigues, A., Sica, Y., Teixeira, H., Yovcheva, N. & Fernandez, M. Alignment of B3 with European Biodiversity Initiative: Insights from EU policy.

### European Red Lists of species
The European Red Lists of species was downloaded from the [European Environment Agency Datahub](https://sdi.eea.europa.eu/data/9c785326-8859-4abd-aad6-c8d35b619ff9).
The name of the file is `european_red_list_2017_december.csv`. Accessed on [04 June 2025].

![A diagram of the connections between scripts that generate the phylogenetic trees of policies and taxonomists](policies_flow.png)

#######################################################################################

## Visualization
  
### maps.py Country Frequency

This Python script analyzes and visualizes the geographic distribution of authors' institutions by plotting country frequencies on maps. It processes the input data, calculates the frequency of authors by country, and generates maps displaying these distributions using **Geopandas** and **Matplotlib**.

#### Key Features

1. **Frequency Calculation**: 
   The script includes a function `freq_countries` that processes a dataset of authors' institution country codes and calculates how frequently each country appears. It returns this information in a dictionary that links country codes to their respective author counts.

2. **Map Generation**:
   The core functionality of the script is to visualize these frequencies on maps. Using **GeoPandas**, the script loads a world map and maps each country’s author frequency onto it. Additionally, it supports generating maps that focus on Europe, as well as creating visualizations based on the relative frequency of authors (e.g., percentage of the population).

3. **Custom Color Mapping**:
   The script includes a custom color gradient, ranging from light green to dark blue, that is used in the maps to represent the frequency data, making it easier to differentiate regions with higher author counts.

#### Input Data

The script requires two main input datasets, which are expected to be in pickle format:
1. **`single_authors_of_taxonomic_articles.pkl`**: This dataset contains information about authors of taxonomic articles, including the countries of their institutions.
2. **`country_taxonomic_authors_no_duplicates.pkl`**: This dataset is similar but contains a filtered version without duplicates, focusing on European authors.

Additionally, a **country codes** file (`country_codes.tsv`) is used to convert between different country code formats for proper map plotting.

#### Output

The script produces several types of maps:
- A **global map** that shows the number of authors per country.
- A **European map** that zooms in on Europe and highlights country frequencies.
- A **relative map** for Europe that shows author frequencies as a percentage of the country’s population.
- Specialized maps for authors from the **EUJOT journal**, again including both absolute and relative frequencies.

All of these maps are saved as PNG files and stored in the `../../reports/figures/` directory.

#### Conclusion

Once the script is run, you’ll find a series of maps that visually represent where authors of taxonomic articles are based, both globally and within Europe. The resulting visualizations offer an insightful view into the geographic distribution of the academic community in this field.

### Open Access status of taxonomic articles


