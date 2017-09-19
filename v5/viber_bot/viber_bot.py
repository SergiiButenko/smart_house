from flask import Flask, request, Response
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages.text_message import TextMessage
from viberbot.api.messages.rich_media_message import RichMediaMessage
# from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
# from viberbot.api.viber_requests import ViberUnsubscribedRequest


import time
import logging
import sched
import threading
import json

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


USERS = [{'Sergii': 'cHxBN+Zz1Ldd/60xd62U/w=='}, {'Oleg': ''}, {'Irina': ''}]


def get_response(incom_message):
    if (incom_message.text.lower() == 'полив'):
        return TextMessage(text='начать')
    elif (incom_message.text.lower() == 'тест'):
        SAMPLE_RICH_MEDIA = '{"ButtonsGroupColumns": 6, "Buttons": [{"ActionType": "open-url", "BgColor": "#000000", "Rows": 4, "ActionBody": "http://www.website.com/go_here", "Columns": 6, "Image": "http://www.images.com/img.jpg", "BgMediaType": "picture", "TextOpacity": 60}, {"ActionType": "open-url", "Text": "Buy", "Rows": 1, "ActionBody": "http://www.website.com/go_here", "Columns": 6, "BgColor": "#85bb65", "TextOpacity": 60}], "BgColor": "#FFFFFF", "ButtonsGroupRows": 2}'

        SAMPLE_ALT_TEXT = "upgrade now!"

        return RichMediaMessage(rich_media=json.loads(SAMPLE_RICH_MEDIA), alt_text=SAMPLE_ALT_TEXT)


@app.route('/', methods=['POST'])
def incoming():
    logger.debug("received request. post data: {0}".format(request.get_data()))
    if not viber.verify_signature(request.get_data(), request.headers.get('X-Viber-Content-Signature')):
            return Response(status=403)

    viber_request = viber.parse_request(request.get_data().decode())

    if (isinstance(viber_request, ViberMessageRequest)):
        message = get_response(viber_request.message)
        logger.warn("Sending message")
        viber.send_messages(viber_request.sender.id, [
            message
        ])
    elif isinstance(viber_request, ViberSubscribedRequest):
        viber.send_messages(viber_request.get_user.id, [
            TextMessage(text="thanks for subscribing!")
        ])
    elif isinstance(viber_request, ViberFailedRequest):
        logger.warn("client failed receiving message. failure: {0}".format(viber_request))

    return Response(status=200)


@app.route('/send_message', methods=['POST'])
def send_message():
    logger.debug("received request for send_message. post data: {0}".format(request.get_data()))
    data = json.loads(request.get_data())
    users = data['users']
    message = data['message']

    logger.info("Sending message")

    for user in users:
        logger.info("Sending message to {0}. id: {1}".format(user['name'], user['id']))
        viber.send_messages(user['id'], [
            TextMessage(text=message)
        ])


def set_webhook(viber):
    viber.set_webhook('https://mozart.hopto.org:7443/')


if __name__ == "__main__":
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(5, 1, set_webhook, (viber,))
    t = threading.Thread(target=scheduler.run)
    t.start()

    context = ('/var/www/v5/viber_bot/concat.crt', '/var/www/v5/viber_bot/private.key')
    app.run(host='0.0.0.0', port=7443, debug=False, ssl_context=context)
