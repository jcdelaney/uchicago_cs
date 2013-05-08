'''
This file takes care of downloading the data, initial preprocessing
and construction of the local database.

Usage:

update_db(username,password)
'''

from ftplib import FTP
from StringIO import StringIO
import dateutil.parser
import sqlite3

def pull_csv(dir_list,ftp):
    '''
    Pulls a CSV file from the ftp server and reads its contents. Also maintains
    a list of processed files and adds each file to that list as it is processed.
    '''
    try:
        with open('parsed_list.txt','r+') as parsed_list:
            parsed_query_list = [line.strip('\n') for line in parsed_list.readlines()]
            
        for file in dir_list:
            if file.endswith('.csv') and len(file.split('_')) == 5 \
                                    and file not in parsed_query_list:
                r = StringIO()
                print 'Now Downloading %s' % file
                ftp.retrbinary('RETR ' + str(file), r.write)
                print 'Download Complete'
                query_date = file.split('_')[1]
                query_contents = [[x.strip('"') for x in line.split(',')] \
                                    for line in r.getvalue().split('\n')][:-1]
                r.close()
                yield {'date':query_date,'contents':query_contents}
                parsed_query_list.append(file)
    
    except KeyboardInterrupt as ex:
        print ex, ': saving parsed file list'
        raise
    finally:
        with open('parsed_list.txt','w') as parsed_list:
            for query in parsed_query_list:
                parsed_list.write('%s\n' % query)
                
def parse_query(query):
    '''
    Parses the contents of a CSV file and loads the data into the database
    '''
    try:
        con = sqlite3.connect('flight_data.db')
        for i,row in enumerate(query['contents']):
            if i == 0:
                headers = row
                headers.insert(0,'QDATE')
                con.execute('create table if not exists flightdata(' +
                            ', '.join(headers) + ')')
            else:
                row.insert(0,query['date'])
                for j,val in enumerate(row):
                    #Converts date into a more readable/sortable format
                    if j == headers.index('DDATE'):
                        row[j] = dateutil.parser.parse(val).strftime('%Y-%m-%d')
                    else:
                        try:
                            row[j] = float(val)
                        except ValueError:
                            pass  
                if row[headers.index('CURRENCY')] == 'USD':            
                    con.execute('insert into flightdata(%s) values (%s)' %\
                             % (', '.join(headers), ', '.join(len(headers)*['?'])) ,row)
                                
    except KeyboardInterrupt as ex:
        print ex, ': terminating database connection'
        con.close()
        raise
    else:
        con.commit()
        con.close()
                
def update_db(username,password):
    try:
        ftp = FTP('ftp.tripbend.com',username,password)
        r = StringIO()
        dir_list = ftp.nlst()
        print 'Connected to Server'
        num_added = 0
        for query in pull_csv(dir_list,ftp):
            parse_query(query)
            num_added += 1
            
    except KeyboardInterrupt as ex:
        print ex, ': terminating ftp connection'
    finally:
        ftp.close()
        print '%d files added' % num_added