library(RSQLite)
library(ggplot2)


query_db <- function(sql,db) {
	drv <- dbDriver('SQLite')
	con <- dbConnect(drv, db)
	res <- dbGetQuery(con, sql)
}

parse_data <- function(db) {
	print('Loading Data')
  	data <- query_db('SELECT QDATE, MARKET, CXR, DDATE, DFLIGHT, FARE from flightdata',db)

  	data$QDATE <- as.Date(as.character(data$QDATE), '%Y%m%d%H%M')
	data$DDATE <- as.Date(data$DDATE, '%Y-%m-%d')
	data$DFLIGHT <- as.numeric(data$DFLIGHT)
	data$FARE <- as.numeric(data$FARE)
	data$DTD <- as.numeric(difftime(data$DDATE,data$QDATE,units='days'))

	return(data)
}

sd_by_dtd <- function(data) {
	aggdata <- aggregate(data$FARE, by=list(data$DTD, data$DFLIGHT), FUN=sd, na.rm=TRUE)
	names(aggdata) <- c('DTD', 'DFLIGHT', 'SD')
	aggdata2 <- aggregate(aggdata$SD, by=list(aggdata$DTD), FUN=mean, na.rm=TRUE)
	#print(aggdata)

	p <- ggplot()
	df <- data.frame(DTD = aggdata2$'Group.1', SD = aggdata2$x)
	p  <- p + geom_point(data = df, aes(x = DTD, y = SD)) + labs(title = 'Average Standard Deviation of Flight Price') + scale_x_reverse() + ylab('Average Standard Deviation')		    + xlab('Days until Departure')
	print(p)

	return(aggdata2)
}















