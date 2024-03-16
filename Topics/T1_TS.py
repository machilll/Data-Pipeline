#!/usr/bin/python3
import json
from kafka import KafkaConsumer
from kafka import KafkaProducer
import time
from dotenv import load_dotenv
from pathlib import Path
import os
import sys

parent_path = Path(__file__).parent.parent
sys.path.append(str(parent_path / 'logger'))
from log import Log


load_dotenv(dotenv_path=str(parent_path / '.env'))

logger = Log()

KAFKA_HOST_PORT = os.getenv('KAFKA_HOST_PORT', 9092)

logger.info(
    f"First Topic (T1_TS) - Making Connection with Consumer - On Port {KAFKA_HOST_PORT}")

consumer = KafkaConsumer(
    'T1_TS',
    group_id='consumer_services',
    enable_auto_commit=True,
    bootstrap_servers=[f'localhost:{KAFKA_HOST_PORT}'],
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

logger.info('First Topic (T3_DB) - Succussfully Connected')

producer = KafkaProducer(
    bootstrap_servers=[f'localhost:{KAFKA_HOST_PORT}'],
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

for message in consumer:
    print('HERE')
    logger.info(
        f"Partition:{message.partition}\tOffset:{message.offset}\tKey:{message.key}\tValue:{message.value}")

    data = message.value
    data['ts'] = time.strftime('%Y-%m-%d %H:%M:%S')
    producer.send('add_info', value=data)
    producer.flush()

    logger.info(
        f'First Topic (T3_DB) - id: {data["id"]} - first_name: {data["first_name"]} - Sent to second topic(add_info)')
