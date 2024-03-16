#!/usr/bin/python3
import time
from kafka import KafkaConsumer
from kafka import KafkaProducer
from pathlib import Path
import re
from dotenv import load_dotenv
from pathlib import Path
import os
import sys

parent_path = Path(__file__).parent.parent
sys.path.append(str(parent_path / 'Logger'))
from Log import Log


load_dotenv(dotenv_path=str(parent_path / '.env'))

logger = Log()

KAFKA_TOPICS = os.getenv(
    'KAFKA_TOPICS', 'T1_TS:1:1,T2_LA:1:1,T3_DB:1:1')
KAFKA_HOST_PORT = os.getenv('KAFKA_HOST_PORT', 9092)


def extract_topics(topics: str):
    if re.match(r'^\w+:\d+:\d+(,\w+:\d+:\d+)*$', topics):
        return [topic.split(':')[0] for topic in topics.split(',')]
    else:
        logger.critical(f'topics pattern is not valid ! topics: {topics}')


def connect(topic: str, port: int):
    fail = 0
    try:
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=[f'localhost:{port}'],
        )
        consumer.close()
    except Exception as e:
        logger.warning(
            f'Kafka health - can not connect to consumer - topic: {topic} - port: {port}')
        fail += 1

    try:
        producer = KafkaProducer(
            bootstrap_servers=[f'localhost:{port}']
        )
        producer.close()
    except Exception as e:
        logger.warning(
            f'Kafka health - can not connect to producer - port: {port}')
        fail += 1

    return fail


topics = extract_topics(KAFKA_TOPICS)

for _ in range(5):
    fail_counter = 0

    for topic in topics:
        fail_counter += connect(topic, KAFKA_HOST_PORT)

    if fail_counter == 0:
        exit(0)

    time.sleep(1)

exit(1)
