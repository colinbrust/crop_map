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
  tags$style(type = "text/css", "html, body {width:100%;height:100%}"),
  mapview::mapviewOutput("map", width = "100%", height = "100%"),
  absolutePanel(
    id="controls",
    style="z-index:500;",
    top = 0, right = 125,
      selectInput("year", "Year (1979 - Present)",
        selected = lubridate::year(Sys.Date()),
        choices = c(1979:lubridate::year(Sys.Date()))
      ),
      radioButtons(
        "crop", "Crop:",
        c(
          "Alfalfa" = "alf",
          "Wheat" = "whe",
          "Barley" = "bar"
        )
      )
    
  )
)

outlines <- sf::read_sf("../boundaries/all_merged.geojson") %>% 
  dplyr::rename(state = state_name)

dat <- readr::read_csv("../data_frames/master_scpi.csv",
    col_types = readr::cols()
  ) %>%
  dplyr::select(-X1, -window, -month, -scvi, -orig_year, 
                -stat, -alpha, -beta, -gamma, -variable, -spi)



# Define server logic required to draw a histogram
server <- function(input,
                   output, session) {

  # Reactive expression for the data subsetted to what the user selected
  filteredData <- reactive({
    dat %>%
      dplyr::filter(
        year == input$year,
        crop == input$crop
      ) %>%
      dplyr::right_join(outlines, by = c("county", "state")) %>%
      sf::st_as_sf()
    
  })
  
  out_plot <- observeEvent(input$map_shape_click, { # update the location selectInput on map clicks
    
    p <- input$map_shape_click 
    
    print(p)

    # p$id %>%
    #   stringr::str_split("/") %>%
    #   unlist() %>%
    #   {historical_plot(dat, .[[1]], .[[2]], input$crop)}
    
  })

  output$map <- renderLeaflet({
    
    out_dat <- filteredData()
    
    test = mapview(out_dat)
    
    test@map
    
  })
}

# Run the application
shinyApp(ui = ui, server = server)
