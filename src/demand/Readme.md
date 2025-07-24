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

![A diagram of the connections between scripts that generate the phylogenetic trees of policies and taxonomists](../policies_flow.png)

### `count_demand_supply.py` Matching Taxonomic Supply with Policy Demand

This comprehensive script quantifies and compares the **supply** of taxonomic expertise (i.e., authorship on species) with **demand** indicated by conservation and policy priorities. It builds a unified dataset linking taxa to research needs and outputs a taxonomic matrix for further analysis and visualization.

#### Purpose

To generate a taxonomic matrix linking species and higher taxa (especially orders) to:

* Taxonomic research supply (i.e., number of taxonomic authors per species/order)
* Demand indicators from major EU and international biodiversity policies

This matrix supports downstream analyses such as phylogenetic coverage heatmaps and gap assessments.

#### Workflow Summary

1. **Input Data**:

   * GBIF taxonomic backbone: `Taxon.tsv`
   * Author data: `authors_disambiguated_truncated.pkl`
   * Policy datasets (e.g., IUCN, CWR, Birds Directive, etc.)

2. **Standardization of Species Names**:

   * Uses `pygbif` to retrieve canonical names for species mentioned in author and policy datasets.
   * Standardizes names and logs unmatched species to `unmatched_species.csv`.

3. **Linking Authors to Taxa**:

   * Tallies how many disambiguated authors have published on each species.
   * Aggregates these counts by taxonomic order.

4. **Linking Policy Demand to Taxa**:

   * Extracts species of concern from multiple policy sources:

     * IUCN Red List (taxonomy research needed)
     * Crop Wild Relatives
     * Horizon scanning invasive species
     * Birds Directive, Habitats Directive, Marine Strategy, Pollinator lists, and more
   * Standardizes and matches these species to the GBIF backbone.

5. **Aggregation to Order Level**:

   * Totals demand and supply indicators across taxonomic orders (excluding Bacteria and Archaea).
   * Produces a `supply_and_demand_order_level.pkl` and `.tsv`.

6. **Output for Visualization**:

   * **`taxAssignments.txt`**: List of OTUs (taxonomic units) with taxonomic lineage and IDs, used for visual tools like iTOL.
   * **`otutable.tsv`**: Matrix of taxonomic orders vs. counts of authors and species appearing in different policy datasets.

#### Output Files

* `taxAssignments.txt`: Lineage per OTU ID with confidence annotations.
* `otutable.tsv`: Main output matrix of taxonomic orders × policy indicators and author counts.
* `supply_and_demand_order_level.tsv`: Raw order-level summary of supply and demand.
* `unmatched_species.csv`: Log of species names not found in GBIF during standardization.

#### Example Indicators in Final Matrix

| OTU\_ID | nr\_authors | taxonomicResearchNeeded | cropWildRelatives | ... |
| ------- | ----------- | ----------------------- | ----------------- | --- |
| 1       | 32          | 12                      | 4                 | ... |
