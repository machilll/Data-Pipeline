#!/usr/bin/python3
import json
from kafka import KafkaConsumer
from kafka import KafkaProducer
from dotenv import load_dotenv
from faker import Faker
from pathlib import Path
import os
import sys

parent_path = Path(__file__).parent.parent
sys.path.append(str(parent_path / 'Logger'))
from Log import Log


load_dotenv(dotenv_path=str(parent_path / '.env'))

logger = Log()
fake = Faker()


KAFKA_HOST_PORT = os.getenv('KAFKA_HOST_PORT', 9092)

logger.info(
    f"Second Topic (add_info) - Making Connection with Consumer - On Port {KAFKA_HOST_PORT}")

consumer = KafkaConsumer(
    'add_info',
    group_id='consumer_services',
    enable_auto_commit=True,
    bootstrap_servers=[f'localhost:{KAFKA_HOST_PORT}'],
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

logger.info('Second Topic (add_info) - Succussfully Connected')

producer = KafkaProducer(
    bootstrap_servers=[f'localhost:{KAFKA_HOST_PORT}'],
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

def add_info(data: dict):
    data['passport'] = fake.passport_number()
    return data

for msg in consumer:
    data = add_info(msg.value)
    producer.send('T3_DB', value=data)
    producer.flush()

    logger.info(
        f'Second Topic (add_info) - id: {data["id"]} - first_name: {data["first_name"]} - Sent to third topic(T3_DB)')
