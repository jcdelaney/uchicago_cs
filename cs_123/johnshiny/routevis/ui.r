library(shiny)
library(maps)
library(geosphere)

flights <- read.csv("http://datasets.flowingdata.com/tuts/maparcs/flights.csv", header=TRUE, as.is=TRUE)

shinyUI(pageWithSidebar(

    headerPanel("Miles Per Gallon"),
    
    sidebarPanel(
        selectInput("airline", "Variable:",
                    choices = unique(flights$airline)
                    )
    ),
    
    mainPanel(
        imageOutput("dataImage")
)
))