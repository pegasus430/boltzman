import sys
sys.path.append('..')

from core.aibase import AIAggregationType
from core.aidataport import AIDataport
from datetime import datetime


test_data = [
    {
        "desc": "simple same day",
        "date_params": [2021, 8, 13, 10, 0],
        "symbol": "FB",
        "record_count": 5,
        "aggregation_type": AIAggregationType.OneHour,
        "expected": [1628866800, 1628870400, 1628874000, 1628877600, 1628881200],
        "is_input_dp": False

    },
    {
        "desc": "carrying next day",
        "date_params": [2021, 8, 13, 14, 1],
        "symbol": "FB",
        "record_count": 8,
        "aggregation_type": AIAggregationType.OneHour,
        "expected": [1628881200, 1629118800, 1629122400, 1629126000, 1629129600, 1629133200, 1629136800, 1629140400],
        "is_input_dp": False

    },
    {
        "desc": "before hours",
        "date_params": [2021, 8, 13, 4, 23],
        "symbol": "GOOGL",
        "record_count": 5,
        "aggregation_type": AIAggregationType.OneHour,
        "expected": [1628859600, 1628863200, 1628866800, 1628870400, 1628874000],
        "is_input_dp": False

    },
    {
        "desc": "before hours + next day",
        "date_params": [2021, 8, 12, 4, 23],
        "symbol": "GOOGL",
        "record_count": 12,
        "aggregation_type": AIAggregationType.OneHour,
        "is_input_dp": False,
        "expected": [1628773200, 1628776800, 1628780400, 1628784000, 1628787600, 1628791200, 1628794800, 1628859600, 1628863200, 1628866800, 1628870400, 1628874000]
    },
    {
        "desc": "before hours + weekend + monday",
        "date_params": [2021, 8, 13, 4, 23],
        "symbol": "GOOGL",
        "record_count": 12,
        "aggregation_type": AIAggregationType.OneHour,
        "is_input_dp": False,
        "expected": [1628859600, 1628863200, 1628866800, 1628870400, 1628874000, 1628877600, 1628881200, 1629118800, 1629122400, 1629126000, 1629133200, 1629136800],
    },
    {
        "desc": "after hours single day",
        "date_params": [2021, 8, 12, 19, 23],
        "symbol": "GOOGL",
        "record_count": 7,
        "aggregation_type": AIAggregationType.OneHour,
        "expected": [1628859600, 1628863200, 1628866800, 1628870400, 1628874000, 1628877600, 1628881200],
        "is_input_dp": False
    },
    {
        "desc": "after hours two days overlay day",
        "date_params": [2021, 8, 11, 19, 23],
        "symbol": "GOOGL",
        "record_count": 14,
        "aggregation_type": AIAggregationType.OneHour,
        "expected": [1628773200, 1628776800, 1628780400, 1628784000, 1628787600, 1628791200, 1628794800, 1628859600, 1628863200, 1628866800, 1628870400, 1628874000, 1628877600, 1628881200],
        "is_input_dp": False
    },
    # input dp tests

    {
        "desc": "simple same day",
        "date_params": [2021, 8, 13, 14, 1],
        "symbol": "FB",
        "record_count": 4,
        "aggregation_type": AIAggregationType.OneHour,
        "expected": [1628863200, 1628866800, 1628870400, 1628874000],
        "is_input_dp": True

    },
    {
        "desc": "carrying prev day",
        "date_params": [2021, 8, 12, 9, 30],
        "symbol": "GOOGL",
        "record_count": 7,
        "aggregation_type": AIAggregationType.OneHour,
        "expected": [1628690400, 1628694000, 1628697600, 1628701200, 1628704800, 1628708400, 1628773200],
        "is_input_dp": True

    },
    {
        "desc": "before hours",
        "date_params": [2021, 8, 13, 4, 23],
        "symbol": "GOOGL",
        "record_count": 5,
        "aggregation_type": AIAggregationType.OneHour,
        "expected": [1628780400, 1628784000, 1628787600, 1628791200, 1628794800],
        "is_input_dp": True

    },
    {
        "desc": "before hours + prev day",
        "date_params": [2021, 8, 12, 4, 23],
        "symbol": "GOOGL",
        "record_count": 12,
        "aggregation_type": AIAggregationType.OneHour,
        "is_input_dp": True,
        "expected": [1628607600, 1628611200, 1628614800, 1628618400, 1628622000, 1628686800, 1628690400, 1628694000, 1628697600, 1628701200, 1628704800, 1628708400]
    },
    {
        "desc": "before hours + weekend + friday + thursday",
        "date_params": [2021, 8, 16, 4, 23],
        "symbol": "GOOGL",
        "record_count": 12,
        "aggregation_type": AIAggregationType.OneHour,
        "is_input_dp": True,
        "expected": [1628780400, 1628784000, 1628787600, 1628791200, 1628794800, 1628859600, 1628863200, 1628866800, 1628870400, 1628874000, 1628877600, 1628881200]
    },
    {
        "desc": "after hours single day",
        "date_params": [2021, 8, 12, 19, 23],
        "symbol": "GOOGL",
        "record_count": 7,
        "aggregation_type": AIAggregationType.OneHour,
        "expected": [1628773200, 1628776800, 1628780400, 1628784000, 1628787600, 1628791200, 1628794800],
        "is_input_dp": True
    },
    {
        "desc": "after hours two days overlay day",
        "date_params": [2021, 8, 12, 19, 23],
        "symbol": "GOOGL",
        "record_count": 14,
        "aggregation_type": AIAggregationType.OneHour,
        "expected": [1628686800, 1628690400, 1628694000, 1628697600, 1628701200, 1628704800, 1628708400, 1628773200, 1628776800, 1628780400, 1628784000, 1628787600, 1628791200, 1628794800],
        "is_input_dp": True
    }


]


