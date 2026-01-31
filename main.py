import sys
import re
import json
from pathlib import Path
import requests
from pydantic import BaseModel, Field

import zulip

from zulip_client import ZulipClient
from logger import create_logger
from config import settings
import helpers

logger = create_logger(logger_name=__name__)

zulip = ZulipClient()
zulip_client = zulip.client  # todo - исправить
"""   !!!! Важно
Пользователь, от лица которого создается клиент, 
(прописан в переменных окружения ZULIP_API_KEY, ZULIP_EMAIL)
д.б. подписан на каналы, сообщения в которых нужно перехватывать.
=> Пользователь ТГБот д.б. подписан на все каналы.  
"""
# todo Пользователь ТГБот д.б. подписан на все каналы.
# todo все сотрудники ТехОтдела д.б. подписаны на все каналы.

# {'id': 86, 'sender_id': 8, 'content': 'проблема 7', 'recipient_id': 20, 'timestamp': 1744282058, 'client': 'ZulipPython',
# 'subject': 'от бота', 'topic_links': [], 'is_me_message': False, 'reactions': [], 'submessages': [], 'sender_full_name': 'Александр Ермолаев',
# 'sender_email': 'alex@kik-soft.ru', 'sender_realm_str': '', 'display_recipient': '79219376763_542393918', 'type': 'stream', 'stream_id': 12,
# 'avatar_url': None, 'content_type': 'text/x-markdown'}
# {'ok': True, 'result': {'message_id': 480, 'from': {'id': 7586848030, 'is_bot': True, 'first_name': 'kik-test-bot', 'username': 'kik_soft_supp_bot'},
# 'chat': {'id': 542393918, 'first_name': 'Александр', 'type': 'private'}, 'date': 1744282059, 'text': 'проблема 7'}}

class Message(BaseModel):
    sender_full_name: str
    content: str
    client: str  # 'ZulipPython' - от бота,  'website' - боту
    subject: str  # топик
    channel_id:  int = Field(alias='stream_id')   # channel_id

    def from_zulip(self):
        return self.client in ("website", "ZulipMobile")

    def get_topic_owner_tg_id(self):
        try:
            _, tg_id = tuple(self.subject.split("_"))
            if (tg_id.isdigit() and int(tg_id) > 0):
                return tg_id
        except ValueError:
            msg_text = f"Не удалось извлеч TG_ID из строки {subject}"
            logger.error(msg_text)
            send_msg_to_bot(settings.ADMIN_ID, msg_text)

        return None

    def get_clean_msg_text(self):
        # чистим тект сообщения

        # редактируем цитирование
        clean_text = helpers.clean_quote(self.content)

        return clean_text


"""
'[Снимок экрана от 2025-07-10 17-48-37.png](/user_uploads/2/4c/vQfELySoD1xFWvxK7lPBz6Yv/2025-07-10-17-48-37.png)  \nи еще и еще'
из этой строки выделяем 1)имя файла - все что в скобках 2)остальной текст 
"""
def uploaded_file_name(msg_text: str) -> str:
    pattern = r'[^(]+(\(\/.+\))'

    logger.info(f"***msg_text='{msg_text}'")
    matches = re.match(pattern, msg_text)
    if matches:
        file_name = matches.group(1)[1:-1]
        logger.info(f"***file_name='{file_name}'")
        return file_name
    else:
        return ''

def description_text(msg_text: str) -> str:
    pattern = r'(\(\/.+\))'
    substr = re.sub(pattern, '', msg_text)
    return substr


def send_photo_to_tg(user_tg_id: int, file_name: str) -> bool:
    token = settings.BOT_TOKEN
    chat_id = str(user_tg_id)

    file_path = Path(file_name)
    if not file_path.is_file():
        logger.error(f"Не найден файл по пути '{file_name}'")
        return False

    try:
        with open(file_name, 'rb') as file:
            files = {'photo': file}
            url = f"https://api.telegram.org/bot{token}/sendPhoto"
            data = {'chat_id' : chat_id}
            result = requests.post(url, files=files, data=data)

            if result.status_code == 200:
                return True

    except Exception as e:
        logger.error(f"Не удалось отправить в ТГ файл '{file_name}': {e}")

    return False


def send_text_to_tg(user_tg_id, msg_text):
    # # https://api.telegram.org/bot<Bot_token>/sendMessage?chat_id=<chat_id>&text=Привет%20мир
    token = settings.BOT_TOKEN
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={user_tg_id}&text={msg_text}"
    result = requests.get(url)



