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
    tibble::add_column(year = dat$year, 
                       county = dat$county) %>%
    dplyr::rename(prod = `Series 1`)
}

detrend_data <- function(fname) {
  
  suppressWarnings(fname %>% 
                     readr::read_csv(col_types = readr::cols()) %>% 
                     dplyr::select(-X1) %>%
                     dplyr::mutate(county = county %>%
                                     tolower() %>%
                                     stringr::str_replace_all(" ", "_") %>%
                                     stringr::str_replace_all("&", "and")) %>%
                     dplyr::group_by(crop, state, county) %>%
                     dplyr::arrange(county, state, crop, year) %>%
                     dplyr::filter(year >= 1979, 
                                   county != "other_(combined)_counties",
                                   county != 'other_counties',
                                   !all(county == "sublette" & crop == "BARLEY"),
                                   !all(county == "sweetwater" & crop == "WHEAT"),
                                   !all(county == "uinta" & crop == "WHEAT")) %>%
                     dplyr::mutate(detrended = pracma::detrend(value, tt = "linear")) %>%
                     dplyr::filter(!is.na(detrended))
  )
  
}


"../data_frames/nass_production.csv" %>% 
  detrend_data() %>%
  dplyr::do(spi_calc(.)) %>%
  dplyr::ungroup() %>%
  dplyr::mutate(crop = dplyr::if_else(crop == "BARLEY", "bar", crop),
                crop = dplyr::if_else(crop == "WHEAT", "whe", crop),
                crop = dplyr::if_else(crop == "HAY", "alf", crop)) %>%
  readr::write_csv("../data_frames/prod_detrended.csv")

