import os
import datetime as dt
# Paths
DIR = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
ASSETS_DIR = os.path.join(DIR,'assets')
DATA_DIR = os.path.join(DIR,'data')

CREDS_PATH = os.path.join(ASSETS_DIR,'creds.json')
TOKEN_PATH = os.path.join(ASSETS_DIR,'token.pkl')
DB_PATH = os.path.join(DATA_DIR,'database.db')
GOALS_PATH = os.path.join(ASSETS_DIR,'Goals.xlsx')

# Refresh time in seconds
REFRESH_TIME = 8*60*60 # 8 hours
DAEMON_SLEEP = 60 # 1 minute
DAYS_TO_UPDATE = 7
RATE_LIMIT = 150 - (DAYS_TO_UPDATE + 2) # 150 requests per HOUR - initial backdate request eg 7 for macros (have to request each day individually) + 2 for steps and bodyweight (time series requests)
NUM_REQUESTS_PER_UPDATE = 3 # STEPS + BODYWEIGHT + MACROS (Macros doesn't have a time series request) 
SLEEP_TIME = int(3600 / (RATE_LIMIT/NUM_REQUESTS_PER_UPDATE))+1

# Data Constants
START_DATE = dt.datetime(2022, 12, 31)
FIG_START_DATE = dt.datetime(2024, 12, 1)
LBS_TO_KG =  0.45359237
KG_TO_LBS = 1/LBS_TO_KG
CALORIES_PER_LB = 3500

#SQL
NEWEST_DATA_QUERY = '''
SELECT fitbit.*
FROM fitbit
JOIN (
    SELECT dateTime, MAX(scrapeTime) AS maxScrapeTime
    FROM fitbit
    GROUP BY dateTime
) grouped
ON fitbit.dateTime = grouped.dateTime AND fitbit.scrapeTime = grouped.maxScrapeTime
WHERE fitbit.dateTime > '{}'
'''.format(START_DATE.strftime('%Y-%m-%d'))

ALL_DATA_QUERY = '''
SELECT *
FROM fitbit
'''
