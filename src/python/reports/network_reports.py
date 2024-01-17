from config import config
from utils.psqlutils import PsqlUtils 
sql_utils = PsqlUtils()

def network_stats():
    query ='''SELECT AVG (timeSeriesCurrentValue) as value, 
                    timeSeriesClass as class, 
                    timeSeriesName as name, 
                    (timeSeriesStamp / {0} * {0}) as timeStamp 

        FROM  timeSeries 
        WHERE timeSeriesStamp > 0 
        AND timeSeriesName = '{1}' 
        GROUP BY timeSeriesName , timeSeriesClass, timeStamp \
        Order By timeStamp DESC\
        LIMIT {2}'''.format(self.params["aggregation_type"].value,
                                self.params["symbol"],
                                self.params["size"])                                    
    rv = None
    for rec in sql_utils.run_select_query(query):
        rv = rec[3]
    return rv    