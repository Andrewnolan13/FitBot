import sqlite3
import datetime as dt
import pandas as pd
import threading

from .fitbit import exceptions
from .server import FitbitServer
from .utils import sleep
from .constants import (    RATE_LIMIT,
                            DAYS_TO_UPDATE,
                            NUM_REQUESTS_PER_UPDATE,
                            SLEEP_TIME,
                            DB_PATH)

def raise_or_return(df:pd.DataFrame,left_length:int,right_length:int)->pd.DataFrame:
    '''
    check if _merge column is not both, if so raise an error, otherwise return the dataframe
    '''
    if df['_merge'].value_counts()['both'] != len(df):
        raise ValueError('DataFrames did not merge correctly.')
    if left_length != right_length:
        raise ValueError('DataFrames are not the same length.')
    if left_length != len(df):
        raise ValueError('DataFrames did not merge correctly.')
    return df.drop(columns=['_merge'])

class FitbitDataDaemon(threading.Thread):
    def __init__(self):
        super().__init__()
        self.fs = FitbitServer()
        self.requestsRemaining = RATE_LIMIT
        self._stop_event = threading.Event()
        self.firstCall = True
    
    def stop(self):
        # self.conn.close()
        self.fs.stop()
        self._stop_event.set()
        self.join()
        print("FitbitDataDaemon stopped.")
    
    def run(self):
        self.__connect()
        self.main()

    def __connect(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.execute('PRAGMA journal_mode = WAL;')
        self.conn.cursor().execute('''CREATE TABLE IF NOT EXISTS fitbit (scrapeTime TEXT, 
                                                                        dateTime TEXT,
                                                                        steps INTEGER,
                                                                        weight REAL,
                                                                        calories INTEGER,
                                                                        carbs INTEGER,
                                                                        fat INTEGER,
                                                                        protein INTEGER,
                                                                        sodium INTEGER)''')
        self.conn.commit()
        
    def getData(self)->pd.DataFrame:
        days = DAYS_TO_UPDATE if self.firstCall else 1
        steps:list[dict] = self.fs.activity_time_series(period=days) # dict(dateTime, value)
        weight:list[dict] = self.fs.body_time_series(period=days) # dict(dateTime, value)
        macros:list[dict] = self.fs.macros_time_series(period=days) # dict(dateTime, calories, carbs, fat, fiber, protein, sodium)

        df = pd.DataFrame(steps)
        df = pd.merge(df,pd.DataFrame(weight),on='dateTime',how='outer',suffixes=('_steps','_weight'), indicator=True).pipe(raise_or_return,len(steps),len(weight))
        df = pd.merge(df,pd.DataFrame(macros),on='dateTime',how='outer',suffixes=('','_macros'),indicator=True).pipe(raise_or_return,len(df),len(macros))
        df.columns = df.columns.str.replace('value_','')

        df.steps = df.steps.fillna(0).astype(int)
        df.weight = df.weight.fillna(0).astype(float)
        df.calories = df.calories.fillna(0).astype(int)
        df.carbs = df.carbs.fillna(0).astype(int)
        df.fat = df.fat.fillna(0).astype(int)
        df.protein = df.protein.fillna(0).astype(int)
        df.sodium = df.sodium.fillna(0).astype(int)
        df = df['dateTime steps weight calories carbs fat protein sodium'.split()]

        self.requestsRemaining -= NUM_REQUESTS_PER_UPDATE
        return df
    
    def getUpdatedData(self)->pd.DataFrame:
        '''
        From the database, select the most recent scrapeTime for each dateTime. Then, merge the new data with the database data and calculate the difference between the two.
        Only return the data that has changed.
        '''
        db = pd.read_sql('''
                            SELECT fitbit.*
                            FROM fitbit
                            JOIN (
                                SELECT dateTime, MAX(scrapeTime) AS maxScrapeTime
                                FROM fitbit
                                GROUP BY dateTime
                            ) grouped
                            ON fitbit.dateTime = grouped.dateTime AND fitbit.scrapeTime = grouped.maxScrapeTime
                            ''', self.conn)
        
        updatedData = (self.getData().merge(db, on='dateTime', how='left', suffixes=('_new','_old'))
            .fillna(0)
            .drop(columns=['scrapeTime'])
            .assign(steps = lambda x: x.steps_new - x.steps_old,
                    weight = lambda x: x.weight_new - x.weight_old,
                    calories = lambda x: x.calories_new - x.calories_old,
                    carbs = lambda x: x.carbs_new - x.carbs_old,
                    fat = lambda x: x.fat_new - x.fat_old,
                    protein = lambda x: x.protein_new - x.protein_old,
                    sodium = lambda x: x.sodium_new - x.sodium_old)
            .loc[lambda self: (self['steps weight calories carbs fat protein sodium'.split()].abs()>0).any(axis=1)]
            [['dateTime','steps_new','weight_new','calories_new','carbs_new','fat_new','protein_new','sodium_new']]
            .rename(columns={'steps_new':'steps',
                            'weight_new':'weight',
                            'calories_new':'calories',
                            'carbs_new':'carbs',
                            'fat_new':'fat',
                            'protein_new':'protein',
                            'sodium_new':'sodium'})
            .assign(scrapeTime = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        return updatedData
    
    def updateDatabase(self)->str:
        data = self.getUpdatedData()
        if not data.empty:
            data.to_sql('fitbit', self.conn, if_exists='append', index=False)
            return "FitbitDataDaemon saved to database. "
        return "FitbitDataDaemon no new data to save. "
    
    def main(self):
        while not self._stop_event.is_set():
            sleepTime = SLEEP_TIME
            report = "[{}] ".format(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            try:
                report += self.updateDatabase() + f"Requests remaining: {self.requestsRemaining}. "
            except exceptions.HTTPTooManyRequests:
                report += "FitbitDataDaemon encountered a rate limit error. Sleeping until top of the hour. "
                now = dt.datetime.now()
                topOfHour = now.replace(minute=0, second=0, microsecond=0)+dt.timedelta(hours=1)
                # sleep until one minute past the hour as the reset time is not exactly on the hour.
                # This prevents the script from hitting the rate limit again at the top of the hour
                # and then sleeping for another hour.
                sleepTime = (topOfHour-now).total_seconds()+60 
            except KeyboardInterrupt:
                report += "FitbitDataDaemon was interrupted. "
                sleepTime = 0
                self.stop()
                break
            except Exception as e:
                report += f"FitbitDataDaemon encountered an error: {e}. "
            finally:
                report += "[sleeping for {:,.0f}s]".format(sleepTime)
                print(report)
                sleep(sleepTime)
        self.conn.close()