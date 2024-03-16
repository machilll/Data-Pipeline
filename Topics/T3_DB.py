import json
import psycopg2
from kafka import KafkaConsumer
from urllib.parse import urlparse
from dotenv import load_dotenv
from pathlib import Path
import os
import sys

parent_path = Path(__file__).parent.parent
sys.path.append(str(parent_path / 'logger'))
from Ncdb import Nocodb
from log import Log


load_dotenv(dotenv_path=str(parent_path / '.env'))

logger = Log()

KAFKA_HOST_PORT = os.getenv('KAFKA_HOST_PORT', 9092)
NC_ADMIN_EMAIL = os.getenv('NC_ADMIN_EMAIL', 'machil@gmail.com')
NC_ADMIN_PASSWORD = os.getenv('NC_ADMIN_PASSWORD', '12345678')

try:
    client = Nocodb()
except Exception as e:
    logger.error(f'can not connect to nocodb without any argument - {str(e)}')
    try:
        client = Nocodb(NC_ADMIN_EMAIL, NC_ADMIN_PASSWORD)
    except Exception as e:
        logger.critical(f'can not connect to nocodb with arguments - email: {NC_ADMIN_EMAIL} - password: {NC_ADMIN_PASSWORD} - error: {str(e)}')
        exit(1)

cursor = None
connection = None

logger.info(
    f"Third Topic (T3_DB) - Making Connection with Consumer - On Port {KAFKA_HOST_PORT}")

consumer = KafkaConsumer(
    'T3_DB',
    group_id='consumer_services',
    enable_auto_commit=True,
    bootstrap_servers=[f'localhost:{KAFKA_HOST_PORT}'],
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

logger.info('Third Topic (T3_DB) - Succussfully Connected')


def connect_to_database():
    global cursor
    global connection

    try:
        connection.close()
    except:
        pass

    URI = os.getenv('URI')

    if URI is not None:
        result = urlparse(URI)
        DATABASE_NAME = result.path[1:]
        DATABASE_HOST = result.hostname
        DATABASE_USER = result.username
        DATABASE_PASSWORD = result.password
        DATABASE_PORT = result.port

        if None in [DATABASE_NAME, DATABASE_HOST, DATABASE_USER, DATABASE_PASSWORD, DATABASE_PORT]:
            logger.critical('Can\'t load environment variables - URI mode')
            raise ImportError('Can\'t load environment variables - URI mode')

        DATABASE_SCHEMA = os.getenv('DATABASE_SCHEMA', 'mahsa')

        try:
            if DATABASE_SCHEMA is not None:
                connection = psycopg2.connect(
                    database=DATABASE_NAME,
                    host=DATABASE_HOST,
                    user=DATABASE_USER,
                    password=DATABASE_PASSWORD,
                    port=DATABASE_PORT,
                    options=f'-c search_path={DATABASE_SCHEMA}'
                )
            else:
                connection = psycopg2.connect(
                    database=DATABASE_NAME,
                    host=DATABASE_HOST,
                    user=DATABASE_USER,
                    password=DATABASE_PASSWORD,
                    port=DATABASE_PORT
                )
        except Exception as e:
            logger.critical(str(e))
            exit(1)

        if connection is None:
            logger.critical('can\'t connect to database')
            exit(1)

        cursor = connection.cursor()

    else:
        DATABASE_NAME = os.getenv('DATABASE_NAME', 'postgres')
        DATABASE_HOST = os.getenv('DATABASE_HOST', 'localhost')
        DATABASE_USER = os.getenv('DATABASE_USER', 'mahsa')
        DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', 'mahsa')
        DATABASE_PORT = os.getenv('DATABASE_PORT', 13742)

        if None in [DATABASE_NAME, DATABASE_HOST, DATABASE_USER, DATABASE_PASSWORD, DATABASE_PORT]:
            logger.critical('Can\'t load environment variables')
            raise ImportError('Can\'t load environment variables')

        DATABASE_SCHEMA = os.getenv('DATABASE_SCHEMA', 'mahsa')

        try:
            if DATABASE_SCHEMA is not None:
                connection = psycopg2.connect(
                    database=DATABASE_NAME,
                    host=DATABASE_HOST,
                    user=DATABASE_USER,
                    password=DATABASE_PASSWORD,
                    port=DATABASE_PORT,
                    options=f'-c search_path={DATABASE_SCHEMA}'
                )
            else:
                connection = psycopg2.connect(
                    database=DATABASE_NAME,
                    host=DATABASE_HOST,
                    user=DATABASE_USER,
                    password=DATABASE_PASSWORD,
                    port=DATABASE_PORT
                )
        except Exception as e:
            logger.critical(f'database error, {str(e)}')
            exit(1)

        if connection is None:
            logger.critical('can\'t connect to database')
            exit(1)

        cursor = connection.cursor()


def add_to_database(data):
    for _ in range(5):
        try:
            cursor.execute(f'''
                INSERT INTO users  AS u (username, email, id, first_name, last_name, gender, address, post_code, dob, registered_date, phone, picture)
                VALUES ('{data['username']}', '{data['email']}', '{data['id']}', '{data['first_name']}', '{data['last_name']}', '{data['gender']}', '{data['address']}', '{data['post_code']}', '{data['dob']}', '{data['registered_date']}', '{data['phone']}', '{data['picture']}', '{data['passport']}');
            ''')
            connection.commit()
            break
        except psycopg2.InterfaceError as e:
            connect_to_database()
        except psycopg2.OperationalError as e:
            connect_to_database()
        except psycopg2.errors.UniqueViolation as e:
            connection.reset()
            logger.warning(
                f'user already exists, id: {data["id"]} - username: {data["username"]}')
        except psycopg2.errors.InvalidTextRepresentation as e:
            logger.error(
                f"Bad query ! - insert new user section - values ('{data['username']}', '{data['email']}', '{data['id']}', '{data['first_name']}', '{data['last_name']}', '{data['gender']}', '{data['address']}', '{data['post_code']}', '{data['dob']}', '{data['registered_date']}', '{data['phone']}', '{data['picture']}', '{data['passport']})")
            connect_to_database()
            return
        except Exception as e:
            logger.error(f'{e}')
            connect_to_database()


    else:
        logger.error('can\'t connect to database, database is down')

    logger.info(
        f'new user added into postgres database, id: {data["id"]} - username: {data["username"]}')

def add_to_nocodb(table_name: str, new_row: dict):
    new_row['u_id'] = new_row.pop('id')
    client.add_new_row(table_name, new_row)

connect_to_database()

for message in consumer:
    logger.info(
        f"Partition:{message.partition}\tOffset:{message.offset}\tKey:{message.key}\tValue:{message.value}")

    try:
        add_to_database(message.value)
    except Exception as e:
        logger.error(f'{e}')
        connect_to_database()
        
    try:
        add_to_nocodb('users', message.value)
    except Exception as e:
        logger.error(f'{e}')

