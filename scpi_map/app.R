#
# This is a Shiny web application. You can run the application by clicking
# the 'Run App' button above.
#
# Find out more about building applications with Shiny here:
#
#    http://shiny.rstudio.com/
#

# library(crosstalk)
library(shiny)
library(magrittr)
library(leaflet)
library(mapview)
library(tmap)
library(shinydashboard)
library(RColorBrewer)
source("./helpers.R")

ui <- bootstrapPage(
  title = "Standardized Crop Production Index",
  tags$style(type = "text/css", "html, body {width:100%;height:100%}",
             "div.info.legend.leaflet-control br {clear: both;}"),
  mapview::mapviewOutput("map", width = "100%", height = "100%"),
  absolutePanel(
    # id="controls",
    # style="z-index:500;",
    # top = 0, right = 125,
    top = 20, right = 20, width = 300,
    fixed = T,
    style = "opacity: 0.90",
    wellPanel(
      selectInput("year", "Year",
        selected = lubridate::year(Sys.Date()),
        choices = c(1990:lubridate::year(Sys.Date()))
      ),
      radioButtons(
        "crop", "Crop:",
        c(
          "Alfalfa" = "alf",
          "Wheat" = "whe",
          "Barley" = "bar"
        )
      ),
      actionButton("button", "Change Inputs")
    )
  )
)

outlines <- sf::read_sf("../boundaries/all_merged.geojson") %>% 
  dplyr::rename(state = state_name)

states <- sf::read_sf("../boundaries/state_outlines.geojson") %>%
  sf::st_cast("LINESTRING")

dat <- readr::read_csv("../data_frames/master_scpi.csv",
    col_types = readr::cols()
  ) %>%
  dplyr::select(-X1, -scvi, -orig_year, 
                -stat, -variable, -spi) %>%
  dplyr::mutate(lab=paste0('<strong>County</strong>: ', 
                  county_change(county),
                  '<br><strong>State</strong>: ',
                  state,
                  '<br><strong>SCPI</strong>: ',
                  scpi,
                  '<br><strong>RMSE</strong>: ',
                  rmse,
                  '<br><strong>Optimal Window</strong>: ', 
                  window,
                  '<br><strong>Optimal Month</strong>: ',
                  month,
                  '<br><strong>Alpha Coefficient</strong>: ',
                  alpha,
                  '<br><strong>Beta Coefficient</strong>: ', 
                  beta,
                  '<br><strong>Gamma Coeffieient</strong>: ',
                  gamma))

# Define server logic required to draw a histogram
server <- function(input,
                   output, session) {

  current_selection <- reactiveVal(NULL)
  
  # now store your current selection in the reactive value
  observeEvent(input$year, {
    current_selection(input$year)
  })
  
  
  observe({
    
    years_use <- dat %>%
      dplyr::filter(crop == input$crop) %>%
      {unique(.$year)}
    
    if (current_selection() %in% years_use) {
      updateSelectInput(session, "year",
                        selected = current_selection(),
                        choices = years_use)
    } else {
      updateSelectInput(session, "year",
                        selected =  lubridate::year(Sys.Date()),
                        choices = years_use)
    }
    
  })
  
  button_vals <- eventReactive(input$button, {
    list(input$year, input$crop)
  }, ignoreNULL = FALSE)
  

  output$map <- renderLeaflet({
    
    out_dat <- dat %>%
      dplyr::filter(
        year == button_vals()[[1]],
        crop == button_vals()[[2]]
      ) %>%
      dplyr::right_join(outlines, by = c("county", "state")) %>%
      sf::st_as_sf()
    
    out_plot <- list.files("../plot_data/", pattern = button_vals()[[2]], 
                           full.names = T) %>%
      readRDS()
    
    labs <- out_dat$lab %>%
      as.list() %>%
      lapply(HTML)
   
    mapviewOptions(legend.pos = "bottomright")         
    out_map = mapview(out_dat, 
                   popup = out_plot,
                   zcol = c("scpi"),
                   label = labs, 
                   na.label = "No Data",
                   col.regions = brewer.pal(9,"RdBu"),
                   layer.name = "SCPI (Standard Deviations)") %>%
      addFeatures(states, weight = 3, color = "black")
      
    
    out_map
    
  })
}

# Run the application
shinyApp(ui = ui, server = server)

#run cronjob

