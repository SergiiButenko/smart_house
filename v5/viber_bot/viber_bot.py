from flask import Flask, request, Response
import requests
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages.text_message import TextMessage
from viberbot.api.messages.rich_media_message import RichMediaMessage
from viberbot.api.messages.keyboard_message import KeyboardMessage

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
    {'name': 'Sergii', 'id': 'cHxBN+Zz1Ldd/60xd62U/w=='},
    {'name': 'Oleg', 'id': 'IRYaSCRnmV1IT1ddtB8Bdw=='},
    {'name': 'Irina', 'id': 'mSR74mGibK+ETvTTx2VvcQ=='}
]

BACKEND_IP = 'http://127.0.0.1:7542'


def check_user_is_valid(user_id):
    for user in USERS:
        if (user_id == user['id']):
            return True

    return False


def send_response(viber_request):
    text = viber_request.message.text.lower().strip()
    sender_id = viber_request.sender.id
    sender_name = viber_request.sender.name

    if (check_user_is_valid(sender_id) is False):
        logger.warn('User is not registered in system or this is bot')
        return

    if (text == 'тест' or text == 'test'):
        # this is not supoprted yet
        # SAMPLE_RICH_MEDIA = '{"ButtonsGroupColumns": 6, "Buttons": [{"ActionType": "open-url", "BgColor": "#000000", "Rows": 4, "ActionBody": "http://www.website.com/go_here", "Columns": 6, "Image": "http://www.images.com/img.jpg", "BgMediaType": "picture", "TextOpacity": 60}, {"ActionType": "open-url", "Text": "Buy", "Rows": 1, "ActionBody": "http://www.website.com/go_here", "Columns": 6, "BgColor": "#85bb65", "TextOpacity": 60}], "BgColor": "#FFFFFF", "ButtonsGroupRows": 2}'
        # SAMPLE_ALT_TEXT = "upgrade now!"
        # return RichMediaMessage(rich_media=json.loads(SAMPLE_RICH_MEDIA), alt_text=SAMPLE_ALT_TEXT, min_api_version=1)
        viber.send_messages(sender_id, [TextMessage(text='Все ок')])

    if (text == 'тест3' or text == 'test3'):
        # this is not supoprted yet
        # SAMPLE_RICH_MEDIA = '{"ButtonsGroupColumns": 6, "Buttons": [{"ActionType": "open-url", "BgColor": "#000000", "Rows": 4, "ActionBody": "http://www.website.com/go_here", "Columns": 6, "Image": "http://www.images.com/img.jpg", "BgMediaType": "picture", "TextOpacity": 60}, {"ActionType": "open-url", "Text": "Buy", "Rows": 1, "ActionBody": "http://www.website.com/go_here", "Columns": 6, "BgColor": "#85bb65", "TextOpacity": 60}], "BgColor": "#FFFFFF", "ButtonsGroupRows": 2}'
        # SAMPLE_ALT_TEXT = "upgrade now!"
        # return RichMediaMessage(rich_media=json.loads(SAMPLE_RICH_MEDIA), alt_text=SAMPLE_ALT_TEXT, min_api_version=1)

        #r = '{"Type": "keyboard", "Buttons": [{"ActionType": "open-url", "Text": "Key text", "TextOpacity": 60, "BgMediaType": "gif", "BgColor": "#2db9b9", "BgLoop": "true", "BgMedia": "http://www.url.by/test.gif", "TextVAlign": "middle", "TextHAlign": "center", "Image": "www.tut.by/img.jpg", "Columns": 6, "ActionBody": "www.tut.by", "TextSize": "regular", "Rows": 1}]}'
        r = '{"Type": "keyboard", "Buttons": [{ "Columns": 3, "Rows": 2, "Text": "<font color=\\"#494E67\\">Smoking</font><br><br>", "TextSize": "medium", "TextHAlign": "center", "TextVAlign": "bottom", "ActionType": "reply", "ActionBody": "Smoking", "BgColor": "#f7bb3f", "Image": "https://s12.postimg.org/ti4alty19/smoke.png" }, { "Columns": 3, "Rows": 2, "Text": "<font color=\\"#494E67\\">Non Smoking</font><br><br>", "TextSize": "medium", "TextHAlign": "center", "Tex tVAlign": "bottom", "ActionType": "reply", "ActionBody": "Non smoking", "BgColor": "# f6f7f9", "Image": "https://s14.postimg.org/us7t38az5/Nonsmoke.png"}]}'

        viber.send_messages(sender_id, [TextMessage(text='Все ок', keyboard=json.loads(r))])

    if (text.startswith('відмінити')):
        res = re.findall(r'\d+', text)
        if not res:
            viber.send_messages(sender_id, [TextMessage(text='Перевірте чи Ви все правильно надіслали')])
            return

        logger.info("Rule {0} will be canceled".format(res[0]))
        try:
            payload = {'id': res[0], 'sender': sender_name}
            response_status = requests.get(url='http://mozart.hopto.org:7542/cancel_rule', params=payload, timeout=(10, 10))
            response_status.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(e)
            logging.error("Can't cancel rule")
            viber.send_messages(sender_id, [TextMessage(text='Не вдалося відмінити правило. Передіть на сайт або спробуйте ще раз.')])
        else:
            for user in USERS:
                # here is good place to cancel sms for current uset
                logger.info("Sending message to {0}. id: {1}".format(user['name'], user['id']))
                viber.send_messages(user['id'], [TextMessage(text='Користувач {0} відмінив цей полив'.format(sender_name))])


@app.route('/', methods=['POST'])
def incoming():
    logger.debug("received request. post data: {0}".format(request.get_data()))
    if not viber.verify_signature(request.get_data(), request.headers.get('X-Viber-Content-Signature')):
            return Response(status=403)

    viber_request = viber.parse_request(request.get_data().decode())

    if (isinstance(viber_request, ViberMessageRequest)):
        send_response(viber_request)
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
            # TextMessage(text='Через {0} хвилин {1} будут поливатися {2}хв.\nДля того, щоб відмнінити правило, наберіть \'Відмінити {3}\' або перейдіть за посиланням з наступного повідомлення'.format(timeout, user_friendly_name, time, rule_id))
            TextMessage(text="Через {0} хвилин почнеться полив гілки '{1}'. Триватиме {2} хвилин.\nДля того, щоб відмнінити цей полив, відправте мені повідомлення \n'Відмінити {3}'".format(timeout, user_friendly_name, time, rule_id))
            # URLMessage(media="http://185.20.216.94:7542/cancel_rule?id={0}".format(rule_id))
        ])

    logger.info("Done")
    return Response(status=200)


@app.route('/send_message', methods=['POST'])
def send_message():
    """Send prefomatted message to viber."""
    logger.debug("received request for send_message. post data: {0}".format(request.get_data()))
    data = json.loads(request.get_data().decode())
    users = data['users']
    msg_text = data['msg_text']

    for user in users:
        logger.info("Sending message to {0}. id: {1}".format(user['name'], user['id']))
        viber.send_messages(user['id'], [
            TextMessage(text=msg_text)
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
