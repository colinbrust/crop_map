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
  wins <- 1:15
  
  for (win in wins) {
    for (d in 1:length(dates)) {
      
      print()
    }
  }
  
}

