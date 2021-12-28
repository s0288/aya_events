#!/usr/bin/python3.6
# coding: utf8

"""
Maintains aya event listener alive
"""
import time
import logging
import sys

# load .env variables
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from event_listener import EventListener
from event_creator import respond_to_input

def main(chat_id=None):
    # last_update_id is used to make sure that messages are only retrieved once
    next_update_id = None
    logging.info("starting to listen")

    while True:
        try:
            ##### listen for new messages
            update, next_update_id = EventListener.get_update_and_next_update_id(next_update_id)
            logging.info(f"update: {update}")
            if update:
                # extract incoming message
                chat_id, message, message_id, user_id, original_message = EventListener.extract_main(update)
                logging.info(f"user message: {message}")

                if not all((chat_id, message)):
                    # if a user provides input that is not expected (e.g. adding a user to a chat), ignore these inputs for now
                    # better solution is to set a default "I don't know what this means" response and send it to Rasa
                    continue

                respond_to_input(chat_id, message, message_id, user_id, original_message)
                logging.info(f"responded to input")
        except Exception as e:
            logging.exception(e)

        time.sleep(0.5)
        sys.stdout.write('.'); sys.stdout.flush()

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=logging.INFO) # filename='aya.log'
    EventListener = EventListener()
    main()
