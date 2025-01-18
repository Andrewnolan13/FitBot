import datetime as dt
import pickle
import json
import time

from .fitbit import Fitbit, gather_keys_oauth2
from .token import FitbitTokenDaemon
from .utils import sleep
from .constants import TOKEN_PATH, CREDS_PATH

class FitbitServer(Fitbit):
    # time series data
    BODY = ['weight','fat','bmi']
    ACTIVITY = 'activityCalories calories caloriesBMR distance floors minutesSedentary minutesLightlyActive minutesFairlyActive minutesVeryActive steps'.split()
    FOODS = ['caloriesIn','water']
    TS_RESOURCE = dict(body = BODY,activities = ACTIVITY,foods = FOODS)

    def __init__(self, expires_at=None,redirect_uri=None, system='', **kwargs):
        self.client_id,self.client_secret = self.__get_creds()
        token = self.__get_token()
        super(FitbitServer,self).__init__(client_id = self.client_id,
                                          client_secret = self.client_secret,
                                          oauth2 = True,
                                          refresh_cb=self.__refresh_cb,
                                          access_token=token['access_token'],
                                          refresh_token=token['refresh_token'],
                                          expires_at=expires_at,
                                          redirect_uri=redirect_uri,
                                          system=system,
                                          **kwargs)
        self.client.refresh_token()
        self.__running = True
        self.token_daemon = FitbitTokenDaemon(self)
        self.token_daemon.start()
    
    @property
    def running(self):
        return self.__running
    
    @running.setter
    def running(self, val:bool):
        if not isinstance(val, bool):
            raise TypeError('running must be a boolean')
        self.__running = val
    
    def stop(self):
        self.running = False
    
    # Public Methods
    def _assertions(self,dtype:str,begin_date:dt.datetime,end_date:dt.datetime,resource:str,**kwargs):
        '''
        Function to assert the input parameters for the time series data functions.
        '''
        max_days = 30 if (dtype == 'activities' and resource == 'activityCalories') else 1095 

        assert dtype in self.TS_RESOURCE.keys(), "dtype not recognized."
        assert resource in self.TS_RESOURCE[dtype], "Resource not recognized."
        assert (begin_date or kwargs.get('period',None)), "Need to pass a begin_date or a period."
        assert not (begin_date and kwargs.get('period',None)), "Cannot pass both begin_date and period."
        
        if kwargs.get('period',None):
            assert type(kwargs['period']) == int, "Period must be an integer."
            assert kwargs['period'] > 0 and kwargs['period'] < max_days, f"Period must be between 1 and {max_days} days."
        if begin_date and end_date:
            assert begin_date < end_date, "Begin date must be before end date."
        

    def body_time_series(self,begin_date:dt.datetime = None,end_date:dt.datetime = None,resource:str=None,**kwargs):
        '''
        Function to get the body time series data.

        Parameters:
        begin_date:dt.datetime: The date from which to start the data retrieval. If None, period must be passed.
        end_date:dt.datetime: The date to end the data retrieval. Default is today.
        resource:str: The resource to get the data for. Default is weight. Options are weight, fat, bmi.
        
        **kwargs: 
        period = The period to get the data for. Must be an integer representing the number of days.

        '''
        dtype = 'body'
        url = '{0}/{1}/user/-/body/{resource}/date/{begin_date}/{end_date}.json'
        resource = resource or 'weight' #default to weight

        self._assertions(dtype,begin_date,end_date,resource,**kwargs)
        
        if not end_date:
            end_date = dt.datetime.now()
        if not begin_date:
            begin_date = end_date - dt.timedelta(days=kwargs['period'])
        begin_date = begin_date.strftime('%Y-%m-%d')
        end_date = end_date.strftime('%Y-%m-%d')

        payload = dict(resource=resource,begin_date=begin_date,end_date=end_date)
        url = url.format(*self._get_common_args(),**payload)

        return self.make_request(url)[f'{dtype}-{resource}']
    
    def activity_time_series(self,begin_date:dt.datetime = None,end_date:dt.datetime = None,resource:str=None,**kwargs):
        '''
        Function to get the activity time series data.

        Parameters:
        begin_date:dt.datetime: The date from which to start the data retrieval. If None, period must be passed.
        end_date:dt.datetime: The date to end the data retrieval. Default is today.
        resource:str: The resource to get the data for. Default is steps. Options are activityCalories, calories, caloriesBMR, distance, floors, minutesSedentary, minutesLightlyActive, minutesFairlyActive, minutesVeryActive, steps.

        **kwargs:
        period = The period to get the data for. Must be an integer representing the number of days.
        '''
        dtype = 'activities'
        url = '{0}/{1}/user/-/activities/{resource}/date/{begin_date}/{end_date}.json'
        resource = resource or 'steps' #default to weight

        self._assertions(dtype,begin_date,end_date,resource,**kwargs)

        if not end_date:
            end_date = dt.datetime.now()
        if not begin_date:
            begin_date = end_date - dt.timedelta(days=kwargs['period'])
        begin_date = begin_date.strftime('%Y-%m-%d')
        end_date = end_date.strftime('%Y-%m-%d')

        payload = dict(resource=resource,begin_date=begin_date,end_date=end_date)
        url = url.format(*self._get_common_args(),**payload)

        return self.make_request(url)[f'{dtype}-{resource}']
    
    def food_time_series(self,begin_date:dt.datetime = None,end_date:dt.datetime = None,resource:str=None,**kwargs):
        dtype = 'foods'
        url = '{0}/{1}/user/-/foods/log/{resource}/date/{begin_date}/{end_date}.json'
        resource = resource or 'caloriesIn'

        self._assertions(dtype,begin_date,end_date,resource,**kwargs)
        
        if not end_date:
            end_date = dt.datetime.now()
        if not begin_date:
            begin_date = end_date - dt.timedelta(days=kwargs['period'])
        begin_date = begin_date.strftime('%Y-%m-%d')
        end_date = end_date.strftime('%Y-%m-%d')

        payload = dict(resource=resource,begin_date=begin_date,end_date=end_date)
        url = url.format(*self._get_common_args(),**payload)

        return self.make_request(url)
    
    def get_macros_by_date(self,date:dt.datetime)->dict:
        '''
        Function to get the macronutrient data for a given date.
        '''
        url = '{0}/{1}/user/-/foods/log/date/{date}.json'
        date = date.strftime('%Y-%m-%d')
        url = url.format(*self._get_common_args(),date=date)
        return self.make_request(url)['summary']
    
    def macros_time_series(self,begin_date:dt.datetime=None,end_date:dt.datetime=None,**kwargs)->list[dict]:
        '''
        Function to get the macronutrient data for a given date range.
        '''
        self._assertions('foods',begin_date,end_date,'caloriesIn',**kwargs)
        if not end_date:
            end_date = dt.datetime.now()
        if not begin_date:
            begin_date = end_date - dt.timedelta(days=kwargs['period'])
        res = []
        while begin_date <= end_date:
            _dict = self.get_macros_by_date(begin_date)
            _dict['dateTime'] = begin_date.strftime('%Y-%m-%d')
            res.append(_dict)
            begin_date += dt.timedelta(days=1)
        return res
    
    def heart_time_series(self,begin_date:dt.datetime = None,end_date:dt.datetime = None,**kwargs):
        url = '{0}/{1}/user/-/activities/heart/date/{begin_date}/{end_date}.json'
        
        assert begin_date or kwargs.get('period',None), "Need to pass a begin_date or a period."
        assert not (begin_date and kwargs.get('period',None)), "Cannot pass both begin_date and period."
        if kwargs.get('period',None):
            assert type(kwargs['period']) == int, "Period must be an integer."
            assert kwargs['period'] > 0 and kwargs['period'] < 364, "Period must be between 1 and 364 days."
        
        if not end_date:
            end_date = dt.datetime.now()
        if not begin_date:
            begin_date = end_date - dt.timedelta(days=kwargs['period'])
        begin_date = begin_date.strftime('%Y-%m-%d')
        end_date = end_date.strftime('%Y-%m-%d')
        
        payload = dict(begin_date=begin_date,end_date=end_date)
        url = url.format(*self._get_common_args(),**payload)

        return self.make_request(url)['activities-heart']

    def sleep_time_series(self,begin_date:dt.datetime = None,end_date:dt.datetime = None,**kwargs):
        url = '{0}/{1}/user/-/sleep/date/{begin_date}/{end_date}.json'
        
        assert begin_date or kwargs.get('period',None), "Need to pass a begin_date or a period."
        assert not (begin_date and kwargs.get('period',None)), "Cannot pass both begin_date and period."
        if kwargs.get('period',None):
            assert type(kwargs['period']) == int, "Period must be an integer."
            assert kwargs['period'] > 0 and kwargs['period'] < 100, "Period must be between 1 and 100 days."
        
        if not end_date:
            end_date = dt.datetime.now()
        if not begin_date:
            begin_date = end_date - dt.timedelta(days=kwargs['period'])
        begin_date = begin_date.strftime('%Y-%m-%d')
        end_date = end_date.strftime('%Y-%m-%d')
        
        payload = dict(begin_date=begin_date,end_date=end_date)
        url = url.format(*self._get_common_args(),**payload)

        return self.make_request(url)['sleep']
    # Private methods 
    @staticmethod
    def __refresh_cb(token:dict)->None:
        '''
        Function to be passed to the FITBIT object to store the new token. If not passed, the app needs to be re-authed every time the script runs. The Access Token only lasts for an hour.
        '''
        assert [key in token for key in ['access_token', 'refresh_token', 'expires_at']], "Token is missing a key"
        with open(TOKEN_PATH, 'wb') as f:
            pickle.dump(token, f)

    @staticmethod
    def __get_creds()->tuple[str,str]:
        with open(CREDS_PATH, 'r') as f:
            creds = json.load(f)
        return creds['CLIENT_ID'], creds['CLIENT_SECRET']
    
    def __get_token(self)->dict:
        try:
            with open(TOKEN_PATH, 'rb') as f:
                token = pickle.load(f)
            if token['expires_at'] < time.time():
                token = self._authenticate()
        except FileNotFoundError:
            token = self._authenticate()
        except:
            raise
        return token

    def _authenticate(self)->dict:
        server = gather_keys_oauth2.OAuth2Server(self.client_id, self.client_secret)
        server.browser_authorize()
        token = server.fitbit.client.session.token
        self.__refresh_cb(token)
        return token

    def __del__(self):
        self.running = False
        self.token_daemon.stop()
        self.token_daemon.join()
        sleep(self.token_daemon.sleep_interval*2)
        super(FitbitServer, self).__del__()
