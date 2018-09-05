# install all necessary packages

get_packages <- function(x) {

  if(!require(x, character.only = T)){
    install.packages(x)
    library(x, character.only = T)
  } else {
    library(x, character.only = T)
  }
}

packages <- c("SPEI", "tidyverse", "pracma", "lubridate")
for (pak in packages) get_packages(pak)

reorder_data <- function(dat, win) {

  #dat <- detrend_data() %>% dplyr::filter(state == "MT", county_name == "CARBON", variable == "precip")

  ### Ask about gamma and Inf values ###
  dat %>%
    dplyr::ungroup() %>%
    dplyr::select(date, detrended) %>%
    tidyr::separate(col = date, into = c("year", "month"), sep = "-") %>%
    dplyr::mutate(year = as.numeric(year),
                  month = as.numeric(month)) %>%
    {ts(.$detrended,
        end=c(tail(.$year, 1), tail(.$month, 1)),
        frequency=12)} %>%
    SPEI::spi(scale = win, distribution = 'log-Logistic') %>%
    {.$fitted} %>%
    {data.frame(spi = as.vector(.), date = dat$date)} %>%
    tibble::as_tibble() %>%
    tibble::add_column(window = win)



}

# function that detrends data from each county across entire time period
detrend_data <- function() {

  suppressWarnings(
    readr::read_csv("../data_frames/master_df.csv", col_types = readr::cols()) %>%
      dplyr::select(-X1) %>%
      dplyr::filter(!is.na(county_name)) %>%
      dplyr::group_by(county_name, variable, state) %>%
      dplyr::arrange(date) %>%
      dplyr::mutate(detrended = pracma::detrend(value, tt = 'linear'))
  )
}

calc_spi <- function(win) {

  dat <- detrend_data() %>%
    dplyr::filter(variable == "precip") %>%
    dplyr::do(reorder_data(., win))

}

lapply(1:15, calc_spi) %>%
  dplyr::bind_rows() %>%
  readr::write_csv("../data_frames/spi_out.csv")

