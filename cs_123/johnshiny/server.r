library(maps)
library(shiny)
library(datasets)
library(geosphere)

mpgData <- mtcars
mpgData <- factor(mpgData$am, labels = c("Automatic", "Manual"))

airports <- read.csv("http://datasets.flowingdata.com/tuts/maparcs/airports.csv", header=TRUE) 
flights <- read.csv("C:\\Users\\John\\Dropbox\\CS\\BitBend\\bitbend_data_test\\johnshiny\\stdev_data.csv", header=TRUE, as.is=TRUE)

# Unique carriers
carriers <- unique(flights$airline)

# Color
pal <- colorRampPalette(c("#f2f2f2", "red"))

colors <- pal(100)

xlim <- c(-171.738281, -56.601563)
ylim <- c(12.039321, 71.856229)


shinyServer(function(input, output) {
    
    output$dataImage <- renderImage({
    
        outfile <- paste(input$airline, ".png", sep="")
        png(outfile, width=3200, height=2400)
        map("world", col="#191919", fill=TRUE, bg="#000000", lwd=0.05, xlim=xlim, ylim=ylim)
        fsub <- flights[flights$airline == input$airline,]
        fsub <- fsub[order(fsub$stdev),]
        maxstdev <- max(fsub$stdev)
        for (j in 1:length(fsub$airline)) {
            air1 <- airports[airports$iata == fsub[j,]$airport1,]
            air2 <- airports[airports$iata == fsub[j,]$airport2,]
            
            inter <- gcIntermediate(c(air1[1,]$long, air1[1,]$lat), c(air2[1,]$long, air2[1,]$lat), n=100, addStartEnd=TRUE)
            colindex <- round( (fsub[j,]$stdev / maxstdev) * length(colors) )
                    
            lines(inter, col=colors[colindex], lwd=0.6)
        }
        
        dev.off()
        
        list(src = outfile,
            contentType = 'image/png',
            width = 800,
            height = 600,
            alt = "This is alternate text")

    }, deleteFile = TRUE)
    
    output$table <- renderTable({
        fsub <- flights[flights$airline == input$airline,]
        fsub <- fsub[order(fsub$stdev),]
        data.frame(fsub)
    })
})