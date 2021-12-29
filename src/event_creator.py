"""
Respond to inputs 
"""
import os
import urllib
import datetime
import json
import re
import requests

from utils import db_conn

URL = f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_TOKEN')}/"
WEEK_ABBR_DICT = {"mo": "montag", "di": "dienstag", "mi": "mittwoch", "do": "donnerstag", \
    "fr": "freitag", "sa": "samstag", "so": "sonntag"}
WEEK_INT_DICT = {"montag": 0, "dienstag": 1, "mittwoch": 2, "donnerstag": 3, "freitag": 4, \
    "samstag": 5, "sonntag": 6}

def _load_users():
    """get the most recent telegram_id-name combination for each telegram_id"""
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                select u.telegram_id, u.name 
                from {os.environ.get('DB_PROD_LEVEL')}.users u
                join (
                        select telegram_id, max(status_timestamp) as max_timestamp 
                        from {os.environ.get('DB_PROD_LEVEL')}.users group by telegram_id
                    ) s
                on u.telegram_id = s.telegram_id and u.status_timestamp = s.max_timestamp
                ;""")
            df = cur.fetchall()
    return {row[0]: row[1] for row in df}
USER_DICT = _load_users()


def respond_to_input(chat_id, message, message_id, telegram_id, original_message):
    def _get_rules():
        response = "Hallo 🙂. Diese Gruppe dient zum Vereinbaren von Fastensitzungen.\n\n"
        response += "Beachte hierfür bitte folgende Regeln:\n\n"
        response += "- 1.) Gib einen Namen ein, um dich zu registrieren\n"
        response += "(oder um deinen Namen zu ändern):\n\n"
        response += "/name [dein Name]\n"
        response += "Beispiel: /name alex\n\n"
        response += "- 2.) Du kannst eine Fastengruppe erstellen, indem du Folgendes eingibst "
        response += "(Wichtig 1: Vermeide Kommas oder Wörter wie 'Uhr', 'Stunden', ...)\n"
        response += "(Wichtig 2: Du kannst nur für die laufende Woche eine Fastensitzung einstellen):\n\n"
        response += "/fasten [Wochentag] [Startuhrzeit] [Länge des Fastens]\n"
        response += "Beispiel 1: /fasten Dienstag 17:00 36\n"
        response += "Beispiel 2: /fasten di 17 36\n\n"
        response += "- 3.) Du nimmst an einer Fastengruppe teil, indem du auf 'Dabei' klickst.\n"
        response += "Indem du 'Nicht dabei' klickst, entfernst du dich wieder von der Gruppe."
        return response
    first_word = message.split(' ')[0].lower()
    if first_word == '/name':
        name = message.split(' ')[1]
        if name in USER_DICT.values():
            response = f"Name bereits vergeben. Bitte wähle einen anderen mit /name [dein Name]"
        else:
            response = f"Willkommen, {name}"
            USER_DICT[telegram_id] = name
            _write_user_to_db(telegram_id, name)
        _delete_message_from_telegram(chat_id, message_id)
        _send_message_to_event_telegram(chat_id, response, _create_del_msg_keyboard())
    elif '/regeln' in first_word:
        response = _get_rules()
        _delete_message_from_telegram(chat_id, message_id)
        _send_message_to_event_telegram(chat_id, response, _create_del_msg_keyboard())
    elif USER_DICT.get(telegram_id): # check if the user set a name yet
        if first_word == '/fasten':
            response = _extract_fasten_elements(telegram_id, message)
            _delete_message_from_telegram(chat_id, message_id)
            keyboard = _create_fast_event_keyboard()
            _send_message_to_event_telegram(chat_id, response, keyboard)
        elif first_word == '/teilnehmen':
            keyboard = _create_fast_event_keyboard()
            _add_participant(chat_id, message_id, USER_DICT.get(telegram_id), original_message, keyboard)
        elif first_word == '/absagen':
            keyboard = _create_fast_event_keyboard()
            _remove_participant(chat_id, message_id, USER_DICT.get(telegram_id), original_message, keyboard)
        elif first_word == '/loeschen':
            _delete_message_from_telegram(chat_id, message_id)
        else:
            response = "Bitte schreibe Nachrichten gemäß der Regeln. Deine Nachricht wurde gelöscht.\n\n"
            response += "Um die Regeln anzuzeigen, gib /regeln ein."
            _delete_message_from_telegram(chat_id, message_id)
            _send_message_to_event_telegram(chat_id, response, _create_del_msg_keyboard())
    else: # if the user sends a msg without having set a name, tell him to create a name first.
        response = "Bitte erstelle zuerst einen Namen, indem du '/name [dein Name]' schreibst.\n\n"
        response += "Beispiel:\n"
        response += "/name alex\n\n"
        response += "Unsere Regeln findest du unter /regeln."
        _send_message_to_event_telegram(chat_id, response, _create_del_msg_keyboard())

def _send_message_to_event_telegram(chat_id, message_text, inline_keyboard=None):
    parsed_message = urllib.parse.quote_plus(message_text)
    url = URL + f"sendMessage?text={parsed_message}&chat_id={chat_id}"
    url += "&parse_mode=HTML&disable_web_page_preview=true"
    if inline_keyboard:
        url += f"&reply_markup={inline_keyboard}"
    else:
        # remove keyboard from the background
        url += "&reply_markup={\"remove_keyboard\":%20true}"
    requests.get(url) # post msg to Telegram server

def _delete_message_from_telegram(chat_id, message_id):
    url = URL + f"deleteMessage?chat_id={chat_id}&message_id={message_id}"
    requests.get(url) # post msg to Telegram server

def _extract_fasten_elements(telegram_id, message):
    convert_tag = lambda x : WEEK_ABBR_DICT[f"{x}"] if len(x) == 2 else x
    start_tag = convert_tag(message.split(' ')[1].lower())
    start_date = _calculate_date(start_tag)
    start_zeit = message.split(' ')[2]
    ziel = message.split(' ')[3]

    response = 'Fasten-Gruppe:\n'
    response += f"- Start: {start_tag.capitalize()}, {start_date}, {start_zeit} Uhr\n"
    response += f"- Ziel: {ziel} Stunden\n"
    response += f"- Teilnehmer: {USER_DICT.get(telegram_id)}"
    return response

def _calculate_date(start_tag):
    target_weekday_number = WEEK_INT_DICT[f"{start_tag}"]
    today_weekday_number = datetime.datetime.today().weekday()
    # if target day of week is smaller than current day of week, then move to next week
    if target_weekday_number < today_weekday_number:
        days_from_today = 7 - today_weekday_number + target_weekday_number
    else:
        days_from_today = target_weekday_number - today_weekday_number
    return (datetime.datetime.today() + datetime.timedelta(days_from_today)).strftime("%d.%m.%y")

def _create_fast_event_keyboard():
    """
    'buttons': [{'payload': 'ja', 'title': 'ja'}, {'payload': 'nein', 'title': 'nein'}]
    create correct format for inline_keyboard 
        e.g.: {"inline_keyboard":[[{"text": "Hello", "callback_url": "Hello", "url": "", "callback_data": "Hello"},
                {"text": "No", "callback_url": "Google", "url": "http://www.google.com/"}]]}
    """
    keyboard = [{"text": "Dabei", "callback_url": "/teilnehmen", "url": "", "callback_data": "/teilnehmen"},
                {"text": "Nicht dabei", "callback_url": "/absagen", "url": "", "callback_data": "/absagen"},
                {"text": "Löschen", "callback_url": "/loeschen", "url": "", "callback_data": "/loeschen"}]
    inline_keyboard = {"inline_keyboard": [keyboard]} # required format for Telegram
    return json.dumps(inline_keyboard)

def _create_del_msg_keyboard():
    """
    'buttons': [{'payload': 'ja', 'title': 'ja'}, {'payload': 'nein', 'title': 'nein'}]
    create correct format for inline_keyboard 
        e.g.: {"inline_keyboard":[[{"text": "Hello", "callback_url": "Hello", "url": "", "callback_data": "Hello"},
                {"text": "No", "callback_url": "Google", "url": "http://www.google.com/"}]]}
    """
    keyboard = [{"text": "Löschen", "callback_url": "/loeschen", "url": "", "callback_data": "/loeschen"}]
    inline_keyboard = {"inline_keyboard": [keyboard]} # required format for Telegram
    return json.dumps(inline_keyboard)


def _add_participant(chat_id, message_id, name, original_message, inline_keyboard):
    """
    Edit original message to add new fasting participant.
    """
    original_message += f", {name}" # simple adding of participant
    parsed_message = urllib.parse.quote_plus(original_message)
    url = URL + f"editMessageText?chat_id={chat_id}&message_id={message_id}&text={parsed_message}"
    url += "&parse_mode=HTML&disable_web_page_preview=true"
    url += f"&reply_markup={inline_keyboard}"
    requests.get(url) # post msg to Telegram server

def _remove_participant(chat_id, message_id, name, original_message, inline_keyboard):
    """
    Edit original message to add new fasting participant.
    """
    message_wo_participants, participants = original_message.split('- Teilnehmer:') 
    parsed_message = urllib.parse.quote_plus(
            message_wo_participants + '- Teilnehmer:' + re.sub(name, "", participants)
        )
    url = URL + f"editMessageText?chat_id={chat_id}&message_id={message_id}&text={parsed_message}"
    url += "&parse_mode=HTML&disable_web_page_preview=true"
    url += f"&reply_markup={inline_keyboard}"
    requests.get(url) # post msg to Telegram server

def _write_user_to_db(telegram_id, name):
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO {os.environ.get('DB_PROD_LEVEL')}.users 
                    (telegram_id, name, status_timestamp) 
                VALUES  
                    ({telegram_id}, '{name}', '{datetime.datetime.now()}')
                """)
