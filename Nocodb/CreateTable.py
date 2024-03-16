#!/usr/bin/python3
from dotenv import load_dotenv
from pathlib import Path
import os
import sys

root_path = Path(__file__).parent.parent
sys.path.append(str(root_path / 'logger'))
sys.path.append(str(root_path / 'nocodb'))

from log import Log
from Ncdb import Nocodb

load_dotenv(dotenv_path=str(root_path / '.env'))

NC_ADMIN_EMAIL = os.getenv('NC_ADMIN_EMAIL', 'machil@gmail.com')
NC_ADMIN_PASSWORD = os.getenv('NC_ADMIN_PASSWORD', '12345678')


client = Nocodb(NC_ADMIN_EMAIL, NC_ADMIN_PASSWORD)
logger = Log()

try:
    columns = [
        {
            "column_name": "username",
            "title": "username",
            "dt": "varchar(255)"
        },
        {
            "column_name": "email",
            "title": "email",
            "dt": "varchar(255)"
        },
        {
            "column_name": "u_id",
            "title": "u_id",
            "dt": "varchar(255)"
        },
        {
            "column_name": "first_name",
            "title": "first_name",
            "dt": "varchar(128)"
        },
        {
            "column_name": "last_name",
            "title": "last_name",
            "dt": "varchar(128)"
        },
        {
            "column_name": "gender",
            "title": "gender",
            "dt": "varchar(8)"
        },
        {
            "column_name": "address",
            "title": "address",
            "dt": "text"
        },
        {
            "column_name": "post_code",
            "title": "post_code",
            "dt": "varchar(16)"
        },
        {
            "column_name": "dob",
            "title": "dob",
            "dt": "varchar(32)"
        },
        {
            "column_name": "registered_date",
            "title": "registered_date",
            "dt": "varchar(32)"
        },
        {
            "column_name": "phone",
            "title": "phone",
            "dt": "varchar(32)"
        },
        {
            "column_name": "picture",
            "title": "picture",
            "dt": "varchar(255)"
        },
        {
            "column_name": "passport",
            "title": "passport",
            "dt": "varchar(255)"
        }
    ]
    client.create_table('users', columns)
except Exception as e:
    if str(e).find('Duplicate table name') != -1:
        logger.warning(f'{str(e)}')
        exit(0)
    
    logger.critical(f'there was error in table creation -> {str(e)}')
    exit(1)
