library(shiny)
library(magrittr)
library(leaflet)
library(mapview)
library(RColorBrewer)
source("./helpers.R")


if (lubridate::month(Sys.Date()) == 1) {
  years <- c(1990:(lubridate::year(Sys.Date()) - 1))
} else if (lubridate::month(Sys.Date()) == 2 && lubridate::day(Sys.Date()) <=3) {
  years <- c(1990:(lubridate::year(Sys.Date()) - 1))
} else {
  years <- c(1990:lubridate::year(Sys.Date()))
}

ui <- bootstrapPage(
  title = "Standardized Crop Production Index",
  tags$style(type = "text/css", "html, body {width:100%;height:100%}",
             "div.info.legend.leaflet-control br {clear: both;}",
             HTML(".shiny-notification {
                  position:fixed;
                  width: 16em;
                  top: calc(40%);;
                  left: calc(40%);;
                  }
                  "
             )
             ),
  mapview::mapviewOutput("map", width = "100%", height = "100%"),
  absolutePanel(
    # id="controls",
    style="z-index:500;",
    # top = 0, right = 125,
    top = 20, right = 20, width = 150,
    fixed = T,
    style = "opacity: 0.90",
    wellPanel(
      selectInput("year", "Year",
        selected = tail(years, 1),
        choices = years,
        width = '80px'
      ),
      radioButtons(
        "crop", "Crop:",
        c(
          "Alfalfa" = "alf",
          "Wheat" = "whe",
          "Barley" = "bar"
        )
      ),
      # radioButtons(
      #   "stat", "Statistic:",
      #   c(
      #     "Standardized Precipitation Index (SPI)" = "spi",
      #     "Evaporative Drought Demand Index (EDDI)" = "eddi"
      #   )
      # ),
      selectInput(
        "vari", "Variable:",
        c(
          "SCPI" = "scpi",
          "SCVI" = "scvi",
          "SPI" = "stat_value", 
          "Alpha Coefficient" = "alpha", 
          "Beta Coefficient" = "beta", 
          "Gamma Coefficient" = "gamma"
        )
      ),
      actionButton("button", "Change Inputs")
    )
  )
)

outlines <- sf::read_sf("../boundaries/all_merged.geojson") 

states <- suppressWarnings(sf::read_sf("../boundaries/state_outlines.geojson") %>%
  sf::st_simplify(dTolerance = 0.01))

dat <- readr::read_csv("../data_frames/scpi_use.csv", col_types = readr::cols())

server <- function(input,
                   output, session) {

  current_selection <- reactiveVal(NULL)

  observeEvent(input$year, {
    current_selection(input$year)
  })


  observe({

    years_use <- dat %>%
      dplyr::filter(crop == input$crop) %>%
      {unique(.$year)}

    years_use <- years_use[order(years_use)]

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

    list(input$year, input$crop, input$vari)#, input$stat)

  }, ignoreNULL = FALSE)
  
  observe({
    showNotification("Please Wait, Map is Loading 
                     _________________________",
                     duration = 20)
  })
  
  observeEvent(input$button, {
    showNotification("Please Wait, Loading Data 
                     ________________________",
                     duration = 5)
  })
  
  output$map <- renderLeaflet({

      out_dat <- dat %>%
        dplyr::filter(
          year == button_vals()[[1]],
          crop == button_vals()[[2]],
          stat == "spi"#button_vals()[[3]]
        ) %>%
        dplyr::right_join(outlines, by = c("county", "state")) %>%
        sf::st_as_sf() %>%
        sf::st_simplify(dTolerance = 0.01)

      out_plot <- list.files("../plot_data/", pattern = button_vals()[[2]],
                             full.names = T) %>%
        grep(pattern = 'spi', ., value = T) %>%
        #grep(pattern = button_vals()[[3]], ., value = T) %>%
        readRDS()

      labs <- out_dat$lab %>%
        as.list() %>%
        lapply(HTML)
    
      var_use <- button_vals()[[3]]
  
      breaks_col <- out_dat %>%
        dplyr::select(!!var_use) %>%
        as.list() %>%
        {.[[1]]}
    
      col_out <- seq(min(breaks_col, na.rm = T), max(breaks_col, na.rm = T),
                     length.out = 10) %>%
        round(2)

      mapviewOptions(legend.pos = "bottomright")
      
      mapview(out_dat,
              popup = out_plot,
              zcol = c(var_use),
              label = labs,
              na.label = "No Data",
              col.regions = brewer.pal(10, "RdBu"),
              at = col_out,
              layer.name = var_use) %>%
        addFeatures(states, weight = 3, color = "black") %>%
        setView(lng = -107.5, lat = 46, zoom = 5) %>%
        addProviderTiles(providers$CartoDB.Positron) # %>% 
        # addLegend(
        #   position = 'bottomright',
        #   colors = brewer.pal(10, "RdBu"),
        #   labels = col_out,
        #   title = "SCPI (Standard Deviations)"
        # )

  })
}

# Run the application
shinyApp(ui = ui, server = server)