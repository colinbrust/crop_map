historical_plot <- function(dat, year, state, county, crop) {
  
  library(ggplot2)
  
  out_dat <- dat %>%
    dplyr::filter(state == !!state, 
                  county == !!county,
                  crop == !!crop)
  
  # This method taken from stack exchange" 
  interp <- approx(out_dat$year, out_dat$scpi, n=10000)
  
  out_dat <- data.frame(year=interp$x, scpi=interp$y) %>%
    dplyr::mutate(color = dplyr::if_else(scpi <= 0, "neg", "pos"))
  
  out_dat %>%
    ggplot(aes(x = year, y = scpi)) + 
      geom_area(aes(fill=color)) +
      geom_line() +
      geom_hline(yintercept = 0, size = 0.5, color = "red", 
                 linetype = 'dashed') +
      theme_minimal() + 
      ylab("SCPI") + 
      xlab("Year") +
    theme(legend.position = "none") 
  
}
