#
# This is a Shiny web application. You can run the application by clicking
# the 'Run App' button above.
#
# Find out more about building applications with Shiny here:
#
#    http://shiny.rstudio.com/
#

library(shiny)
library(magrittr)
library(leaflet)

# Define UI for application that draws a histogram
ui <- bootstrapPage(
  tags$style(type = "text/css", "html, body {width:100%;height:100%}"),
  leafletOutput("map", width = "100%", height = "100%"),
  absolutePanel(top = 10, right = 10,
                
                selectInput("year", "Year (1979 - Present)", 
                             choices = c(1979:lubridate::year(Sys.Date()))),
                radioButtons("crop", "Crop:", 
                             c("Alfalfa" = "alf",
                               "Wheat" = "whe", 
                               "Barley" = "bar"))
  )
)

dat <- sf::read_sf("../boundaries/all_merged.geojson") %>%
  dplyr::rename(state = state_name) %>%
  dplyr::full_join(readr::read_csv("../data_frames/master_scpi.csv", 
                                   col_types = readr::cols()),
                   by = c("state", "county"))


# Define server logic required to draw a histogram
server <- function(input, output, session) {
  
  # Reactive expression for the data subsetted to what the user selected
  filteredData <- reactive({
    dat %>% 
      dplyr::filter(year == input$year, 
                    crop == input$crop)
  })
  
  output$map <- renderLeaflet({
    
    bbox = sf::st_bbox(dat)
    # Use leaflet() here, and only include aspects of the map that
    # won't need to change dynamically (at least, not unless the
    # entire map is being torn down and recreated).
    leaflet(dat) %>% addTiles() %>%
      fitBounds(~bbox$xmin, ~bbox$ymin, ~bbox$xmax), ~bbox$ymax)
  })
  
  # Incremental changes to the map (in this case, replacing the
  # circles when a new color is chosen) should be performed in
  # an observer. Each independent set of things that can change
  # should be managed in its own observer.
  observe({
    pal <- colorpal()
    
    leafletProxy("map", data = filteredData()) %>%
      clearShapes() %>%
      addCircles(radius = ~10^mag/10, weight = 1, color = "#777777",
                 fillColor = ~pal(mag), fillOpacity = 0.7, popup = ~paste(mag)
      )
  })
  
  # Use a separate observer to recreate the legend as needed.
  observe({
    proxy <- leafletProxy("map", data = quakes)
    
    # Remove any existing legend, and only if the legend is
    # enabled, create a new one.
    proxy %>% clearControls()
    if (input$legend) {
      pal <- colorpal()
      proxy %>% addLegend(position = "bottomright",
                          pal = pal, values = ~mag
      )
    }
  })
}

# Run the application 
shinyApp(ui = ui, server = server)