def _dp_pull(params, test_name=None):
    if test_name and not params["desc"] == test_name:
        return
    dt = datetime(params["date_params"][0], params["date_params"][1], params["date_params"][2],
                  params["date_params"][3], params["date_params"][4])
    ts = datetime.timestamp(dt)
    dp: AIDataport = AIDataport(params["symbol"],
                                params["record_count"], params["aggregation_type"], params["is_input_dp"])
    records = list(dp.pull_data(ts))
    i = 0
    generated_ts = []
    print("Testing :", params["desc"], "  input dp" if params["is_input_dp"] == True
          else "  output dp")
    target_dt = datetime.fromtimestamp(ts)
    print("==>", target_dt, target_dt.strftime("%A"))

    for rec in records:
        dt_object = datetime.fromtimestamp(rec[3])
        #print(dt_object, dt_object.strftime("%A"), rec[3])
        generated_ts.append(rec[3])
        assert(rec[3] == params["expected"][i])
        i += 1
    #print(generated_ts)


def test_prediction_matured():
    test_data = [{  
        'desc' : 'regular day , no overlsy',
        'aggregation': AIAggregationType.FifteenMinutes,
        'prediction_time': [2021, 8, 13, 4, 23, 10],
        'mature_time': [2021, 8, 13, 4, 23, 10],
        'size': 4},
        { 
        'desc' : 'begin friday before hours end Monday',
        'aggregation': AIAggregationType.OneHour,
        'prediction_time': [2021, 8, 13, 4, 23, 10],
        'mature_time': [2021, 8, 16, 10, 30, 0],
        'size': 8},
        { 
        'desc' : 'begin mid day end next day',
        'aggregation': AIAggregationType.OneHour,
        'prediction_time': [2021, 8, 11, 11, 23, 10],
        'mature_time': [2021, 8, 16, 10, 30, 0],
        'size': 8}
    ]
    for params in test_data:
        dp = AIDataport("GOOGL", params['size'], params["aggregation"], False)
        dt = datetime(params["prediction_time"][0], params["prediction_time"][1], params["prediction_time"][2],
                      params["prediction_time"][3], params["prediction_time"][4], params['prediction_time'][5])

        p_ts = dt.timestamp()
        m_ts = dp.predicton_matured_time(p_ts)
        mt = datetime.fromtimestamp(m_ts)
        print(f'{dt} {dt.strftime("%A")}=> {mt} {mt.strftime("%A")}')


def test_data_pulls():
    for params in test_data:
        _dp_pull(params)


test_prediction_matured()
#test_data_pulls()
