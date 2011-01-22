#!/usr/bin/python
#! -*- encoding: utf-8 -*-
###########################################################################
# Don't try to modify parameters below unless you know what you're doing!!!
###########################################################################

CHARACTER_LIMIT = 140

REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'

ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'

AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'

SIGNIN_URL = 'https://api.twitter.com/oauth/authenticate'

BASE_URL = 'https://api.twitter.com/1'

MAX_SHORT_ID_LIST_NUM = 100

MAX_MENTION_ID_LIST_NUM = 100

MAX_REPLY_STATUS = 4

MAX_EXECUTION_TIME = 28 # should not large than 30, in seconds

CRON_NUM = 10

TASK_QUEUE_NUM = 10

USERS_NUM_IN_TASK = 8

LOCALES = {'en-us': 'English(United States)', 'zh-cn': u'简体中文(中国)'}

SHORT_COMMANDS = {
    '@': 'reply',
    'r': 'reply',
    'd': 'dm',
    'ho': 'home',
    'lt': 'list',
    'tl': 'timeline',
    's': 'switch',
    'fo': 'follow',
    'unfo': 'unfollow',
    'b': 'block',
    'ub': 'unblock',
    'm': 'msg',
    'f': 'fav',
    'uf': 'unfav',
    'u': 'user',
    '?': 'help',
    'h': 'help'
}

MODE_DM = 8
MODE_MENTION = 4
MODE_LIST = 2
MODE_HOME = 1
MODE_NONE = 0