def send_msg_to_bot(message: Message):
    user_tg_id = message.get_topic_owner_tg_id()
    clean_text = message.get_clean_msg_text()
    msg_text = f"{message.sender_full_name}: {clean_text}"

    if '/user_uploads/' in msg_text:  # отправляется файл
        # zulip file url: /user_uploads/2/de/SYE4TXtSd6kfPWW0L6pD_6RS/.png
        # local uploads dir: /home/zulip/uploads/files/2/c1/w7Rl...
        file_name = uploaded_file_name(clean_text)
        # file_name = file_name.replace("/user_uploads/", "")
        # file_name = f"/home/zulip/uploads/files/{file_name}"

        msg_text = f"{message.sender_full_name}: {description_text(clean_text)}"

        logger.info(f"Отправляется фото из файла {file_name}, описание: {msg_text}")
        if not send_photo_to_tg(user_tg_id, file_name):
            msg_text += "\nТут должна была быть картинка, но увы ..."

    send_text_to_tg(user_tg_id, msg_text)


def on_message(msg: dict):
    message = Message.model_validate(msg)
    logger.info(msg)

    if message.from_zulip():
        # user_phone = extract_phone_from_subject(subject)
        # user = Profile.objects.get(phone=user_phone)

        user_tg_id = message.get_topic_owner_tg_id()
        if not user_tg_id:
            return

        msg_content = message.get_clean_msg_text()
        if user_tg_id == settings.ADMIN_TG_ID and '///' in msg_content:  # какая-то админская команда
            zulip.send_msg_to_channel(
                channel_name="bot_events",
                topic="ответы на команды",
                msg=f"Получена команда: {cmd}",
            )
            return

        send_msg_to_bot(message)

zulip_client.call_on_each_message(on_message)



# от ТгБота
# {'id': 86, 'sender_id': 8, 'content': 'проблема 7', 'recipient_id': 20, 'timestamp': 1744282058, 'client': 'ZulipPython',
# 'subject': 'от бота', 'topic_links': [], 'is_me_message': False, 'reactions': [], 'submessages': [], 'sender_full_name': 'Александр Ермолаев',
# 'sender_email': 'alex@kik-soft.ru', 'sender_realm_str': '', 'display_recipient': '79219376763_542393918', 'type': 'stream', 'stream_id': 12,
# 'avatar_url': None, 'content_type': 'text/x-markdown'}
# {'ok': True, 'result': {'message_id': 480, 'from': {'id': 7586848030, 'is_bot': True, 'first_name': 'kik-test-bot', 'username': 'kik_soft_supp_bot'},
# 'chat': {'id': 542393918, 'first_name': 'Александр', 'type': 'private'}, 'date': 1744282059, 'text': 'проблема 7'}}

# от Zulip
#{'id': 371, 'sender_id': 8, 'content': 'ping', 'recipient_id': 32, 'timestamp': 1750539450, 'client': 'website',
# 'subject': 'Александр_542393918', 'topic_links': [], 'is_me_message': False, 'reactions': [], 'submessages': [],
# 'sender_full_name': 'Александр Ермолаев', 'sender_email': 'alex@kik-soft.ru', 'sender_realm_str': '',
# 'display_recipient': 'КиК-софт (тестовый)', 'type': 'stream', 'stream_id': 20, 'avatar_url': None, 'content_type': 'text/x-markdown'}
#
# {'ok': True, 'result': {'message_id': 481, 'from': {'id': 7586848030, 'is_bot': True, 'first_name': 'kik-test-bot', 'username': 'kik_soft_supp_bot'},
# 'chat': {'id': 542393918, 'first_name': 'Александр', 'type': 'private'}, 'date': 1744282106, 'text': 'решение 6'}}

# от Zulip с картинкой
# {'id': 835, 'sender_id': 8,
# 'content': '[Снимок экрана от 2025-04-04 23-08-25.png](/user_uploads/2/c6/IF2RKikfklKeiJ9kSDMcBlWs/2025-04-04-23-08-25.png)',
# 'recipient_id': 13, 'timestamp': 1755448700, 'client': 'website', 'subject': 'Александр_542393918', 'topic_links': [],
# 'is_me_message': False, 'reactions': [], 'submessages': [], 'sender_full_name': 'Александр', 'sender_email': 'alex@kik-soft.ru',
# 'sender_realm_str': '', 'display_recipient': 'КиК-софт', 'type': 'stream', 'stream_id': 4, 'avatar_url': None,
# 'content_type': 'text/x-markdown'}

# картинка  'content': '[Снимок экрана от 2025-07-10 17-48-37.png](/user_uploads/2/4c/vQfELySoD1xFWvxK7lPBz6Yv/2025-07-10-17-48-37.png)  и еще текст\nи еще текст'
