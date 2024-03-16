#!/usr/bin/python3
import requests
from dotenv import load_dotenv
from pathlib import Path
import os
import sys
from typing import Optional

root_path = Path(__file__).parent.parent
sys.path.append(str(root_path / 'Logger'))

from Log import Log


load_dotenv(dotenv_path=str(root_path / '.env'))

logger = Log()

NOCODB_HOST_PORT = os.getenv('NOCODB_HOST_PORT', 8080)

class Nocodb:
    def __init__(self, email: Optional[str] = None, password: Optional[str] = None, save_token: Optional[bool] = True, save_info: Optional[bool] = True):
        
        self.base_url = f'http://localhost:{NOCODB_HOST_PORT}'
        self.v1_data_url = self.base_url + '/api/v1/db/data'
        self.v1_meta_url = self.base_url + '/api/v1/db/meta'

        try:
            token = self.load_token(email, password, save_info)
        except ValueError as ve:
            logger.critical(f'there was a error in app ! error: {str(ve)}')
            exit(1)
        
        self._token = token

    def load_token(self, email: Optional[str] = None, password: Optional[str] = None, save_token: Optional[bool] = True, save_info: Optional[bool] = True):
        if None not in [email, password]:
            response = self.sign_in(email, password)
            if response is None:
                logger.critical(f'an unknown error occured! please see logs to')
                exit(1)
            else:
                if 'token' in list(response.json().keys()):
                    token = response.json()['token']
                    if save_info:
                        self.save_info(email, password)
                elif 'msg' in list(response.json().keys()):
                    logger.critical(f'error in validate user - email: {email}, password: {password} - msg: {response.json()["msg"]}')
                    raise ValueError(f'error in validate user - email: {email}, password: {password} - msg: {response.json()["msg"]}')
                else:
                    logger.critical(f'error in validate user - email:{email}, password: {password} - response: {response.text}')
                    raise ValueError(f'error in validate user - email: {email}, password: {password} - msg: {response.text}')
        else:
            token = self.load_token_from_file()
            if token is None:
                logger.critical('there was a error in app ! please see logs')
                raise ValueError(f'error in validate user - email: {email}, password: {password}')
        
        if save_token:
            self.save_token(token)

        return token
    
    def sign_in(self, email: str, password: str):
        try:
            response = requests.post(
                f'{self.base_url}/api/v1/auth/user/signin',
                json={
                    "email": email,
                    "password": password
                }
            )
        except Exception as e:
            logger.critical(f'nocodb - can not sign-in - error: {str(e)}')
        else:
            return response
    
    def validate_token(self, token: str):
        headers = {
            'xc-auth': token
        }
        try:
            response = requests.get(f'{self.base_url}/api/v1/auth/user/me', headers=headers)
        except Exception as e:
            raise e
        # respons.raise_for_status()
        
        if response.status_code == 200:
            if 'id' in list(response.json().keys()):
                return True
            else:
                if response.json()['roles']['guest'] == True:
                    logger.info(f'envalied token - token: {token}')
                
                return False
        else:
            return ConnectionError(f'error in response from server: {self.base_url}/api/v1/auth/user/me - status: {response.status_code}')

    def load_token_from_file(self) -> str:
        try:
            with open(root_path / 'NocoSettings/token.txt', 'r', encoding='utf-8') as f:
                token = f.read().strip()
            
            if self.validate_token(token):
                return token
            else:
                info = self.load_info()
                if info is None:
                    return
                else:
                    response = self.sign_in(info['email'], info['password'])
                    if response is None:
                        logger.critical(f'an unknown error occured! please see logs to')
                        exit(1)
                    else:
                        if 'token' in list(response.json().keys()):
                            return response.json()['token']
                        elif 'msg' in list(response.json().keys()):
                            logger.error(f'error in validate user - email: {info["email"]}, password: {info["password"]} - msg: {response.json()["msg"]}')
                        else:
                            logger.critical(f'error in validate user, load from file mode - email:{info["email"]}, password: {info["password"]} - response: {response.text}')
                            exit(1)

        except ConnectionError as ce:
            logger.critical(f'{str(ce)}')
        except Exception as e:
            logger.info(f'can not load token from file - try to login again...')
            
            info = self.load_info()
            if info is None:
                return
            else:
                response = self.sign_in(info['email'], info['password'])
                if response is None:
                    logger.critical(f'an unknown error occured! please see logs to')
                    exit(1)
                else:
                    if 'token' in list(response.json().keys()):
                        return response.json()['token']
                    elif 'msg' in list(response.json().keys()):
                        logger.error(f'error in validate user - email: {info["email"]}, password: {info["password"]} - msg: {response.json()["msg"]}')
                    else:
                        logger.critical(f'error in validate user, load from file mode - email:{info["email"]}, password: {info["password"]} - response: {response.text}')
                        exit(1)

    def save_token(self, token: str):
        with open(root_path / 'NocoSettings/token.txt', 'w', encoding='utf-8') as f:
            f.write(token)

    def save_info(self, email: str, password: str):
        with open(root_path / 'NocoSettings/email.txt', 'w', encoding='utf-8') as f:
            f.write(email)

        with open(root_path / 'NocoSettings/password.txt', 'w', encoding='utf-8') as f:
            f.write(password)
    
    def load_info(self) -> dict:
        info = {}
        try:
            with open(root_path / 'NocoSettings/email.txt', 'r', encoding='utf-8') as f:
                info['email'] = f.read().strip()

            with open(root_path / 'NocoSettings/password.txt', 'r', encoding='utf-8') as f:
                info['password'] = f.read().strip()
        except Exception as e:
            logger.error(f'{str(e)}')
        else:
            return info
    
    def load_base_id(self):
        try:
            with open(root_path / 'NocoSettings/base_id.txt', 'r', encoding='utf-8') as f:
                base_id = f.read().strip()
            
            self.validate_base_id(base_id)

            return base_id
        except:
            base_id = self.get_base_id()
            if base_id is not None:
                return base_id
            else:
                raise ValueError(f'you should create a base')
    
    def validate_base_id(self, base_id: str):
        try:
            response = requests.get(
                f'{self.v1_meta_url}/projects',
                headers=self.get_headers()
            )
        except Exception as e:
            raise e

        if not response.json()['list'][0]['id'] == base_id:
            raise ValueError(f'base id not found: {base_id}')

    def save_base_id(self, base_id: str):
        with open(root_path / 'NocoSettings/base_id.txt', 'w', encoding='utf-8') as f:
            f.write(base_id)
    
    def get_base_id(self):
        try:
            response = requests.get(
                f'{self.v1_meta_url}/projects',
                headers=self.get_headers()
            )
            if len(response.json()['list']) == 0:
                return
            else:
                self.save_base_id(response.json()['list'][0]['id'])
                return response.json()['list'][0]['id']
        except Exception as e:
            raise e
    
    def get_headers(self):
        try:
            if not self.validate_token(self._token):
                try:
                    token = self.load_token()
                    self._token = token
                except ValueError as ve:
                    logger.critical(f'there was a error in app ! error: {str(ve)}')
                    exit(1)
        
        except ConnectionError as ce:
            logger.critical(f'there was a error in app ! error: {str(ce)}')
            exit(1)

        except Exception as e:
            logger.info(f'{str(e)}')
            try:
                token = self.load_token()
                self._token = token
            except ValueError as ve:
                logger.critical(f'there was a error in app ! error: {str(ve)}')
                exit(1)
        
        return {
            'xc-auth': self._token
        }

    def create_base(self, title: str, save_base_id: Optional[bool] = True):
        try:
            response = requests.get(
                f'{self.v1_meta_url}/projects',
                headers=self.get_headers()
            )
        except Exception as e:
            raise e

        for base_item in response.json()['list']:
            if base_item['title'] == title:
                raise ValueError(f'duplicate title -> {title}')
        
        if len(response.json()['list']) == 0:
            try:
                response = requests.post(
                    f'{self.v1_meta_url}/projects', 
                    json={
                        'title': f'{title}'
                    },
                    headers=self.get_headers()
                )
            except Exception as e:
                logger.error(f'{str(e)}')
                raise e
            else:
                if save_base_id:
                    self.save_base_id(response.json()['id'])
                return response.json()
        else:
            logger.info(f'already you have {len(response.json()["list"])} base and can not create new base')
            raise ValueError(f'already you have {len(response.json()["list"])} base and can not create new base')

    def create_table(self, title: str, columns: dict):
        data = {
            "title": f"{title}",
            "table_name": f"{title}",
            "columns": [
                {
                    "column_name": "id",
                    "title": "Id",
                    "dt": "int4",
                    "dtx": "integer",
                    "ct": "int(11)",
                    "nrqd": 0,
                    "rqd": 1,
                    "ck": 0,
                    "pk": 1,
                    "un": 0,
                    "ai": 1,
                    "cdf": None,
                    "clen": None,
                    "np": 11,
                    "ns": 0,
                    "dtxp": "11",
                    "dtxs": "",
                    "altered": 1,
                    "uidt": "ID",
                    "uip": "",
                    "uicn": ""
                },
                {
                    "column_name": "created_at",
                    "title": "CreatedAt",
                    "dt": "timestamp",
                    "dtx": "specificType",
                    "ct": "timestamp",
                    "nrqd": 1,
                    "rqd": 0,
                    "ck": 0,
                    "pk": 0,
                    "un": 0,
                    "ai": 0,
                    "clen": 45,
                    "np": None,
                    "ns": None,
                    "dtxp": "",
                    "dtxs": "",
                    "altered": 1,
                    "uidt": "CreatedTime",
                    "uip": "",
                    "uicn": "",
                    "system": 1
                },
                {
                    "column_name": "updated_at",
                    "title": "UpdatedAt",
                    "dt": "timestamp",
                    "dtx": "specificType",
                    "ct": "timestamp",
                    "nrqd": 1,
                    "rqd": 0,
                    "ck": 0,
                    "pk": 0,
                    "un": 0,
                    "ai": 0,
                    "clen": 45,
                    "np": None,
                    "ns": None,
                    "dtxp": "",
                    "dtxs": "",
                    "altered": 1,
                    "uidt": "LastModifiedTime",
                    "uip": "",
                    "uicn": "",
                    "system": 1
                }
            ]
        }

        [data['columns'].insert(i + 1, col) for i, col in enumerate(columns)]

        try:
            response = requests.post(
                f'{self.v1_meta_url}/projects/{self.load_base_id()}/tables', 
                json=data,
                headers=self.get_headers()
            )
        except ConnectionError as ce:
            logger.critical(f'connection error - {ce}')
            raise ce

        if response.status_code == 200:
            self.save_table_id(response.json()['id'])
        elif response.status_code == 401:
            logger.error(f'create table error - {response.status_code} - token is envalied or unauthorized - {response.text}')
            raise PermissionError(f'create table error - {response.status_code} - token is envalied or unauthorized - {response.text}')
        else:
            logger.error(response.json()['msg'])
            raise ValueError(f'{response.json()["msg"]}')
    
    def save_table_id(self, table_id: str):
        with open(root_path / 'NocoSettings/table_id.txt', 'w', encoding='utf-8') as f:
            f.write(table_id)
    
    def load_table_id(self, table_name: str):
        table_id = self.load_table_id_from_file(table_name)
        if table_id is None:
            logger.critical(f'can not load table_id - please see logs')
            exit(1)
        else:
            return table_id

    def load_table_id_from_database(self, table_name: str):
        try:
            response = requests.get(
                f'{self.v1_meta_url}/projects/{self.load_base_id()}/tables',
                headers=self.get_headers()
            )

            if response.status_code == 200:
                for table_info in response.json()['list']:
                    if table_info['title'] == table_name:
                        return table_info['id']
        except Exception as e:
            logger.error(f'can not connect to database - get table id frpm database - {str(e)}')
        
        return None

    def validate_table_id(self, table_id: str):
        response = requests.get(
            f'{self.v1_meta_url}/tables/{table_id}',
            headers=self.get_headers()
        )

        if response.status_code == 404:
            return False
        elif response.status_code == 200:
            return True

    def load_table_id_from_file(self, table_name: str):
        try:
            with open(root_path / 'NocoSettings/table_id.txt', 'r', encoding='utf-8') as f:
                table_id = f.read().strip()
            
            if self.validate_table_id(table_id):
                return table_id

        except Exception as e:
            logger.info(f'can not load table_id from file - error: {str(e)} - try to load with connection to database...')
        
        table_id = self.load_table_id_from_database(table_name)
        self.save_table_id(table_id)
        return table_id

    def add_new_row(self, table_name: str, new_row: dict):
        response = requests.post(
            f'{self.v1_data_url}/nc/{self.load_base_id()}/{self.load_table_id(table_name)}',
            json=new_row,
            headers=self.get_headers()
        )

        if response.status_code == 200:
            return response
        elif response.status_code == 400:
            logger.error(f'table not found - name: {table_name} - {response.text}')
            return
        elif response.status_code == 401:
            logger.error(f'unauthorized - {response.text}')

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
    }
]
