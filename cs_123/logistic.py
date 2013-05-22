import sqlite3
import datetime
import pandas as pd
from pandas.io import sql
import statsmodels.api as sm
import pylab as pl
import numpy as np
import random


def dateParser(s, t):
    if t == 0:
        return datetime.datetime(int(s[0:4]), int(s[4:6]), int(s[6:8]))
    elif t == 1:
        return datetime.datetime(int(s[0:4]), int(s[5:7]), int(s[8:10]))

def time_of_day(x):
    if x <= 9:
        return 0
    elif x <= 12:
        return 1
    elif x <= 17:
        return 2
    else:
        return 3

def day_diff(x):
    return int((x[0] - x[1]).total_seconds()/(60*60*24))


def parse_data(sample_size):
    cnx = sqlite3.connect('flight_data_3.db')
    df = sql.read_frame('SELECT QDATE, MARKET, CXR, DDATE, DTIME, DFLIGHT, FARE, DFARE from flightdata;',cnx)
    df['QDATE'] = df['QDATE'].apply(lambda x: dateParser((str(int(x))),0))
    df['DDATE'] = df['DDATE'].apply(lambda x: dateParser(x,1))
    df['DTIME'] = df['DTIME'].apply(lambda x: int(x[:2]))
    df['DTD'] = df[['DDATE','QDATE']].apply(day_diff, axis = 1)
    df['QDAY'] = df['QDATE'].apply(lambda x: x.weekday())
    df['DDAY'] = df['DDATE'].apply(lambda x: x.weekday())
    df['DCHUNK'] = df['DTIME'].apply(time_of_day)
    df['DMONTH'] = df['DDATE'].apply(lambda x: x.strftime('%m'))

    '''
    This part of the code does not yet work
    '''
    MARKET_dummies = pd.get_dummies(df['MARKET'], prefix = 'MARKET')
    CXR_dummies = pd.get_dummies(df['CXR'], prefix = 'CXR')
    QDAY_dummies = pd.get_dummies(df['QDAY'], prefix = 'QDAY')
    DDAY_dummies = pd.get_dummies(df['DDAY'], prefix = 'DDAY')
    DCHUNK_dummies = pd.get_dummies(df['DCHUNK'], prefix = 'DCHUNK')
    MARKET_dummies = pd.get_dummies(df['MARKET'], prefix = 'MARKET')
    DMONTH_dummies = pd.get_dummies(df['DMONTH'], prefix = 'DMONTH')

    return df

    #df['DTD'] = 




