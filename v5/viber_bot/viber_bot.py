from flask import Flask, request, Response
import requests
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages.text_message import TextMessage
from viberbot.api.messages.rich_media_message import RichMediaMessage
from viberbot.api.messages.url_message import URLMessage

from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest

import time
import logging
import sched
import threading
import json
import re


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

app = Flask(__name__)
viber = Api(BotConfiguration(
    name='Автоматичний запуск',
    avatar='http://viber.com/avatar.jpg',
    auth_token='46a517b9f870fcf1-799a9ca308bbd873-7745aee775fec7a7'
))


USERS = [
{'name':'Сергей', 'id': 'cHxBN+Zz1Ldd/60xd62U/w=='}
# {'name':'Сергей', 'id': 'cHxBN+Zz1Ldd/60xd62U/w=='}, 
# {'name':'Сергей', 'id': 'cHxBN+Zz1Ldd/60xd62U/w=='}
]
BACKEND_IP = 'http://127.0.0.1:7542'


def get_response(viber_request):
    text = viber_request.message.text.lower()
    sender_id = viber_request.sender.id
    sender_name = viber_request.sender.name

    if (text == 'тест'):
        # this is not supoprted yet
        # SAMPLE_RICH_MEDIA = '{"ButtonsGroupColumns": 6, "Buttons": [{"ActionType": "open-url", "BgColor": "#000000", "Rows": 4, "ActionBody": "http://www.website.com/go_here", "Columns": 6, "Image": "http://www.images.com/img.jpg", "BgMediaType": "picture", "TextOpacity": 60}, {"ActionType": "open-url", "Text": "Buy", "Rows": 1, "ActionBody": "http://www.website.com/go_here", "Columns": 6, "BgColor": "#85bb65", "TextOpacity": 60}], "BgColor": "#FFFFFF", "ButtonsGroupRows": 2}'
        # SAMPLE_ALT_TEXT = "upgrade now!"
        # return RichMediaMessage(rich_media=json.loads(SAMPLE_RICH_MEDIA), alt_text=SAMPLE_ALT_TEXT, min_api_version=1)
        return [TextMessage(text='Все ок')]

    if ('відмінити' in text):
        res = re.findall(r'\d+', text)
        if not res:
            return [TextMessage(text='Перевірте правильність данних')]

        logger.info("Rule {0} will be canceled".format(res[0]))
        try:
            payload = {'id': res[0], 'sender': sender_name}
            response_status = requests.get(url='http://mozart.hopto.org:7542/cancel_rule', params=payload, timeout=(10, 10))
            response_status.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(e)
            logging.error("Can't cancel rule")
            return [TextMessage(text='Не вдалося відмінити правило. Передіть за посиланням або спробуйте ще раз.')]


@app.route('/', methods=['POST'])
def incoming():
    logger.debug("received request. post data: {0}".format(request.get_data()))
    if not viber.verify_signature(request.get_data(), request.headers.get('X-Viber-Content-Signature')):
            return Response(status=403)

    viber_request = viber.parse_request(request.get_data().decode())

    if (isinstance(viber_request, ViberMessageRequest)):
        message = get_response(viber_request)
        logger.warn("Sending message")
        viber.send_messages(viber_request.sender.id, message)
    elif isinstance(viber_request, ViberSubscribedRequest):
        viber.send_messages(viber_request.get_user.id, [
            TextMessage(text="thanks for subscribing!")
        ])
    elif isinstance(viber_request, ViberFailedRequest):
        logger.warn("client failed receiving message. failure: {0}".format(viber_request))

    return Response(status=200)


@app.route('/notify_users_irrigation_started', methods=['POST'])
def notify_users():
    logger.debug("received request for send_message. post data: {0}".format(request.get_data()))
    data = json.loads(request.get_data().decode())
    users = data['users']
    rule_id = data['rule_id']
    time = data['time']
    timeout = data['timeout']
    user_friendly_name = data['user_friendly_name']

    for user in users:
        logger.info("Sending message to {0}. id: {1}".format(user['name'], user['id']))
        viber.send_messages(user['id'], [
            TextMessage(text='Через {0} хвилин {1} будут поливатися {2}хв.\nНаберіть \'Відмінити {3}\' або перейдіть за посиланням з наступного повідомлення'.format(timeout, user_friendly_name, time, rule_id)),
            URLMessage(media="http://mozart.hopto.org:7542/cancel_rule?id={0}&sender={1}".format(rule_id, user['name']))
        ])

    logger.info("Done")
    return Response(status=200)


@app.route('/notify_users_cancel_rule', methods=['POST'])
def notify_users_cancel_rule():
    logger.debug("received request for send_message. post data: {0}".format(request.get_data()))
    data = json.loads(request.get_data().decode())
    users = data['users']
    user_name = data['user_name']
    branch_name = data['branch_name']

    for user in users:
        logger.info("Sending message to {0}. id: {1}".format(user['name'], user['id']))
        viber.send_messages(user['id'], [
            TextMessage(text='Коричтувач {0} відмінив полив для {1}'.format(user_name, branch_name))
        ])
    logger.info("Done")
    return Response(status=200)


def set_webhook(viber):
    viber.set_webhook('https://mozart.hopto.org:7443/')


if __name__ == "__main__":
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(5, 1, set_webhook, (viber,))
    t = threading.Thread(target=scheduler.run)
    t.start()

    context = ('/var/www/v5/viber_bot/concat.crt', '/var/www/v5/viber_bot/private.key')
    app.run(host='0.0.0.0', port=7443, debug=False, ssl_context=context)
