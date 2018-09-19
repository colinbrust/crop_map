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
library(mapview)
source("./helpers.R")

# Define UI for application that draws a histogram
ui <- fluidPage(
  titlePanel("Shiny tmap!"),
  sidebarLayout(
    sidebarPanel(
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
    ),
    mainPanel(
      leafletOutput("map")
    )
  )
)


outlines <- sf::read_sf("../boundaries/all_merged.geojson") 

dat <- outlines %>%
  dplyr::rename(state = state_name) %>%
  dplyr::full_join(readr::read_csv("../data_frames/master_scpi.csv",
    col_types = readr::cols()
  ),
  by = c("state", "county")
  ) %>%
  dplyr::filter(year == 2017, crop == "alf")


# Define server logic required to draw a histogram
server <- function(input,
                   output, session) {

  # Reactive expression for the data subsetted to what the user selected
  filteredData <- reactive({
    dat %>%
      dplyr::filter(
        year == input$year,
        crop == input$crop
      )
  })
  
  print(filteredData)
  
  output$map = renderLeaflet({
    
    out_map <-  tm_basemap(leaflet::providers$Stamen.TerrainBackground) +
      tm_shape(outlines) +
        tm_borders(alpha = 0.5) +
        tm_fill("gray") +
      tm_shape(filteredData) +
        tm_polygons("scpi", group = "county", midpoint = 0)
   
    tmap_leaflet(out_map)
    
  })
}

# Run the application
shinyApp(ui = ui, server = server)



