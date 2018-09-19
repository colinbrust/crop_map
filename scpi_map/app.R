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
library(tmap)
library(shinydashboard)
library(RColorBrewer)
source("./helpers.R")

# Define UI for application that draws a histogram
# ui <- fluidPage(
#   titlePanel("Standardized Crop Production Index Map"),
#   sidebarLayout(
#     sidebarPanel(
#       selectInput("year", "Year (1979 - Present)",
#         selected = lubridate::year(Sys.Date()),
#         choices = c(1979:lubridate::year(Sys.Date()))
#       ),
#       radioButtons(
#         "crop", "Crop:",
#         c(
#           "Alfalfa" = "alf",
#           "Wheat" = "whe",
#           "Barley" = "bar"
#         )
#       )
#     ),
#     mainPanel(
#       leafletOutput("map")
#     )
#   )
# )

ui <- bootstrapPage(
  title = "Standardized Crop Production Index",
  tags$style(type = "text/css", "html, body {width:100%;height:100%}"),
  leafletOutput("map", width = "100%", height = "100%"),
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


outlines <- sf::read_sf("../boundaries/all_merged.geojson")

suppressWarnings(
  dat <- outlines %>%
    dplyr::rename(state = state_name) %>%
    dplyr::full_join(readr::read_csv("../data_frames/master_scpi.csv",
      col_types = readr::cols()
    ),
    by = c("state", "county")
    ) %>%
    dplyr::select(-X1)
)


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
  
  out_plot <- observeEvent(input$map_shape_click, { # update the location selectInput on map clicks
    
    p <- input$map_shape_click 
    
    print(p)
    # p$id %>%
    #   stringr::str_split("/") %>%
    #   unlist() %>%
    #   {historical_plot(dat, .[[1]], .[[2]], input$crop)}
    
  })

  output$map <- renderLeaflet({
    
    Ndat <- filteredData()
    
      
    out_map <- tm_basemap(leaflet::providers$Stamen.TerrainBackground) +
      tm_shape(outlines) +
      tm_borders(alpha = 0.5) +
      tm_fill("gray") +
      tm_shape(Ndat) +
      tm_polygons("scpi", group = paste(Ndat$state, Ndat$county, sep = "/"),
                                        midpoint = 0) +
      tm_legend(legend.position = c("right", "bottom"),
                main.title = "SCPI",
                main.title.position = "center")

    tmap_leaflet(out_map)
  })
}

# Run the application
shinyApp(ui = ui, server = server)
