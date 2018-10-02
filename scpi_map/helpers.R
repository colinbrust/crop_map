county_change <- function(name) {
  
  name %>%
    stringr::str_replace_all("_", " ") %>%
    tools::toTitleCase()
}

historical_plot <- function(state, county, stat, crop, dat, nass) {

  library(ggplot2)
  
  cName <- county_change(county)
  
  crName <- switch(crop, 
                   "alf" = "Alfalfa", 
                   "bar" = "Barley", 
                   "whe" = "Wheat")

  out_dat <- dat %>%
    dplyr::filter(state == !!state, 
                  county == !!county,
                  crop == !!crop) 
  
  if (nrow(out_dat) == 0) {
    
    ggplot(dat, aes(x = year, y = scpi)) + 
      geom_blank() + 
      theme_minimal() + 
      labs(x = "Year", y = "SCPI", 
           title = paste("No Data for", cName, "County")) +
      theme(plot.title = element_text(hjust = 0.5),
            text = element_text(family="Times", face="bold", size=12))
    
  } else {
    
    out_dat %>%
      dplyr::left_join(nass, by = c("crop", "state", "year")) %>%
      dplyr::select(-stat_value, -window, -month, -lab,
                    -alpha, -beta, -gamma, -rmse) %>%
      #dplyr::mutate(color = dplyr::if_else(scpi <= 0, "neg", "pos")) %>%
      dplyr::filter(!is.na(scpi), !is.na(prod)) %>% 
      tidyr::spread(stat, scpi) %>%
      tidyr::gather(key = "metric", value = "value", 
                    prod, eddi, spi, na.rm = T) %>%
      dplyr::filter(metric == !!stat | metric == "prod") %>% 
      dplyr::mutate(metric = factor(metric)) %>%
      ggplot(aes(x = year, y = value, color = metric)) + 
      geom_line(size = 1) +
      geom_hline(yintercept = 0, linetype = "dashed") +
      theme_minimal() + 
      labs(x = "Year", y = "Production (Standard Deviations)", 
           title = paste("Modeled", toupper(stat), "(SCPI) vs Actual", crName, "Production Anomalies for\n",
                         cName, "County")) +
      scale_color_discrete(name="",
                          breaks=c("prod", "spi", "eddi"),
                          labels=c("Actual\nProduction\nAnomaly\n", 
                                   "Modeled\nProduction\nAnomaly\n(SPI)\n",
                                   "Modeled\nProduction\nAnomaly\n(EDDI)\n"), 
                          colors = ) +
      theme(plot.title = element_text(hjust = 0.5),
            text = element_text(family="Times", face="bold", size=12),
            plot.subtitle = element_text(hjust = 0.5, family = "Times", size = 10)) %>%
      return()
    

  }
  
}
