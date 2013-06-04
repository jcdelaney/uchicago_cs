library(shiny)
library(maps)
library(geosphere)

flights <- read.csv("C:\\Users\\John\\Dropbox\\CS\\BitBend\\bitbend_data_test\\johnshiny\\stdev_data.csv", header=TRUE, as.is=TRUE)

shinyUI(pageWithSidebar(

    headerPanel("Price Standard Deviation"),
    
    sidebarPanel(
        selectInput("airline", "Airline:",
                    choices = unique(flights$airline)
                    ),
        tableOutput("table")
    ),
    
    mainPanel(
        imageOutput("dataImage")
        # tableOutput("table")
        # tabsetPanel(
            # tabPanel("Map",imageOutput("dataImage")),
            # tabPanel("Table",tableOutput("table"))
        # )
    )
))