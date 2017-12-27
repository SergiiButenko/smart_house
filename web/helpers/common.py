import inspect

# For get function name intro function. Usage mn(). Return string with current function name. Instead 'query' will be database.QUERY[mn()].format(....)
mn = lambda: inspect.stack()[1][3]

BACKEND_IP = 'http://0.0.0.0:7542'
VIBER_BOT_IP = 'https://mozart.hopto.org:7443'

BRANCHES_LENGTH = 18
RULES_FOR_BRANCHES = [None] * BRANCHES_LENGTH
BRANCHES_SETTINGS = [None] * BRANCHES_LENGTH

REDIS_KEY_FOR_VIBER = 'viber_sent_intervals'
VIBER_SENT_TIMEOUT = 10
USERS = [
    {'name': 'Sergii', 'id': 'cHxBN+Zz1Ldd/60xd62U/w=='},
    {'name': 'Oleg', 'id': 'IRYaSCRnmV1IT1ddtB8Bdw=='},
    {'name': 'Irina', 'id': 'mSR74mGibK+ETvTTx2VvcQ=='}
]

HOURS = 24
RAIN_MAX = 20

START_RULE = 1
STOP_RULE = 2
ENABLED_RULE = 1