library(magrittr)

thin_df <- function(df) {
  
  df %>%
    readr::read_csv() %>%
    dplyr::filter(stat != 'eddi') %>%
    dplyr::filter(!is.na(scvi)) %>%
    readr::write_csv('../data_frames/scpi_use2.csv')
    
}


thin_df('../data_frames/scpi_use.csv')
