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
        DROP TABLE IF EXISTS staging.users;
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
        """,
        """
        DROP TABLE IF EXISTS staging.aya_messages;
        CREATE TABLE staging.aya_messages (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT NOT NUll,
            telegram_id BIGINT NOT NULL,
            update_id BIGINT,
            message_text VARCHAR(255) NOT NULL,
            event_name VARCHAR(60),
            timestamp_received TIMESTAMP NOT NULL,
            timestamp_saved TIMESTAMP NOT NULL)
        """,
        """
        INSERT INTO staging.aya_messages (telegram_id, chat_id, update_id, 
            message_text, event_name, timestamp_received, timestamp_saved)
            VALUES  (918237832, 918237832, 123, '/fasten di 12 12', 
                        'fast_start', '2021-01-15 16:24:52', '2021-01-15 16:24:52'),
                    (918237832, 918237832, 126, '/teilnehmen',
                        'fast_end', '2021-01-15 18:24:52', '2021-01-15 18:24:52')
        """,
        """
        CREATE TABLE IF NOT EXISTS prod.aya_messages (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT NOT NUll,
            telegram_id BIGINT NOT NULL,
            update_id BIGINT,
            message_text VARCHAR(255) NOT NULL,
            event_name VARCHAR(60),
            timestamp_received TIMESTAMP NOT NULL,
            timestamp_saved TIMESTAMP NOT NULL)
        """,
        """
        DROP TABLE IF EXISTS staging.group_events;
        CREATE TABLE staging.group_events (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT NOT NUll,
            event_id BIGINT NOT NULL,
            event_name VARCHAR(60) NOT NULL,
            telegram_id BIGINT NOT NULL,
            msg_text VARCHAR(255) NOT NULL,
            status_timestamp TIMESTAMP NOT NULL)
        """,
        """
        INSERT INTO staging.group_events (chat_id, event_id, event_name,
            telegram_id, msg_text, status_timestamp)
            VALUES  (-123456789, 123, 'fast_create', 918237832,
                        '/fasten di 12 12', '2021-01-15 16:24:52'),
                    (-123456789, 126, 'fast_accept', 918237832,
                        '/teilnehmen', '2021-01-15 18:24:52'),
                    (-123456789, 129, 'fast_decline', 918237832,
                        '/ablehnen', '2021-01-15 18:25:52'),
                    (-123456789, 138, 'fast_delete', 918237832,
                        '/loeschen', '2021-01-15 19:24:52')
        """,
        """
        CREATE TABLE IF NOT EXISTS prod.group_events (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT NOT NUll,
            event_id BIGINT NOT NULL,
            event_name VARCHAR(60) NOT NULL,
            telegram_id BIGINT NOT NULL,
            msg_text VARCHAR(255) NOT NULL,
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
