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

#### ADD 1980-08 TO DATA ####

reorder_data <- function(dat, win) {
  
  dat <- detrend_data() %>% dplyr::filter(state == "MT", county_name == "CARBON", variable == "precip")
  
  county <- dat$county_name %>%
    unique() %>%
    tolower() %>%
    str_replace(" ", "-")
  
  state <- unique(dat$state)
  
  dat %>%
    dplyr::ungroup() %>%
    dplyr::select(date, detrended) %>%
    tidyr::separate(col = date, into = c("year", "month"), sep = "-") %>%
    dplyr::mutate(year = as.numeric(year), 
                  month = as.numeric(month)) %>%
    {ts(.$detrended,
        end=c(tail(.$year, 1), tail(.$month, 1)), 
        frequency=12)} %>%
    SPEI::spi(scale = win, distribution = 'log-Logistic')
  
}

# function that detrends data from each county across entire time period
detrend_data <- function() {
  
  suppressWarnings(
    readr::read_csv("./data_frames/master_df.csv", col_types = readr::cols()) %>%
      dplyr::select(-X1) %>%
      dplyr::filter(!is.na(county_name)) %>%
      dplyr::group_by(county_name, variable, state) %>%
      dplyr::arrange(date) %>%
      dplyr::mutate(date = format(date, "%Y-%m")) %>%
      dplyr::mutate(detrended = pracma::detrend(value, tt = 'linear')) 
  )
}

calc_spi <- function() {
  
  dat <- detrend_data()
  
  dates <- unique(dat$date)
  wins <- 0:14
  
  for (d in 1:length(dates)) {
    for (win in wins) {
      
      analysis_dates = dates[d:(d+win)]
      
      dat %>%
        dplyr::filter(variable == "precip") %>%
        dplyr::filter(date %in% analysis_dates) %>%
        dplyr::mutate(SPI = SPEI::spi(detrended, scale = 15))
      
      
    }
  }
  
}


data(wichita)

wichita <- ts(wichita[,-c(1,2)], end=c(2011,10), frequency=12)

spi_1 <- spi(wichita[,'PRCP'], 1)
spi_12 <- spi(wichita[,'PRCP'], 12)
