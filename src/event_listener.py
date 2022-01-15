"""

EventListener listens for incoming messages

"""

import os
import json
import logging
import requests

URL = f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_TOKEN')}/"

class EventListener:
    """
    class that listens for incoming msgs
    """
    def get_update_and_next_update_id(self, offset=None):
        """
            Retrieve incoming msgs.

            Telegram saves all incoming msgs into an update json that looks like this:
                {
                    'update_id': 670804824, 'message': {
                        'message_id': 10,
                        'from': {'id': 415604082, 'is_bot': False,
                            'first_name': 'Alex', 'language_code': 'fr'},
                        'chat': {'id': -1001284682229, 'title': 'Aya - Fasten-Events',
                            'type': 'supergroup'},
                        'date': 1617995834,
                        'text': '/fasten',
                        'entities': [{'offset': 0, 'length': 7, 'type': 'bot_command'}]
                    }
                }

            It is possible that Telegram does not update the
            result json before polling occurs again.
            To prevent retrieving the same msg twice,
            ignore the already retrieved update_ids with next_update_id.

            :param offset:                  int     (ignore all update_ids
                                                        until the requested offset)
            :return:        js              json    (json that contains incoming msgs)
                            next_update_id  int     (min(update_id)+1 in json)
        """
        url = URL + "getUpdates?timeout=600"
        if offset:
            url += f"&offset={offset}"

        js_load = EventListener._get_updates_from_telegram_or_answer_callback(url)
        update, next_update_id = EventListener._get_update_and_next_update_id(js_load)

        return update, next_update_id

    @staticmethod
    def _get_updates_from_telegram_or_answer_callback(url):
        response = requests.get(url)
        content = response.content.decode("utf8")
        js_load = json.loads(content)
        return js_load

    @staticmethod
    def _get_update_and_next_update_id(js_load):
        """
        EventListener processes one message per call.
        Therefore, it is not necessary to load all available updates,
        since only the oldest update will be processed in the call.
        """
        if js_load.get("result"):
            update_id = min([row["update_id"] for row in js_load["result"]])
            update = [row for row in js_load["result"] if row["update_id"] == update_id][0]
            return update, update_id+1
        return None, None

    def extract_main(self, update):
        """extract main"""
        extraction_method = EventListener._set_extraction_method(update)
        if extraction_method == 'do_not_extract':
            return None, None, None, None, None
        if extraction_method == 'extract_message':
            chat_id, message_text, message_id, \
                user_id = EventListener._extract_message(update['message'])
            original_message = None
        elif extraction_method == 'extract_callback':
            EventListener._answer_callback(update['callback_query']['id'])
            chat_id, message_text, message_id, \
                user_id, original_message = EventListener._extract_callback(update)
        return chat_id, message_text, message_id, user_id, original_message

    @staticmethod
    def _set_extraction_method(update):
        """
        these extraction methods exist: [message, callback, not-to-be-extracted content]
        """
        if update.get('message'):
            if any(
                update["message"].get(key) for key in
                    ['group_chat_created', 'new_chat_participant', 'left_chat_participant']
                ):
                # ignore out-of-the-ordinary actions
                logging.info("received a do_not_extract_event")
                return 'do_not_extract'
            return 'extract_message'
        elif update.get('callback_query') is not None:
            return 'extract_callback'
        return 'do_not_extract'

    @staticmethod
    def _extract_message(update_message):
        chat_id = update_message["chat"]["id"]
        message_id = update_message["message_id"]
        user_id = update_message["from"]["id"]
        message_text = None

        if update_message.get('text'):
            message_text = update_message["text"]
        elif update_message.get('document'): # e.g. pdf
            message_text = 'file: ' + update_message["document"]["file_id"]
        elif update_message.get('photo'): # e.g. jpg
            try:
                message_text = 'file: ' + update_message["photo"][3]["file_id"]
            except:
                message_text = 'file: ' + update_message["photo"][0]["file_id"]
        return chat_id, message_text, message_id, user_id

    @staticmethod
    def _extract_callback(update):
        chat_id = update['callback_query']["message"]["chat"]["id"]
        message_text = update['callback_query']["data"]
        message_id = update['callback_query']["message"]["message_id"]
        user_id = update['callback_query']["from"]["id"]
        original_message = update['callback_query']["message"]["text"]
        return chat_id, message_text, message_id, user_id, original_message

    @staticmethod
    def _answer_callback(callback_query_id):
        """
        answering a callback is necessary to
        unfreeze the user's telegram chat (e.g. for inline buttons)
        """
        url = URL + f"answerCallbackQuery?callback_query_id={callback_query_id}"
        EventListener._get_updates_from_telegram_or_answer_callback(url)
