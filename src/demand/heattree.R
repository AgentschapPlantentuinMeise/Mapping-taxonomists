setwd("C:/Users/melanie/Documents/GitHub/TETTRIs-mapping-taxonomists")

library(metacoder)
library(rcartocolor)
library(grid)
library(gridExtra)


data <- readr::read_tsv("data/processed/supply_and_demand_order_level.tsv")
data = data[data$kingdom == "Plantae", ]
data_nona =  data[!(is.na(data$order)), ]


my_plots <- lapply(c("nr_authors","taxonomicResearchNeeded","cropWildRelatives","horizonInvasives"), function(demand) {
  # do something with time point data
  set.seed(1) # Make each plot layout look the same
  print(demand)
  obj <- parse_tax_data(data_nona, class_cols = 2:5)
  obj$data$taxon_counts <- calc_taxon_abund(obj, data = "tax_data", cols=demand)
  obj$data$taxon_counts$total <- rowSums(obj$data$taxon_counts[, -1])
  obj$data$taxon_counts$total_leaf <- ifelse(obj$is_leaf(), obj$data$taxon_counts$total, 0)
  
  if(demand=="nr_authors") {
    heat_tree(obj, 
              node_label = taxon_names,
              node_size = n_obs,
              node_color_range=colorRampPalette(c("#c9edde", "#21614A"))(10),
              node_size_range = c(0.01, 0.05),
              edge_size_range = c(0.004, 0.004),
              node_color = total_leaf, 
              make_node_legend = FALSE,
              node_legend_title = NA,
              node_label_size_range = c(0.010,0.03),
              node_size_axis_label = NULL,
              make_edge_legend = FALSE,
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



data <- readr::read_tsv("data/processed/supply_and_demand_order_level.tsv")
head(data)
data = data[data$kingdom == "Animalia", ]
data_nozeros =  data[!(is.na(data$order)), ]


my_plots <- lapply(c("nr_authors","taxonomicResearchNeeded","horizonInvasives"), function(demand) {
  # do something with time point data
  set.seed(1) # Make each plot layout look the same
  obj <- parse_tax_data(data_nozeros, class_cols = 2:5)
  obj$data$taxon_counts <- calc_taxon_abund(obj, data = "tax_data", cols=demand)
  obj$data$taxon_counts$total <- rowSums(obj$data$taxon_counts[, -1])
  obj$data$taxon_counts$total_leaf <- ifelse(obj$is_leaf(), obj$data$taxon_counts$total, 0)
  
  skipnames <- c()
  
  for (row in 1:nrow(obj$data$taxon_counts)) {
    if (obj$data$taxon_counts[[row,"total"]] < 10) {
      skipnames <- append(skipnames, obj$data$taxon_counts[[row,"taxon_id"]])
    }
  }
  
  for (name in skipnames) {
    obj$taxa[[name]]$name$name <- NULL
  }

  if(demand=="nr_authors") {
    heat_tree(obj, 
              node_label = taxon_names,#ifelse(total>5,taxon_names,NA),
              node_label_max=1000000,
              node_size = n_obs,
              node_color_range=colorRampPalette(c("#c9edde", "#21614A"))(10),
              node_size_range = c(0.01, 0.05),
              edge_size_range = c(0.003, 0.003),
              node_color = total_leaf, 
              make_node_legend = FALSE,
              node_label_size_range = c(0.01,0.03),
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

