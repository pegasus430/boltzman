API_URL = "https://cloud.iexapis.com/"
TOKEN = 'pk_5eec2e7eb99945c588d1bf1b84346a93'
import datetime
from utils.iex import IEX

iex = IEX (API_URL, TOKEN)

def pull_symbol_data (symbols, first_date, last_date):
    for symbol in symbols:
        date_cur= first_date
        while date_cur <= last_date:
            date_str = date_cur.strftime("%Y%m%d")
            iex.pull_historical_data(symbol , date_str)
            date_cur = date_cur + datetime.timedelta(days=1)


date_begin = datetime.datetime(2021, 1, 1)
date_end = datetime.datetime(2022, 6, 30)

pull_symbol_data (["TSLA", "AAPL", "GOOGL", "FB", "MSFT"], date_begin, date_end)
