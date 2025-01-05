library(metacoder)
library(rcartocolor)
library(grid)
library(gridExtra)
library(readr)

# PLANTAE

# Load data
data <- readr::read_tsv("supply_and_demand_order_level.tsv")

# Filter for Plantae and remove rows with missing order
data = data[data$kingdom == "Plantae", ]
data =  data[!(is.na(data$order)), ]

# Ensure numeric columns are properly cast
numeric_cols <- c("nr_authors", "taxonomicResearchNeeded", "cropWildRelatives", "horizonInvasives")
data[numeric_cols] <- lapply(data[numeric_cols], as.numeric)

print(data)

# Create heat tree plots
my_plots <- lapply(c("nr_authors","taxonomicResearchNeeded","cropWildRelatives","horizonInvasives"), function(demand) {
  # do something with time point data
  set.seed(1) # Make each plot layout look the same
  print(demand)
  #obj <- parse_tax_data(data, class_cols = 3:6)
  obj <- parse_tax_data(data,
                        class_cols = "lineage", # the column that contains taxonomic information
                        class_sep = ";", # The character used to separate taxa in the classification
                        class_regex = "^(.+)_(.+)$", # Regex identifying where the data for each taxon is
                        class_key = c(tax_rank = "info", # A key describing each regex capture group
                                      tax_name = "taxon_name"))
  # Calculate taxon abundances for all levels
  obj$data$taxon_counts <- calc_taxon_abund(obj, data = "tax_data", cols=demand)
  
  obj$data$taxon_counts$total <- rowSums(obj$data$taxon_counts[, -1], na.rm = TRUE)
  
  # Assign values to non-leaf nodes by summing their descendants  
  obj$data$taxon_counts$total_leaf <- ifelse(obj$is_leaf(), obj$data$taxon_counts$total, 0)
  
  obj$data$tax_abund <- calc_taxon_abund(obj, "tax_data", cols = 8)

  #obj$data$taxon_counts$total_leaf <- ifelse(obj$is_leaf(), obj$data$taxon_counts$total, 
  #                                           rowSums(obj$node_taxon_abundances("total", subset = obj$sub_taxa())))


  print(obj)
  if(demand=="nr_authors") {
    heat_tree(obj, # label nodes except on the order level
              node_label = ifelse(taxon_names %in% data$order, "", taxon_names),
              node_label_size_range = c(0.02,0.1),
              node_size = n_obs,
              node_color_range=colorRampPalette(c("#c9edde", "#091410"))(10),
              node_size_range = c(0.01, 0.05),
              edge_size_range = c(0.004, 0.004),
              node_color = total_leaf,
              make_node_legend = TRUE,
              node_legend_title = NA,
              node_size_axis_label = NULL,
              make_edge_legend = TRUE,
              node_color_axis_label = "Number of authors",
              node_size_digits = -1,
              layout="davidson-harel",
              initial_layout="reingold-tilford") # The layout algorithm that initializes node locations
  } else {
    heat_tree(obj, 
              node_size = n_obs,
              node_color_range=colorRampPalette(c("#ffd2b2", "#7f3500"))(10),
              node_size_range = c(0.01, 0.05),
              edge_size_range = c(0.005, 0.005),
              node_color = total_leaf, 
              make_node_legend = FALSE,
              make_edge_legend = FALSE,
              layout="davidson-harel",
              initial_layout="reingold-tilford") # The layout algorithm that initializes node locations
  }
})
grid.arrange(my_plots[[1]], 
             arrangeGrob(my_plots[[2]], 
                         right=textGrob("Taxonomic research needed", rot=270,
                                        gp=gpar(cex=1))), 
             arrangeGrob(my_plots[[3]], 
                         right=textGrob("Crop wild relatives", rot=270)),
             arrangeGrob(my_plots[[4]], 
                         right=textGrob("Invasives species on horizon", rot=270)),
             layout_matrix=rbind(c(1,1,1,2),c(1,1,1,3),c(1,1,1,4)))


# ANIMALIA

data <- readr::read_tsv("data/processed/supply_and_demand_order_level.tsv")
data = data[data$kingdom == "Animalia", ]
data =  data[!(is.na(data$order)), ]
# GBIF deleted Actinopterygii; restore Chordata with NA as a class as Actinopterygii 
data[is.na(data$class)&data$phylum=="Chordata","class"] <- "Actinopterygii"

