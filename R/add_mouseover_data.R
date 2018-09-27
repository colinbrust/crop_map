library(magrittr)

county_change <- function(name) {
  
  name %>%
    stringr::str_replace_all("_", " ") %>%
    tools::toTitleCase()
}

readr::read_csv("../data_frames/master_scpi.csv",
                col_types = readr::cols()) %>%
  dplyr::select(-X1, -scvi, -orig_year, 
                -stat, -variable, -spi) %>%
  dplyr::mutate(lab=paste0('<strong>County</strong>: ', 
                           county_change(county),
                           '<br><strong>State</strong>: ',
                           state,
                           '<br><strong>SCPI</strong>: ',
                           scpi,
                           '<br><strong>RMSE</strong>: ',
                           rmse,
                           '<br><strong>Optimal Window</strong>: ', 
                           window,
                           '<br><strong>Optimal Month</strong>: ',
                           month.name[month],
                           '<br><strong>Alpha Coefficient</strong>: ',
                           alpha,
                           '<br><strong>Beta Coefficient</strong>: ', 
                           beta,
                           '<br><strong>Gamma Coeffieient</strong>: ',
                           gamma)) %>%
  readr::write_csv("../data_frames/scpi_use.csv")