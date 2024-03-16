#!/usr/bin/python3
from dotenv import load_dotenv
from pathlib import Path
import os
import sys

root_path = Path(__file__).parent.parent
sys.path.append(str(root_path / 'Logger'))
sys.path.append(str(root_path / 'Nocodb'))

from Log import Log
from Ncdb import Nocodb

load_dotenv(dotenv_path=str(root_path / '.env'))

NC_ADMIN_EMAIL = os.getenv('NC_ADMIN_EMAIL', 'machil@gmail.com')
NC_ADMIN_PASSWORD = os.getenv('NC_ADMIN_PASSWORD', '12345678')


logger = Log()
client = Nocodb(NC_ADMIN_EMAIL, NC_ADMIN_PASSWORD)

try:
    client.create_base('Base-00')
except ValueError as ve:
    logger.warning(f'{str(ve)}')
    exit(0)
except Exception as e:
    logger.critical(f'error in creating base for nocodb - {str(e)}')
    exit(1)
