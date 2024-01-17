import pyEX
#client = pyEX.Client(api_token="pk_5eec2e7eb99945c588d1bf1b84346a93", version='stable', api_limit=5)

#results = client.stocks.batch(["APPL", "GOOGL"], fields=None, range_='1m', last=10,   filter='', format='json')
#print (results)

def double (x, limit, cap):
    if(limit == cap):
        return x
    limit = limit + 1
    x = x - x* 0.05
    return double(x + x * 0.10 + 15000, limit, cap)

for year in range (1,30):
    print (year, double(0, 1, year))
