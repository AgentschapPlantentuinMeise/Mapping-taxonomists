setwd("C:/Users/melanie/Documents/GitHub/TETTRIs-mapping-taxonomists")

library(metacoder)

data <- readxl::read_xlsx("data/processed/krona_IUCN_redlist_needsresearch_authors.xlsx")
colnames(data) <- c("taxon_id","kingdom","needsResearch","numberAuthors","phylum","class","order","family")
data <- data[,c(2,5,6,7,8,3)]

obj <- parse_tax_data(data, class_cols = 1:5)
obj

obj$data$taxon_counts <- calc_taxon_abund(obj, data = "tax_data")
obj$data$taxon_counts$total <- rowSums(obj$data$taxon_counts[, -1])


set.seed(1) # This makes the plot appear the same each time it is run 
heat_tree(obj, 
          node_label = taxon_names,
          node_size = n_obs,
          node_color = total, 
          node_size_axis_label = "IUCN count",
          node_color_axis_label = "Samples with reads",
          layout = "davidson-harel", # The primary layout algorithm
          initial_layout = "reingold-tilford") # The layout algorithm that initializes node locations

# normalize
# colour blind red
# node size but stay at family level
