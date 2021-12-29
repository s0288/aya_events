"""
set up relevant tables
"""
import logging

from utils import db_conn

def create_tables():
    """ create tables"""
    commands = (
        """
        CREATE SCHEMA IF NOT EXISTS prod
        """,
        """
        CREATE SCHEMA IF NOT EXISTS staging
        """,
        """
        DROP TABLE staging.users; 
        CREATE TABLE staging.users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            name VARCHAR(60) NOT NULL,
            status_timestamp TIMESTAMP NOT NULL)
        """,
        """
        INSERT INTO staging.users (telegram_id, name, status_timestamp) 
            VALUES  (459871623, 'tester1', '2021-12-29 16:24:52'),
                    (918237832, 'tester2', '2021-12-29 18:24:52')
        """,
        """
        CREATE TABLE IF NOT EXISTS prod.users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT NOT NULL,
            name VARCHAR(60) NOT NULL,
            status_timestamp TIMESTAMP NOT NULL)
        """
        )
    with db_conn() as conn:
        with conn.cursor() as cur:
            for command in commands:
                cur.execute(command)
                logging.info(f"executed stmt: {command}")


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO)
    create_tables()
