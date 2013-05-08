'''
This file generates the regressand for our logistic model, the change in flight price.
Note: The fare dictionary as currently generated is a very large object and can
often lead to memory errors if other programs are using up a lot of memory. Future versions
will implement this as a database.

Usage:

#Example for the 3 day fare difference
delta_t = 3
fare_dict = gen_fare_dict(gen_fare_data())
add_price_diff_col(fare_dict,delta_t)
'''
import sys
import sqlite3
from dateutil.parser import parse
import datetime

def execute_query(sql,con):
    cur = con.cursor()
    cur.execute(sql)
    rv = cur.fetchall()
    return rv

def get_fare_data():
	'''
	Reads fare data grouped by airline, flight number, and depature data, ie. the identifying 
	characteristics from the main database
	'''
    con = sqlite3.connect('flight_data.db')
    sql = 'SELECT CXR, DFLIGHT, DDATE, GROUP_CONCAT(QDATE), GROUP_CONCAT(FARE) FROM flightdata GROUP BY CXR, DFLIGHT, DDATE'
    res = execute_query(sql,con)
    con.close()
    return res

def gen_fare_dict(data):
	'''
	Generates a nested dictionary of fare prices sorted by
	Airline 'CXR' -> Flight Number 'DFLIGHT' -> Depature Date 'DDATE' -> Query Date 'QDATE' 
	'''
	con = sqlite3.connect('flight_data.db')
	airlines = execute_query('SELECT DISTINCT CXR FROM flightdata',con)
	airlines = [str(x[0]) for x in airlines]
	dflights = execute_query('SELECT DISTINCT DFLIGHT FROM flightdata',con)
	dflights = [int(x[0]) for x in dflights]
	ddates = execute_query('SELECT DISTINCT DDATE FROM flightdata',con)
	ddates = [str(x[0]) for x in ddates]
	con.close()
	rv = {}
	#Generate Dictionary
	for airline in airlines:
		rv[airline] = {}
		for dflight in dflights:
			rv[airline][dflight] = {}
			for ddate in ddates:
				rv[airline][dflight][ddate] = {}
	#Populate Dictionary
	for x in data:
		CXR = str(x[0])
		DFLIGHT = int(x[1])
		DDATE = str(x[2])
		QDATE = [str(i[:-2]) for i in str(x[3]).split(',')]
		FARE = [float(i) for i in str(x[4]).split(',')]
		for i in range(len(QDATE)):
			rv[CXR][DFLIGHT][DDATE][QDATE[i]] = FARE[i]
	return rv

def get_price_diff(row,fare_dict,delta_t):
	'''
	Computes the change in fare over the next n 'delta_t' days and returns 1 if the fare increases
	and 0 if the fare decreases
	'''
    current_fare = float(row[6])
    current_date = parse(str(int(row[0])))
    future_date = (current_date + datetime.timedelta(days=delta_t)).strftime('%Y%m%d%H%M')
    if future_date in fare_dict[str(row[2])][int(row[5])][str(row[3])]:
        future_fare = fare_dict[str(row[2])][int(row[5])][str(row[3])][future_date]
        if future_fare > current_fare:
            return 1
        else:
            return 0
    else:
        return -1
        
def update_db(rows, db):
	'''
	Generates a new database to store the data for the regression
	'''
    con = sqlite3.connect(db)
    headers = ['QDATE', 'MARKET', 'CXR', 'DDATE', 'DTIME', 'DFLIGHT', 'FARE', 'DFARE']
    cur = con.cursor()
    con.execute('create table if not exists flightdata(' + ', '.join(headers) + ')')
    for row in rows:
        con.execute('insert into flightdata(%s) values (%s)' \
                % (', '.join(headers), ', '.join(len(headers)*['?'])) ,row)
    con.commit()
    con.close()

def add_price_diff_col(fare_dict,delta_t):
	'''
	Reads existing database, generates a new column for change in fare and
	feeds that data into a new database to be used for analysis
	'''
	db_name = 'flight_data_' + str(delta_t) + '.db'
    con = sqlite3.connect(db_name)
    sql = 'SELECT QDATE, MARKET, CXR, DDATE, DTIME, DFLIGHT, FARE FROM flightdata'
    cur = con.cursor()
    cur.arraysize = 5000
    cur.execute(sql)
    res = cur.fetchmany()
    while res:
        res = [list(x) for x in res]
        for i,r in enumerate(res):
            res[i].append(get_price_diff(r,fare_dict,delta_t))
        update_db(res,'flight_data_new.db')
        res = cur.fetchmany()
    con.close()

def main(argv):
	add_price_diff_col(gen_fare_dict(gen_fare_data()),argv[1])