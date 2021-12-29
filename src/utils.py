from urllib.parse import urlparse
import os
import psycopg2
# load .env variables
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

DB = os.environ.get('DB')
RESULT = urlparse(DB)
USERNAME = RESULT.username 
PASSWORD = RESULT.password
DATABASE = RESULT.path[1:]
HOSTNAME = RESULT.hostname
PORT = RESULT.port

def db_conn():
    conn = psycopg2.connect(
            database=DATABASE,
            user=USERNAME,
            password=PASSWORD,
            host=HOSTNAME,
            port=PORT
        )
    return conn
