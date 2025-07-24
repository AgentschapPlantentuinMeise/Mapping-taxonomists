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
