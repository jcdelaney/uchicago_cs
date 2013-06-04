import sqlite3
import datetime
import time
import pandas as pd
from pandas.io import sql
import pylab as pl
import numpy as np
import random
from itertools import product, izip
from pyper import *

def dateParser(s, date_type):
    '''
    This function parses dates as stored in the database and returns datetime objects
    '''
    if date_type == 0:
        return datetime.datetime(int(s[0:4]), int(s[4:6]), int(s[6:8]))
    elif date_type == 1:
        return datetime.datetime(int(s[0:4]), int(s[5:7]), int(s[8:10]))

def time_of_day(x):
    '''
    Converts hours as an integer to a subset of the day 
    i.e. early morning, morning, afternoon etc.
    '''
    if x <= 9:
        return 0
    elif x <= 12:
        return 1
    elif x <= 17:
        return 2
    else:
        return 3

def day_diff(x):
    '''
    Computes the difference in days between two datetime objects
    '''
    return int((x[0] - x[1]).total_seconds()/(60*60*24))

def standardize_p(x,m):
    '''
    Calculate percent deviation
    '''
    return (float(x) - float(m))/float(m)

def process_fare(df,verbose):
    '''
    Normalizes fare prices by considering subsets of the data that share days till departure,
    depature day of the week, and departure time of day and computing the percent deviation
    from the average of this set
    '''
    if verbose:
        print "Progress:"
    c = 0
    i = 0
    n = len(df['FARE'])
    for dtd, day, chunk in product(set(df['DTD']), range(7), range(4)):
        fare = 0
        fare = df[df.DTD == dtd][df.DDAY == day][df.DCHUNK == chunk]['FARE']
        i += 1
        c += len(fare)
        if i % 100 == 0 and verbose:
            print str(float(c)/float(n)) + '%'
        m = np.mean(fare)
        if m == m - m:
            return fare
        df.update(fare.apply(lambda x: standardize_p(x,m)))

    return df['FARE']

def gen_fare_dict(df):
    '''
    Generates a nested dictionary of fare prices of the form
    Airline -> Flight Number -> Departure Date -> Query Date
    '''
    rv = {}
    airlines = set(df['CXR'])
    dflights = set(df['DFLIGHT'])
    ddates = set(df['DDATE'].apply(lambda x: x.strftime('%Y%m%d%H%M')))
    for airline in airlines:
        rv[airline] = {}
        for dflight in dflights:
            rv[airline][dflight] = {}
            for ddate in ddates:
                rv[airline][dflight][ddate] = {}
    for airline, fnumber, fare, ddate, qdate in izip(df['CXR'], df['DFLIGHT'], df['FARE'],
                                                     df['DDATE'].apply(lambda x: x.strftime('%Y%m%d%H%M')),
                                                     df['QDATE'].apply(lambda x: x.strftime('%Y%m%d%H%M'))):
        rv[airline][fnumber][ddate][qdate] = fare
    return rv

def get_fare_delta(row, delta_t, fare_dict, r_type = 'binary', time = 'future'):
    '''
    Calculates the interval difference in fare prices. 
    Parameters:
        r_type: 'binary' ->  returns the difference in fare price as a binary variable
                             where 1 indicates an increase in fare price and a 0
                             indicates a decrease in fare price
                'numeric' -> returns the numeric difference
                'percent' -> returns the percent change

        time:   'future' -> computes the fare difference delta_t days in the future
                'past'   -> computes the fare difference delta_t days in the past

    '''
    if r_type not in ['binary','numeric','percent']:
        raise TypeError('Invalid return type')
    if time not in ['past','future']:
        raise TypeError('Invalid return type')
    current_fare = row['FARE']
    if time == 'future': 
        delta_date = (row['QDATE'] + datetime.timedelta(days=delta_t)).strftime('%Y%m%d%H%M')
    if time == 'past': 
        delta_date = (row['QDATE'] - datetime.timedelta(days=delta_t)).strftime('%Y%m%d%H%M')
    if delta_date in fare_dict[row['CXR']][row['DFLIGHT']][row['DDATE'].strftime('%Y%m%d%H%M')]:
        delta_fare = fare_dict[row['CXR']][row['DFLIGHT']][row['DDATE'].strftime('%Y%m%d%H%M')][delta_date]
        if r_type == 'binary': 
            return 1 * (delta_fare > current_fare)
        elif  r_type == 'numeric':
            return delta_fare - current_fare
        else:
            return (delta_fare - current_fare)/current_fare
    else:
        return np.nan

