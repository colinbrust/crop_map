library(magrittr) 

all_counties <- list.files("./Files_for_Colin/county_list", full.names = T) %>%
  lapply(readr::read_csv, col_names = F) %>%
  dplyr::bind_rows() 

all_counties$X1 %>%
  length()

all_counties$X1 %>%
  unique() %>% 
  length()
