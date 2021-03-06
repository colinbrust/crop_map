library(magrittr)

make_tidy_lags <- function() {
  
  "./data_frames/coeffs" %>%
    list.files(full.names = T) %>%
    lapply(add_state_name) %>% 
    dplyr::bind_rows() %>%
    tidyr::gather(coeffs, value, -county, -state, -crop, -stat) %>%
    tidyr::separate(coeffs, into = c("coeff", "month", "lag")) %>%
    dplyr::mutate(month = stringr::str_replace(month, "month", "") %>% as.numeric(),
                  lag = stringr::str_replace(lag, "lag", "") %>% as.numeric()) %>%
    tidyr::spread(coeff, value)
  
}

get_best_lag <- function() {
  
  make_tidy_lags() %>%
    dplyr::group_by(county, state, crop, stat, month) %>%
    dplyr::slice(which.min(rmse)) %>%
    dplyr::ungroup()
  
}

get_best_month_lag <- function() {
  
  make_tidy_lags() %>%
    dplyr::group_by(county, state, crop, stat) %>%
    dplyr::slice(which.min(rmse)) %>%
    dplyr::ungroup()
  
}

add_state_name <- function(fname) {
  
  state_name <- fname %>%
    stringr::str_split("/", simplify = F) %>% 
    unlist() %>% 
    tail(1) %>%
    stringr::str_split("_", simplify = T) %>%
    unlist() %>%
    magrittr::extract(2)
  
  crop_name <- fname %>%
    stringr::str_split("/", simplify = F) %>% 
    unlist() %>% 
    tail(1) %>%
    stringr::str_split("_", simplify = T) %>%
    unlist() %>%
    magrittr::extract(1)
  
  stat_name <- fname %>%
    stringr::str_split("/", simplify = F) %>% 
    unlist() %>% 
    tail(1) %>%
    stringr::str_split("_", simplify = T) %>%
    unlist() %>%
    magrittr::extract(3)
  
  suppressWarnings(fname %>% 
    readr::read_csv(col_types = readr::cols()) %>%
    tibble::add_column(state = state_name,
                       crop = crop_name, 
                       stat = stat_name) %>%
    dplyr::rename(county = X1))
}

get_best_lag() %>% readr::write_csv("./data_frames/tidy_coeffs.csv")
get_best_month_lag() %>% readr::write_csv("./data_frames/best_month_coeffs.csv")
