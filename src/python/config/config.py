import datetime
from config.aitimegenerator import AITimeGenerator
API_URL = "https://cloud.iexapis.com/"
TOKEN = 'pk_5eec2e7eb99945c588d1bf1b84346a93'
DATABASE_FILE = "/Users/arifbilgin/Documents/test_db2.db"
MINIMUM_REQUIRED_DATA_POINTS_PER_DAY = 200
REAL_DATA_PULL_INTERVAL = 60
HISTORICAL_DATA_PULL_INTERVAL = 30  # 60 * 60 * 24
HISTORICAL_DATA_RETENTION_PERIOD = 90  # in days

BEGINNING_OF_TIME = 1
DISABLE_IEX_CALLS = False

USE_CACHED = True
date_str = datetime.datetime.now().strftime("%Y%m%d.%H.%M.%S.log")

CACHE_ROOT_DIRECTORY = "/home/arif/market_data_cache/"

#KAFKA_BROKERS_DEV_DOCKER = ['172.18.0.2:9092']
KAFKA_BROKERS_DEV_DOCKER = ['kafka:9090']
KAFKA_BROKERS_DEV = ['localhost:9092']
KAFKA_BROKERS_PROD_DOCKER = ['localhost:9092']
KAFKA_BROKERS_PROD = ['localhost:9092']
KAFKA_TOPICS = {
    "TOPIC_MODEL_READY": "TOPIC_MODEL_READY",
    "TOPIC_MODEL_TRAINING_ERROR": "TOPIC_MODEL_TRAINING_ERROR",
    "TOPIC_MODEL_NEEDS_TRAINING": "TOPIC_MODEL_NEEDS_TRAINING",
    "TOPIC_MODEL_NEEDS_PARTIAL_TRAINING": "TOPIC_MODEL_NEEDS_PARTIAL_TRAINING",
    # dead networks are dispatched to this topic
    "TOPIC_MODEL_CEMETERY": "TOPIC_MODEL_CEMETERY",
    "TOPIC_SERVICE_STATUS": "TOPIC_SERVICE_STATUS",  # topic to push service status
    "TOPIC_PREDICTIONS": "TOPIC_PREDICTIONS"  # topic to matured predictions
}
MAX_WORKER_NUMBER = 1  # default worker count for orchestrators
DEFAULT_MUTATOR_CAPACITY = 10
DEFAULT_MUTATION_PERC = 0.50

EXCHANGES = {
    "ARCX": {
        "optionClass": 0,
        "activeDays": [0, 1, 2, 3, 4],
        "activeTime": (9, 30, 15, 59)
    },
    "BATS": {
        "optionClass": 0,
        "activeDays": [0, 1, 2, 3, 4],
        "activeTime": (9, 30, 15, 59)
    },
    "XASE": {
        "optionClass": 0,
        "activeDays": [0, 1, 2, 3, 4],
        "activeTime": (9, 30, 15, 59)
    },
    "XNAS": {
        "optionClass": 0,
        "activeDays": [0, 1, 2, 3, 4],
        "activeTime": (9, 30, 15, 59)
    },
    "XNYS": {
        "optionClass": 0,
        "activeDays": [0, 1, 2, 3, 4],
        "activeTime": (9, 30, 15, 59)
    },
    "XPOR": {
        "optionClass": 0,
        "activeDays": [0, 1, 2, 3, 4],
        "activeTime": (9, 30, 15, 59)
    },
    "CRYPTO": {
        "optionClass": 1,
        "activeDays": [1, 2, 3, 4, 5, 6, 7],
        "activeTime": (0, 0, 24, 0)
    }

}
# symbols that has data and available for consumption
AVAILABLE_SYMBOLS = ["AAPL", "FB", "GOOGL", "MSFT", "TSLA"]

NETWORK_STATUS_THRESHOLDS = {  # TODO find a better respresenation ofthe threshold, what if ranges intersects
    "Dead": (-9999, 0),
    "Frozen": (1, 8),
    "Inactive": (9, 50),
    "Active": (50, 999999),
}

# when determining output y value for training this map is used to determine the normalized y-trianing values
# for instance if different in price is:
# 3% it maps to [1, 0, 0 ,0 ,0 ,0]
# 1.5% maps to  [0, 1 ,0 ,0 ,0 ,0]
# 0.03% maps to  [0, 0 ,1 ,0 ,0 ,0]
# -0.06% maps to  [0, 0 ,0 ,1 ,0 ,0]
# -0.6% maps to  [0, 0 ,0 ,0 ,1 ,0]
PROFIT_WEIGHT_MAP = [-5, -2.5, -0.05, 0.05, 2.5, 5]


# time to pull real time data for now, pulling real time data takes a while for now()
PREDICTION_MATURATION_BUFFER_TIME = 0

# maximum prediction count that a network can store
MAX_PREDICTION_SIZE = 100

_current_time = datetime.datetime.timestamp(
    (datetime.datetime.now() - datetime.timedelta(days=90)))

time_generator = AITimeGenerator(initial_time=(datetime.datetime.now() - datetime.timedelta(days=240)).timestamp(),
                                 anchor_to_real_time=False)


MODEL_FILES_LOCATION = "/Users/arifbilgin/model_data/"
MODEL_FILES_LOCATION_IN_DOCKER = "/usr/app/bin/service/model_data/"

# Status update interval in seconds
# Every SERVICE_STATUS_UPDATE_INTERVAL , AIService objects pushes update to kafka status topic
SERVICE_STATUS_UPDATE_INTERVAL = 5
NETWORK_STATUS_UPDATE_INTERVAL = 5


# Some constrains for new networks
INITIAL_NETWORK_MIN_DP_COUNT = 3
INITIAL_NETWORK_MAX_DP_COUNT = 10
INITIAL_NETWORK_MIN_DP_SIZE = 20
INITIAL_NETWORK_MAX_DP_SIZE = 40
INITIAL_NETWORK_MIN_LAYER_COUNT = 2
INITIAL_NETWORK_MAX_LAYER_COUNT = 8

INITIAL_NETWORK_MAX_LAYER_SIZE = 16
INITIAL_NETWORK_MIN_LAYER_SIZE = 8

ZOMBIE_HUNTER_INTERVAL = 3

SERVICE_DEFAULT_NOTIFICATION_CHECK_INTERVAL = 5