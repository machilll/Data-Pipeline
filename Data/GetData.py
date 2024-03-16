#!/usr/bin/python3
from log import Log
import uuid
import json
import requests
from kafka import KafkaProducer
from dotenv import load_dotenv
from pathlib import Path
import os
import sys

parent_path = Path(__file__).parent.parent
sys.path.append(str(parent_path / 'logger'))


load_dotenv(dotenv_path=str(parent_path / '.env'))

logger = Log()

KAFKA_HOST_PORT = os.getenv('KAFKA_HOST_PORT', 9092)

producer = KafkaProducer(
    bootstrap_servers=[f'localhost:{KAFKA_HOST_PORT}'],
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)


def get_data():
    res = requests.get("https://randomuser.me/api/")
    res = res.json()
    res = res['results'][0]

    return res


def format_data(res):
    data = {}
    location = res['location']
    data['id'] = str(uuid.uuid4())
    data['first_name'] = res['name']['first']
    data['last_name'] = res['name']['last']
    data['gender'] = res['gender']
    data['address'] = f"{str(location['street']['number'])} {location['street']['name']}, " \
                      f"{location['city']}, {location['state']}, {location['country']}"
    data['post_code'] = location['postcode']
    data['email'] = res['email']
    data['username'] = res['login']['username']
    data['dob'] = res['dob']['date']
    data['registered_date'] = res['registered']['date']
    data['phone'] = res['phone']
    data['picture'] = res['picture']['medium']

    return data


def stream_data():
    global producer
    try:
        res = get_data()
        res = format_data(res)

        producer.send('T1_TS', value=res)
        producer.flush()
        producer.close()

        logger.info(
            f'Kafka: id: {res["id"]} - username: {res["username"]} - sent to pipeline')

    except Exception as e:
        logger.error(f'An error occured: {e}')


if __name__ == "__main__":
    stream_data()
