from flask import Flask, request, Response
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages import VideoMessage
from viberbot.api.messages.text_message import TextMessage
import logging

from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberUnsubscribedRequest

app = Flask(__name__)
viber = Api(BotConfiguration(
	name='irrigation_bot',
	avatar='http://viber.com/avatar.jpg',
	auth_token='46a517b9f870fcf1-799a9ca308bbd873-7745aee775fec7a7'
))

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


@app.route('/', methods=['POST'])
def incoming():
	viber_request = viber.parse_request(request.get_data())

	if isinstance(viber_request, ViberConversationStartedRequest):
		viber.send_messages(viber_request.get_user().get_id(), [
			TextMessage(text="Welcome!")
		])

	return Response(status=200)


if __name__ == "__main__":
    context = ('server.crt', 'server.key')
    app.run(host='0.0.0.0', port=443, debug=True, ssl_context=context)