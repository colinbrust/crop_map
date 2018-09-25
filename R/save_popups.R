library(mapview)
library(magrittr)
library(sf)
library(readr)
library(dplyr)
source("../scpi_map/helpers.R")

save_plot_obj <- function(crop, dat, outlines, nass) {
  
  out_name <- paste0("../plot_data/", crop, "_plots.RData")
  
  pop_plots <- outlines %>%
    dplyr::rowwise() %>%
    dplyr::mutate(plots = list(historical_plot(state = state, county = county,
                                         crop = crop, dat = dat, nass = nass))) %>%
                                         {.$plots} %>%
    mapview::popupGraph(width = 600, height = 300) 
  
    saveRDS(pop_plots, file = out_name)
    
}

outlines <- sf::read_sf("../boundaries/all_merged.geojson") %>% 
  dplyr::rename(state = state_name)

dat <- readr::read_csv("../data_frames/master_scpi.csv",
                       col_types = readr::cols()) %>%
  dplyr::select(-X1, -scvi, -orig_year, 
                -stat, -variable, -spi)

nass <- readr::read_csv("../data_frames/prod_detrended.csv",
                        col_types = readr::cols())

c("alf", "whe", "bar") %>%
  lapply(save_plot_obj,
         dat = dat, 
         outlines = outlines, 
         nass = nass)
