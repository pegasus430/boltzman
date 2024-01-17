import config.config as config
import datetime

from exceptions.exceptions import *



def fast_forward_time(time_stamp, market_code):
    exchange = config.EXCHANGES[market_code]
    date_obj = datetime.datetime.fromtimestamp(time_stamp)
    local_time_stamp = date_obj.time().hour * 60 * 60 + date_obj.time().minute * \
        60 + date_obj.time().second
    local_begin = exchange["activeTime"][0] * \
        60 * 60 + exchange["activeTime"][1] * 60
    local_end = exchange["activeTime"][2] * \
        60 * 60 + exchange["activeTime"][3] * 60
    if local_time_stamp > local_end or local_time_stamp < local_begin or not date_obj.weekday() in exchange["activeDays"]:
        if local_time_stamp > local_end:
            date_obj = date_obj + datetime.timedelta(days=1)
        date_obj = date_obj.replace(
            hour=exchange["activeTime"][0], minute=exchange["activeTime"][1], second=0)
    while not date_obj.weekday() in exchange["activeDays"]:
        date_obj = date_obj + datetime.timedelta(days=1)

    return date_obj.timestamp()


def is_asset_active(time_stamp, market_code):
    exchange = config.EXCHANGES[market_code]
    date_obj = datetime.datetime.fromtimestamp(time_stamp)
    local_time_stamp = date_obj.time().hour * 60 * 60 + date_obj.time().minute * \
        60 + date_obj.time().second
    local_begin = exchange["activeTime"][0] * \
        60 * 60 + exchange["activeTime"][1] * 60
    local_end = exchange["activeTime"][2] * \
        60 * 60 + exchange["activeTime"][3] * 60
    if not date_obj.weekday() in exchange["activeDays"]:
        return False

    if local_time_stamp > local_end or local_time_stamp < local_begin:
        return False

    return True

def make_sure(condition, error_string):
    '''
        prod time assert
        Throw an exception with given text if condition is not true
    '''
    if not condition:
        raise AssertionError(error_string)

def validate(condition, error_string):
    '''
        Does the same thing with make_sure but raises an ExposedException where these exceptions may be returned to frontend
    '''
    if not condition:
        raise ExposedException(error_string)
