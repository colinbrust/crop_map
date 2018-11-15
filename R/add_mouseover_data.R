library(magrittr)

county_change <- function(name) {
  
  name %>%
    stringr::str_replace_all("_", " ") %>%
    tools::toTitleCase()
}
  
add_hover_data <- function(stat) {
  
  list.files("../data_frames", pattern = "master", full.names = T) %>%
    grep(stat, ., value = T) %>%
    readr::read_csv(col_types = readr::cols()) %>%
    dplyr::select(-X1, -orig_year, -stat) %>%
    dplyr::rename(stat_value = !!stat) %>%
    dplyr::mutate(stat = !!stat) %>%
    dplyr::mutate(lab=paste0('<strong>County</strong>: ', 
                             county_change(county),
                             '<br><strong>State</strong>: ',
                             state,
                             '<br><strong>SCPI</strong>: ',
                             round(scpi, 4),
                             '<br><strong>SCVI</strong>: ',
                             round(scvi, 4),
                             '<br><strong>',toupper(stat),'</strong>: ',
                             round(stat_value, 4),
                             '<br><strong>RMSE</strong>: ',
                             round(rmse, 4),
                             '<br><strong>Optimal Window</strong>: ', 
                             window,
                             '<br><strong>Optimal Month</strong>: ',
                             month.name[month],
                             '<br><strong>Alpha Coefficient</strong>: ',
                             round(alpha, 4),
                             '<br><strong>Beta Coefficient</strong>: ', 
                             round(beta, 4),
                             '<br><strong>Gamma Coeffieient</strong>: ',
                             round(gamma, 4)))
    
}
  

c("eddi", "spi") %>%
  lapply(add_hover_data) %>%
  dplyr::bind_rows() %>%
  dplyr::filter(!is.na(year)) %>% 
  readr::write_csv("../data_frames/scpi_use.csv")
