from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration

bot_configuration = BotConfiguration(
    name='irrigation_bot',
    avatar='http://viber.com/avatar.jpg',
    auth_token='46a517b9f870fcf1-799a9ca308bbd873-7745aee775fec7a7'
)
viber = Api(bot_configuration)