my_plots <- lapply(c("nr_authors","taxonomicResearchNeeded","horizonInvasives"), function(demand) {
  # do something with time point data
  set.seed(1) # Make each plot layout look the same
  obj <- parse_tax_data(data, class_cols = 2:5)
  obj$data$taxon_counts <- calc_taxon_abund(obj, data = "tax_data", cols=demand)
  obj$data$taxon_counts$total <- rowSums(obj$data$taxon_counts[, -1])
  obj$data$taxon_counts$total_leaf <- ifelse(obj$is_leaf(), obj$data$taxon_counts$total, 0)

  if(demand=="nr_authors") {
    heat_tree(obj, 
              node_label = ifelse(taxon_names %in% data$order, "", taxon_names),
              node_label_max = 1000000,
              node_size = n_obs,
              node_color_range=colorRampPalette(c("#c9edde", "#091410"))(10),
              node_size_range = c(0.01, 0.05),
              edge_size_range = c(0.003, 0.003),
              node_color = total_leaf, 
              make_node_legend = FALSE,
              node_label_size_range = c(0.015,0.035),
              node_size_axis_label = NULL,
              node_size_digits = -1,
              layout="davidson-harel",
              initial_layout="reingold-tilford") # The layout algorithm that initializes node locations
  } else { 
    heat_tree(obj, 
              node_size = n_obs,
              node_color_range=colorRampPalette(c("#ffd2b2", "#7f3500"))(10),
              node_size_range = c(0.01, 0.05),
              edge_size_range = c(0.005, 0.005),
              node_color = total_leaf, 
              make_node_legend = FALSE,
              layout="davidson-harel",
              initial_layout="reingold-tilford") # The layout algorithm that initializes node locations
  }
  
})
grid.arrange(my_plots[[1]], 
             arrangeGrob(my_plots[[2]], 
                         right=textGrob("Taxonomic research needed", rot=270)), 
             arrangeGrob(my_plots[[3]], 
                         right=textGrob("Invasive species on horizon", rot=270)),
             layout_matrix=rbind(c(1,1,2),c(1,1,3)))



# FUNGI

data <- readr::read_tsv("data/processed/supply_and_demand_order_level.tsv")
head(data)
data = data[data$kingdom == "Fungi", ]
data =  data[!(is.na(data$order)), ]


my_plots <- lapply(c("nr_authors","taxonomicResearchNeeded"), function(demand) {
  # do something with time point data
  set.seed(1) # Make each plot layout look the same
  obj <- parse_tax_data(data, class_cols = 2:5)
  obj$data$taxon_counts <- calc_taxon_abund(obj, data = "tax_data", cols=demand)
  obj$data$taxon_counts$total <- rowSums(obj$data$taxon_counts[, -1])
  obj$data$taxon_counts$total_leaf <- ifelse(obj$is_leaf(), obj$data$taxon_counts$total, 0)
  
  if(demand=="nr_authors") {
    heat_tree(obj, 
              node_label = ifelse(taxon_names %in% data$order, "", taxon_names),
              node_label_max=1000000,
              node_size = n_obs,
              node_color_range=colorRampPalette(c("#c9edde", "#091410"))(10),
              node_size_range = c(0.01, 0.05),
              edge_size_range = c(0.003, 0.003),
              node_color = total_leaf, 
              make_node_legend = FALSE,
              node_label_size_range = c(0.013,0.03),
              node_size_axis_label = NULL,
              node_size_digits = -1,
              layout="davidson-harel",
              initial_layout="reingold-tilford") # The layout algorithm that initializes node locations
  } else { 
    heat_tree(obj, 
              node_size = n_obs,
              node_color_range=colorRampPalette(c("#ffd2b2", "#7f3500"))(10),
              node_size_range = c(0.01, 0.05),
              edge_size_range = c(0.005, 0.005),
              node_color = total_leaf, 
              make_node_legend = FALSE,
              layout="davidson-harel",
              initial_layout="reingold-tilford") # The layout algorithm that initializes node locations
  }
  
})
grid.arrange(my_plots[[1]], 
             arrangeGrob(my_plots[[2]], 
                         right=textGrob("Taxonomic research needed", rot=270)),
             layout_matrix=rbind(c(1,1,2),c(1,1,2)))

