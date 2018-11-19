library(mapview)
library(magrittr)
library(sf)
library(readr)
library(dplyr)
source("../scpi_map/helpers.R")

save_plot_obj <- function(crop, stat, dat, outlines, nass) {
  
  out_name <- paste0("../plot_data/", crop, "_", stat, "_plots.RData")
  
  pop_plots <- outlines %>%
    dplyr::rowwise() %>%
    dplyr::mutate(plots = list(historical_plot(state = state, county = county, stat = stat,
                                         crop = crop, dat = dat, nass = nass))) %>%
                                         {.$plots} %>%
    mapview::popupGraph(type = 'svg', width = 500, height = 250) 
  
    saveRDS(pop_plots, file = out_name)
    
}

outlines <- sf::read_sf("../boundaries/all_merged.geojson") 

dat <- readr::read_csv("../data_frames/scpi_use.csv",
                       col_types = readr::cols()) 

nass <- readr::read_csv("../data_frames/prod_detrended.csv",
                        col_types = readr::cols())

crops <- c("alf", "whe", "bar")
stats <- c("spi", "eddi")

for (crop in crops) {
  for (stat in stats) {
    save_plot_obj(crop, stat, dat, outlines, nass)
  }
}

