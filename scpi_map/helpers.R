county_change <- function(name) {
  
  name %>%
    stringr::str_replace_all("_", " ") %>%
    tools::toTitleCase()
}

historical_plot <- function(state, county, crop, dat, nass) {
  
  library(ggplot2)
  
  cName <- county_change(county)
  
  crName <- switch(crop, 
                   "alf" = "Alfalfa", 
                   "bar" = "Barley", 
                   "whe" = "Wheat")

    
  out_dat <- dat %>%
    dplyr::filter(state == !!state, 
                  county == !!county,
                  crop == !!crop) %>%
    dplyr::left_join(nass, by = c("crop", "state", "year")) %>%
    dplyr::mutate(color = dplyr::if_else(scpi <= 0, "neg", "pos")) %>%
    dplyr::filter(!is.na(scpi), !is.na(prod)) %>% 
    tidyr::gather(key = "metric", value = "value", 
                  prod, scpi) %>%
    dplyr::mutate(metric = factor(metric))
  
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
      ggplot(aes(x = year, y = value, color = metric)) + 
      geom_line(size = 1) +
      geom_hline(yintercept = 0, linetype = "dashed") +
      theme_minimal() + 
      labs(x = "Year", y = "Production (Standard Deviations)", 
           title = paste("Modeled (SCPI) vs Actual", crName, "Production for", cName, "County")) +
      scale_color_discrete(name="",
                          breaks=c("prod", "scpi"),
                          labels=c("Actual\nProduction\nAnomaly\n", 
                                   "Modeled\nProduction\nAnomaly\n")) +
      theme(plot.title = element_text(hjust = 0.5),
            text = element_text(family="Times", face="bold", size=12),
            plot.subtitle = element_text(hjust = 0.5, family = "Times", size = 10)) %>%
      return()
    
    # # This method taken from stack exchange" 
    # interp <- approx(out_dat$year, out_dat$scpi, n=5000)
    # 
    # out_dat <- data.frame(year=interp$x, scpi=interp$y) %>%
    #   dplyr::mutate(color = dplyr::if_else(scpi <= 0, "neg", "pos"))

    # out_dat %>%
    #   ggplot() + 
    #   geom_bar(aes(x = year, y = scpi, fill = color), stat = "identity") +
    #   geom_line(aes(x = year, y = prod)) +
    #   theme_minimal() + 
    #   labs(x = "Year", y = "SCPI", 
    #        title = paste("SCPI for", cName, "County", crName, "Production")) +
    #   theme(legend.position = "none") +
    #   theme(plot.title = element_text(hjust = 0.5),
    #         text = element_text(family="Times", face="bold", size=12)) %>%
    #   return()
    
    # out_dat %>%
    #   ggplot(aes(x = year, y = scpi)) + 
    #     geom_area(aes(fill=color)) +
    #     geom_line() +
    #     geom_hline(yintercept = 0, size = 0.75, color = "gray30", 
    #                linetype = 'dashed') +
    #     theme_minimal() + 
    #   labs(x = "Year", y = "SCPI", 
    #        title = paste("SCPI for", cName, "County", crName, "Production")) +
    #   theme(legend.position = "none") +
    #   theme(plot.title = element_text(hjust = 0.5),
    #         text = element_text(family="Times", face="bold", size=12)) %>%
    #   return()
  }
  
}
