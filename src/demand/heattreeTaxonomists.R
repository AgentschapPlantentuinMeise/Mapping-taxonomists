library(readr) # Loads the readr package so we can use `read_tsv`
library(dplyr) # Loads the dplyr package so we can use `left_join`
library(metacoder)

library(rcartocolor)
library(grid)
library(gridExtra)
library(ggplot2)

otu_data <- read_tsv("otutable.tsv") # You might need to change the path to the file
print(otu_data) # You can also enter just `otu_data` to print it
tax_data <- read_tsv("taxAssignments.txt")
print(tax_data) # You can also enter `tax_data` to print it


tax_data$OTU_ID <- as.character(tax_data$OTU_ID) # Must be same type for join to work
otu_data$OTU_ID <- as.character(otu_data$OTU_ID) # Must be same type for join to work
otu_data <- left_join(otu_data, tax_data,
                      by = c("OTU_ID" = "OTU_ID")) # identifies cols with shared IDs
print(otu_data)

sample_data <- read_tsv("SMD.txt",
                        col_types = "cccccc") # each "c" means a column of "character"
print(sample_data) # You can also enter `sample_data` to print it

obj <- parse_tax_data(otu_data,
                      class_cols = "taxonomy", # The column in the input table
                      class_sep = ";") # What each taxon is seperated by
print(obj)
print(obj$data$tax_data)

obj <- parse_tax_data(otu_data,
                      class_cols = "taxonomy",
                      class_sep = ";",
                      class_regex = "^([a-z]{0,1})_{0,2}(.*)$",
                      class_key = c("tax_rank" = "taxon_rank", "name" = "taxon_name"))
print(obj)
head(taxon_names(obj))
obj$data$class_data
head(taxon_ranks(obj))
names(obj$data) <- "otu_counts"
print(obj)

heat_tree(obj,
          node_label = taxon_names,
          node_size = n_obs,
          node_color = n_obs)

obj$data$tax_abund <- calc_taxon_abund(obj, "otu_counts",
                                       cols = sample_data$SampleID,
                                       groups = sample_data$type)
print(obj$data$tax_abund)

names(obj$data)[2] <- "taxonomy_table"
#orders <- obj$data$taxonomy_table %>% filter(tax_rank == "o") %>% pull(name)
dontprint <- obj$data$taxonomy_table %>% filter(tax_rank %in% c("o", "c")) %>% pull(name)

dontprint <- c(dontprint, c("Langiophytophyta", "Zoopagomycota", "Xenacoelomorpha", "Loricifera", "Ctenophora", "Acanthocephala"))
dontprint <- c(dontprint, c("Blastocladiomycota", "Entomophthoromycota", "Neocallimastigomycota", "Hemichordata", "Sipuncula"))
dontprint <- c(dontprint, c("Mucoromycota", "Priapulida", "Nematomorpha", "Chaetognatha", "Rotifera","Gnathostomulida"))
dontprint <- c(dontprint, c("Placozoa", "Priapulida", "Chytridiomycota","Echinodermata","Sanchytriomycota","Glomeromycota"))
dontprint <- c(dontprint, c("Zygomycota", "Kinorhyncha", "Glaucophyta"))

dontprint <- setdiff(dontprint, c("Liliopsida","Arachnida", "Insecta", "Eurotiomycetes", "Aves", "Dothideomycetes","Sordariomycetes"))
dontprint <- setdiff(dontprint, c("Magnoliopsida", "Florideophyceae", "Agaricomycetes"))

set.seed(4) # Each number will produce a slightly different result for some layouts

message("Plants")
  
# Filter data for the current kingdom
plants <- obj %>%
  filter_taxa(taxon_names %in% "Plantae", subtaxa = TRUE)
  
plantPlot <- heat_tree(plants,
          node_label = ifelse(taxon_names %in% dontprint, "", taxon_names),
          node_label_size_range = c(0.05,0.08),
          #node_color_range=colorRampPalette(c("#c9edde", "#091410"))(10),
          node_size = n_obs,
          node_color = people ,
          edge_label = NA ,
          #tree_label = taxon_names,
          make_node_legend = TRUE,
          node_legend_title = "Test",
          node_size_axis_label = NULL,
          make_edge_legend = FALSE,
          #node_size_digits = -1,
          node_size_range = c(0.01, 0.06),
          edge_size_range = c(0.004, 0.01),
          layout = "davidson-harel"
)

message("Fungi")
set.seed(2)
# Filter data for the current kingdom
fungi <- obj %>%
  filter_taxa(taxon_names %in% "Fungi", subtaxa = TRUE)

fungiPlot <- heat_tree(fungi,
          node_label = ifelse(taxon_names %in% dontprint, "", taxon_names),
          node_label_size_range = c(0.05,0.08),
          #node_color_range=colorRampPalette(c("#c9edde", "#091410"))(10),
          node_size = n_obs,
          node_color = people ,
          edge_label = NA ,
          #tree_label = taxon_names,
          make_node_legend = TRUE,
          node_legend_title = "Test",
          node_size_axis_label = NULL,
          make_edge_legend = FALSE,
          #node_size_digits = -1,
          node_size_range = c(0.01, 0.06),
          edge_size_range = c(0.004, 0.01),
          layout = "davidson-harel"
)

message("Animals")
set.seed(3)
# Filter data for the current kingdom
animalia <- obj %>%
  filter_taxa(taxon_names %in% "Animalia", subtaxa = TRUE)

animalPlot <- heat_tree(animalia,
          node_label = ifelse(taxon_names %in% dontprint, "", taxon_names),
          node_label_size_range = c(0.05,0.08),
          #node_color_range=colorRampPalette(c("#c9edde", "#091410"))(10),
          node_size = n_obs,
          node_color = people ,
          edge_label = NA ,
          #tree_label = taxon_names,
          make_node_legend = TRUE,
          node_legend_title = "Test",
          node_size_axis_label = NULL,
          make_edge_legend = FALSE,
          #node_size_digits = -1,
          node_size_range = c(0.01, 0.06),
          edge_size_range = c(0.004, 0.01),
          layout = "davidson-harel"
)

grid.arrange(plantPlot, fungiPlot, animalPlot, ncol=2)

# Open a TIFF device with 600 DPI resolution
tiff(
  filename = "taxonomists.tif",  # Change path as needed
  width = 2625,                              # Width in pixels
  height= 2625,                              # Height in pixels
  units = "px",                              # Units set to pixels
  res = 300,                               # Resolution in DPI
  bg = "white",
  compression = "lzw"                      # Optional: compression type
)

# Arrange and render the plots
grid.arrange(plantPlot, fungiPlot, animalPlot, ncol=2)

# Close the device to save the file
dev.off()

# Open a PNG device with 600 DPI resolution
png(
  filename = "taxonomists.png", # Change path as needed
  width = 2625,                              # Width in pixels
  height= 2625,                              # Height in pixels
  units = "px",                              # Units set to pixels
  res = 300,                              # Resolution
  bg = "white",
  type = "cairo"                          # Optional: use Cairo graphics
)

# Arrange and render the plots
grid.arrange(plantPlot, fungiPlot, animalPlot, ncol=2)

# Close the device to save the file
dev.off()