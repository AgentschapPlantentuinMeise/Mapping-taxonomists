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

sample_data <- read_tsv("SMD.txt", col_types = "cccccc") # each "c" means a column of "character"

obj <- parse_tax_data(otu_data,
                      class_cols = "taxonomy", # The column in the input table
                      class_sep = ";") # What each taxon is seperated by

obj <- parse_tax_data(otu_data,
                      class_cols = "taxonomy",
                      class_sep = ";",
                      class_regex = "^([a-z]{0,1})_{0,2}(.*)$",
                      class_key = c("tax_rank" = "taxon_rank", "name" = "taxon_name"))

head(taxon_names(obj))

head(taxon_ranks(obj))
names(obj$data) <- "otu_counts"


obj$data$tax_abund <- calc_taxon_abund(obj, "otu_counts",
                                       cols = sample_data$SampleID,
                                       groups = sample_data$type)
print(obj$data$tax_abund)

names(obj$data)[2] <- "taxonomy_table"

#########################################################################

doprint <- c("Animalia", "Plantae", "Fungi", "Aves", "Basidiomycota", "Ascomycota", "Insecta")
doprint <- c(doprint, c("Chordata", "Mollusca", "Bryophyta", "Tracheophyta", "Rhodophyta", "Chromista"))

#########################################################################
#my_vars <- c("conservation", "breeding", "Invasive", "Habitats", 
#             "marineDir", "IAS", "Redlist", "Birds", "pollinators")

# **New Step: Filter Out Order-Level Taxa**
# Remove taxa where tax_rank is "o" (order)
objNoOrders <- filter_taxa(obj, taxon_ranks != "o", supertaxa = TRUE)

objNoMicro <- filter_taxa(objNoOrders, taxon_names %in% c("Chromista", "Bacteria", "Viruses", "Protozoa"), invert = TRUE, subtaxa = TRUE)

objFinal <- filter_taxa(objNoMicro, taxon_names %in% c("Root", "Fungi", "Plantae", "Animalia"), subtaxa = TRUE)

node_label_size <- c(0.07,0.14)
node_size_range <- c(0.01, 0.06)
edge_size_range <- c(0.004, 0.03)
header_color <- "#00008B"
layout <- "graphopt"
seed <- 1
repel_iter = 20000
repel_force = 2
set.seed(seed) # Each number will produce a slightly different result for some layouts
message("Now plotting conservation")

taxonomyNeeded <- heat_tree(objFinal,
          node_label = ifelse(taxon_names %in% doprint, taxon_names, ""),
          node_label_size_range = node_label_size,
          node_size = n_obs,
          node_color = conservation ,
          edge_label = NA ,
          tree_label = "Taxonomy needed",
          tree_label_color = header_color,
          make_node_legend = FALSE,
          node_legend_title = "Test",
          node_size_axis_label = NULL,
          make_edge_legend = FALSE,
          #node_size_digits = -1,
          node_size_range = node_size_range,
          edge_size_range = edge_size_range,
          layout = layout,
          repel_iter = repel_iter,
          repel_force = repel_force
          )