def parse_data(origin, destination, delta_t = 7, verbose=True):
    '''
    Reads data from flight_data.db for a given origin, destination pair
    and generates / transforms all the data fields necessary for analysis

    Data Name Dictionary:
        QDATE: Query Date
        CXR: Airline
        DFLIGHT: Flight Number
        DTIME: Local Departure Time
        DTD: Days to Departure
        QDAY: Query Day of Week
        DDAY: Departure Day of Week
        DCHUNK: Depature Time of Day eg. morning, afternoon etc.
        DMONTH: Departure Month
        FARE: Current Fare Price in USD
        NFARE: Normalized Fare Price (see process_fare for more information)
        DFARE: Binary reprentation of forward difference in fare price
               where 1 signigifies an increase and 0 a decrease
        DPFARE_i: Percent trailing difference in fare price back i periods

    '''
    if verbose:
        print 'Reading data from flight_data.db...'
    market = ', '.join(["".join(["'",origin, destination,"'"])] + ["".join(["'",destination,origin,"'"])])
    cnx = sqlite3.connect('flight_data_3.db')
    query = 'SELECT QDATE, CXR, DFLIGHT, DDATE, DTIME, FARE \
             from flightdata WHERE MARKET in (%s)' % market
    df = sql.read_frame(query,cnx)

    if verbose:
        print 'Processing Results'
    airlines = list(set(df['CXR']))
    air_code_dict = {airline:i for i,airline in enumerate(airlines)}
    df['CXR'] = df['CXR'].apply(lambda x: air_code_dict[x])
    df['QDATE'] = df['QDATE'].apply(lambda x: dateParser((str(int(x))),0))
    df['DDATE'] = df['DDATE'].apply(lambda x: dateParser(x,1))
    if verbose:
        print 'Computing Days till Departure'
    df['DTD'] = df[['DDATE','QDATE']].apply(day_diff, axis = 1)
    df['DTIME'] = df['DTIME'].apply(lambda x: int(x[:2]))
    df['QDAY'] = df['QDATE'].apply(lambda x: x.weekday())
    df['DDAY'] = df['DDATE'].apply(lambda x: x.weekday())
    df['DCHUNK'] = df['DTIME'].apply(time_of_day)
    df['DMONTH'] = df['DDATE'].apply(lambda x: x.strftime('%m'))

    fare_dict = gen_fare_dict(df)
    if verbose:
        print 'Computing Fare Differences'
    df['DFARE'] = df.apply(lambda x: get_fare_delta(x,delta_t,fare_dict), axis = 1)
    df['DPFARE_1'] = df.apply(lambda x: get_fare_delta(x,delta_t,fare_dict,r_type='percent',time='past'), axis = 1)
    df['DPFARE_2'] = df.apply(lambda x: get_fare_delta(x,delta_t,fare_dict,r_type='percent',time='past'), axis = 1)

    if verbose:
        print 'Normalizing Fare Prices'
    df['NFARE'] = process_fare(df,verbose)

    if verbose:
        print 'Dropping null values'
    return df.dropna()

def run_glm(df,k=10,detailed_results = False):
    '''
    Performs six logistic regressions using the models defined below.
    Prints the crossvalidated classification error alongside the mean
    of our binary dependant variable. This mean indicates a baseline
    performance level because random guessing would lead us to an error
    equal to this mean. With detailed reults enabled the summary for
    each regression is printed
    '''
    r = R(RCMD = 'C:\\Program Files\\R\\R-3.0.0\\bin\\R', use_numpy=True)
    r("library(boot)")
    df_np = df[['FARE', 'DFARE', 'DPFARE_1', 'DPFARE_2', 'NFARE', 'DTD', 'CXR', 'DDAY', 'DCHUNK']].to_records()
    r["data"] = df_np
    r("data$RANDOM <- rnorm(length(data$DFARE))")
    r("data$CXR <- factor(data$CXR)")
    r("data$DDAY <- factor(data$DDAY)")
    r("data$DCHUNK <- factor(data$DCHUNK)")

    baseline_model = ' + '.join(['RANDOM'])
    model_1 = ' + '.join(['FARE'])
    model_2 = ' + '.join(['FARE','DTD','CXR','DDAY','DCHUNK'])
    model_3 = ' + '.join(['NFARE'])
    model_4 = ' + '.join(['NFARE','DTD','CXR','DDAY','DCHUNK'])
    model_5 = ' + '.join(['NFARE','DPFARE_1','DPFARE_2','DTD','CXR','DDAY','DCHUNK'])

    models = [baseline_model,model_1,model_2,model_3,model_4,model_5]
    r("cost <- function(r, pi) mean(r==ifelse(pi > 0.5, 0, 1))")

    for i,model in enumerate(models):
        print "======"
        print "Model: DFARE = " + model
        print "======"
        r("data.glm_%d <- glm(DFARE ~ %s , data = data, family = 'binomial')" % (i,model))
        r("data.glm.error_%d <- cv.glm(data, data.glm_%d, cost, K=%d)" % (i,i,k))
        if detailed_results:
            print r("summary(data.glm_%d)" % i)
        print "DFARE Mean: %f" % np.mean(df['DFARE'])
        print "Model Error: " + str(r("data.glm.error_%d$delta" % i))
        if detailed_results:
            raw_input("Press Enter to continue...")
            print "\n"

def run_demo():
    print "Loading Datasets..."
    df_1 = parse_data("ORD", "SFO", verbose=False)
    df_2 = parse_data("ORD", "LAX", verbose=False)
    raw_input("Loading Complete, Press Enter to Continue to Analysis...")
    print "Results for O'Hare to San Fransisco International"
    run_glm(df_1,detailed_results=True)
    print "Results for O'Hare to LAX"
    run_glm(df_2,detailed_results=True)

