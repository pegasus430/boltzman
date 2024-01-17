from kafka import KafkaConsumer
consumer = KafkaConsumer('TEST', group_id='test_group_1', bootstrap_servers='localhost:39092')
for msg in consumer:
    print (msg)