set.seed(seed)
redList <- heat_tree(objFinal,
                            node_label = ifelse(taxon_names %in% doprint, taxon_names, ""),
                            node_label_size_range = node_label_size,
                            node_size = n_obs,
                            node_color = Redlist,
                            edge_label = NA ,
                            tree_label = "European Red List",
                            tree_label_color = header_color,
                            make_node_legend = FALSE,
                            node_legend_title = "Test",
                            node_size_axis_label = NULL,
                            make_edge_legend = FALSE,
                            #node_size_digits = -1,
                            node_size_range = node_size_range,
                            edge_size_range = edge_size_range,
                            layout = layout,
                            repel_iter = repel_iter,
                            repel_force = repel_force
)
set.seed(seed)
cwr <- heat_tree(objFinal,
                     node_label = ifelse(taxon_names %in% doprint, taxon_names, ""),
                     node_label_size_range = node_label_size,
                     node_size = n_obs,
                     node_color = breeding ,
                     edge_label = NA ,
                     tree_label = "Crop Wild Relatives",
                     tree_label_color = header_color,
                     make_node_legend = FALSE,
                     node_legend_title = "Test",
                     node_size_axis_label = NULL,
                     make_edge_legend = FALSE,
                     #node_size_digits = -1,
                     node_size_range = node_size_range,
                     edge_size_range = edge_size_range,
                     layout = layout,
                     repel_iter = repel_iter,
                     repel_force = repel_force
)
set.seed(seed)
OnHorizon <- heat_tree(objFinal,
                            node_label = ifelse(taxon_names %in% doprint, taxon_names, ""),
                            node_label_size_range = node_label_size,
                            node_size = n_obs,
                            node_color = Invasive ,
                            edge_label = NA ,
                            tree_label = "IAS on Horizon",
                            tree_label_color = header_color,
                            make_node_legend = FALSE,
                            node_legend_title = "Test",
                            node_size_axis_label = NULL,
                            make_edge_legend = FALSE,
                            #node_size_digits = -1,
                            node_size_range = node_size_range,
                            edge_size_range = edge_size_range,
                            layout = layout,
                            repel_iter = repel_iter,
                            repel_force = repel_force
)
set.seed(seed)
iasUnionList <- heat_tree(objFinal,
                     node_label = ifelse(taxon_names %in% doprint, taxon_names, ""),
                     node_label_size_range = node_label_size,
                     node_size = n_obs,
                     node_color = IAS ,
                     edge_label = NA ,
                     tree_label = "Union List of Concern",
                     tree_label_color = header_color,
                     make_node_legend = FALSE,
                     node_legend_title = "Test",
                     node_size_axis_label = NULL,
                     make_edge_legend = FALSE,
                     #node_size_digits = -1,
                     node_size_range = node_size_range,
                     edge_size_range = edge_size_range,
                     layout = layout,
                     repel_iter = repel_iter,
                     repel_force = repel_force
)
set.seed(seed)
birds <- heat_tree(objFinal,
                 node_label = ifelse(taxon_names %in% doprint, taxon_names, ""),
                 node_label_size_range = node_label_size,
                 node_size = n_obs,
                 node_color = Birds ,
                 edge_label = NA ,
                 tree_label = "Birds Directive",
                 tree_label_color = header_color,
                 make_node_legend = FALSE,
                 node_legend_title = "Test",
                 node_size_axis_label = NULL,
                 make_edge_legend = FALSE,
                 #node_size_digits = -1,
                 node_size_range = node_size_range,
                 edge_size_range = edge_size_range,
                 layout = layout,
                 repel_iter = repel_iter,
                 repel_force = repel_force
)
set.seed(seed)
habitats <- heat_tree(objFinal,
                       node_label = ifelse(taxon_names %in% doprint, taxon_names, ""),
                       node_label_size_range = node_label_size,
                       node_size = n_obs,
                       node_color = Habitats ,
                       edge_label = NA ,
                       tree_label = "Habitats Directive",
                       tree_label_color = header_color,
                       make_node_legend = FALSE,
                       node_legend_title = "Test",
                       node_size_axis_label = NULL,
                       make_edge_legend = FALSE,
                       #node_size_digits = -1,
                       node_size_range = node_size_range,
                       edge_size_range = edge_size_range,
                       layout = layout,
                       repel_iter = repel_iter,
                       repel_force = repel_force
)
set.seed(seed)
marineDir <- heat_tree(objFinal,
                          node_label = ifelse(taxon_names %in% doprint, taxon_names, ""),
                          node_label_size_range = node_label_size,
                          node_size = n_obs,
                          node_color = marine ,
                          edge_label = NA ,
                          tree_label = "Marine Framework Directive",
                          tree_label_color = header_color,
                          make_node_legend = FALSE,
                          node_legend_title = "Test",
                          node_size_axis_label = NULL,
                          make_edge_legend = FALSE,
                          #node_size_digits = -1,
                          node_size_range = node_size_range,
                          edge_size_range = edge_size_range,
                          layout = layout,
                          repel_iter = repel_iter,
                          repel_force = repel_force
)
set.seed(seed)
pollinators <- heat_tree(objFinal,
                   node_label = ifelse(taxon_names %in% doprint, taxon_names, ""),
                   node_label_size_range = node_label_size,
                   node_size = n_obs,
                   node_color = pollinator ,
                   edge_label = NA ,
                   tree_label = "Pollinators",
                   tree_label_color = header_color,
                   make_node_legend = FALSE,
                   node_legend_title = "Test",
                   node_size_axis_label = NULL,
                   make_edge_legend = FALSE,
                   #node_size_digits = -1,
                   node_size_range = node_size_range,
                   edge_size_range = edge_size_range,
                   layout = layout,
                   repel_iter = repel_iter,
                   repel_force = repel_force
)
# Arrange and render the plots
grid.arrange(taxonomyNeeded, redList, cwr, OnHorizon, iasUnionList, birds, habitats, marineDir, pollinators, ncol=3)

# Open a TIFF device with 600 DPI resolution
tiff(
  filename = "policies.tif",  # Change path as needed
  width = 2625,                              # Width in pixels
  height= 2625,                              # Height in pixels
  units = "px",                              # Units set to pixels
  res = 300,                               # Resolution in DPI
  bg = "white",
  compression = "lzw"                      # Optional: compression type
)

# Arrange and render the plots
grid.arrange(taxonomyNeeded, redList, cwr, OnHorizon, iasUnionList, birds, habitats, marineDir, pollinators, ncol=3)

# Close the device to save the file
dev.off()

# Open a PNG device with 600 DPI resolution
png(
  filename = "policies.png", # Change path as needed
  width = 1200,                              # Width in pixels
  height= 1200,                              # Height in pixels
  units = "px",                              # Units set to pixels
  res = 300,                              # Resolution
  bg = "white",
  type = "cairo"                          # Optional: use Cairo graphics
)

# Arrange and render the plots
grid.arrange(taxonomyNeeded, redList, cwr, OnHorizon, iasUnionList, birds, habitats, marineDir, pollinators, ncol=3)

# Close the device to save the file
dev.off()