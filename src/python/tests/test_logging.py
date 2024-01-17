import sys
from time import sleep
sys.path.append('..')

from utils.loggerfactory import logger
class TestLogger(object):
    def test_log(self):
        print ("in test_log")
        print (logger)
        logger().error("fasfsdfdf")
        logger().log_to_kafka ({"test_log2": "my name is arif b."} , "TOPIC_SERVICE_STATUS")




logTester = TestLogger()

logTester.test_log()
logTester.test_log()
logTester.test_log()
logTester.test_log()
logTester.test_log()
logTester.test_log()
logTester.test_log()
logTester.test_log()
