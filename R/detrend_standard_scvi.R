library(magrittr)

spi_calc <- function(dat) {
  
  dat %>%
    dplyr::select(year, detrended) %>%
    {
      ts(.$detrended, end = tail(.$year, 1), frequency = 1)
    } %>%
    SPEI::spi(scale = 1, distribution = "log-Logistic") %>%
    {
      .$fitted
    } %>%
    tibble::as_tibble() %>%
    tibble::add_column(year = dat$year) %>%
    dplyr::rename(scvi = `Series 1`)
}

detrend_data <- function(fname) {
  
  suppressWarnings(fname %>% 
    readr::read_csv(col_types = readr::cols()) %>% 
    dplyr::select(-X1) %>%
    dplyr::group_by(crop, state) %>%
    dplyr::arrange(state, crop, year) %>%
    dplyr::mutate(detrended = pracma::detrend(value, tt = "linear")) 
  )
    
}

"../data_frames/nass_data.csv" %>%
  detrend_data() %>% 
  dplyr::do(spi_calc(.)) %>%
  dplyr::ungroup() %>%
  dplyr::rename(orig_year = year) %>%
  dplyr::mutate(crop = dplyr::if_else(crop == "BARLEY", "bar", crop),
                crop = dplyr::if_else(crop == "WHEAT", "whe", crop),
                crop = dplyr::if_else(crop == "HAY", "alf", crop),
                year = orig_year + 1) %>%
  readr::write_csv("../data_frames/scvi_detrended.csv")

