#!/usr/bin/python
import twitter
import utils
import oauth
import cgi
import logging
import config

from string import Template
from db import TwitterUser, GoogleUser, Db, IdList, MODE_LIST, MODE_MENTION, MODE_DM, MODE_HOME
from pytz.gae import pytz
from mylocale import gettext, LOCALES
from google.appengine.ext import webapp
from google.appengine.api import xmpp, memcache
from google.appengine.ext.webapp.util import run_wsgi_app

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

_locale = config.DEFAULT_LANGUAGE
_ = lambda x: gettext(x, locale=_locale)

class Dummy(object):
  def __getattr__(self, item):
    raise NotImplementedError(item)

  def __getitem__(self, item):
    raise NotImplementedError(item)


class XMPP_handler(webapp.RequestHandler):
  def post(self):
    global _locale
    try:
      message = xmpp.Message(self.request.POST)
    except xmpp.InvalidMessageError:
      return
    jid = message.sender.split('/')[0]
    self._google_user = GoogleUser.get_by_jid(jid)
    if self._google_user is None:
      self._google_user = GoogleUser.add(jid)
    _locale = self._google_user.locale
    if self._google_user.enabled_user:
      self._twitter_user = TwitterUser.get_by_twitter_name(self._google_user.enabled_user, self._google_user.jid)
      self._api = Dummy()
      if self._twitter_user is None:
        self._google_user.enabled_user = ''
      else:
        self._api = twitter.Api(consumer_key=config.OAUTH_CONSUMER_KEY,
                                consumer_secret=config.OAUTH_CONSUMER_SECRET,
                                access_token_key=self._twitter_user.access_token_key,
                                access_token_secret=self._twitter_user.access_token_secret)
        try:
          self._user = self._api.verify_credentials()
          if not self._user:
            raise twitter.TwitterAuthenticationError
        except twitter.TwitterAuthenticationError:
          self._google_user.retry += 1
          if self._google_user.retry >= config.MAX_RETRY:
            GoogleUser.disable(self._google_user.jid)
            xmpp.send_message(self._google_user.jid, _('NO_AUTHENTICATION'))
          else:
            Db.set_datastore(self._google_user)
          return
        else:
          if self._google_user.retry > 0:
            self._google_user.retry = 0
          if self._twitter_user.twitter_name != self._user['screen_name']:
            self._twitter_user.twitter_name = self._user['screen_name']
            self._google_user.enabled_user = self._user['screen_name']
    else:
      self._twitter_user = Dummy()
      self._api = Dummy()
      self._user = Dummy()
    utils.set_jid(self._google_user.jid)
    result = self.parse_command(message.body)
    if result is None:
      return
    if result:
      message.reply(result)
    IdList.flush(self._google_user.jid)
    Db.set_datastore(self._google_user)

  def parse_command(self, content):
    content = content.rstrip()
    if content.startswith(self._google_user.command_prefix):
      args = content[len(self._google_user.command_prefix):].split(' ')
      args[0] = args[0].lower()
      if args[0] in SHORT_COMMANDS:
        args[0] = SHORT_COMMANDS[args[0]]
      func_name = 'func_' + args[0]
      try:
        func = getattr(self, func_name)
      except (AttributeError, UnicodeEncodeError):
        return _('INVALID_COMMAND')
      try:
        return func(args[1:])
      except NotImplementedError:
        return _('INVALID_COMMAND')
      except twitter.TwitterInternalServerError:
        return _('INTERNAL_SERVER_ERROR')
    else:
      if isinstance(self._api, Dummy):
        return ''
      if not len(content):
        return ''
      if len(content) > twitter.CHARACTER_LIMIT:
        return _('WORDS_COUNT_EXCEED') % (len(content), twitter.CHARACTER_LIMIT)
      try:
        self._api.post_update(content)
      except twitter.TwitterError, e:
        if 'Status is a duplicate' in e.message:
          return _('STATUS_DUPLICATE')
      return _('SUCCESSFULLY_UPDATE_STATUS')

  def func_msg(self, args):
    length = len(args)
    if length == 1 and (args[0].isdigit() or (args[0] and args[0][0] == '#' and args[0][1:].isdigit())):
      if args[0][0] == '#':
        short_id = int(args[0][1:])
        id = utils.restore_short_id(short_id, self._google_user.jid)
      elif int(args[0]) < config.MAX_SHORT_ID_LIST_NUM:
        short_id = int(args[0])
        id = utils.restore_short_id(short_id, self._google_user.jid)
      else:
        short_id = None
        id = long(args[0])
      id_str = '#' + str(short_id) if short_id else str(id)
      statuses = list()
      for __ in xrange(config.MAX_REPLY_STATUS):
        try:
          status = self._api.get_status(id)
        except twitter.TwitterError, e:
          if 'No status found' in e.message:
            if statuses:
              break
            else:
              return _('STATUS_NOT_FOUND') % id_str
        statuses.append(status)
        if 'in_reply_to_status_id' in status:
          id = status['in_reply_to_status_id']
        else:
          break
      return _('STATUSES_CONVERSATION') + '\n\n' + utils.parse_statuses(statuses, reverse=False)
    raise NotImplementedError


  def func_reply(self, args):
    length = len(args)
    if not length or (length == 1 and (args[0][0].lower() == 'p' and args[0][1:].isdigit())):
      page = args[0][1:] if length else 1
      statuses = self._api.get_mentions(page=int(page))
      return _('MENTIONS') + _('PAGE') % str(page) + '\n\n' + utils.parse_statuses(statuses)
    elif length > 1 and (args[0].isdigit() or (args[0] and args[0][0] == '#' and args[0][1:].isdigit())\
    and ' '.join(args[1:])):
      if args[0][0] == '#':
        short_id = int(args[0][1:])
        id = utils.restore_short_id(short_id, self._google_user.jid)
      elif int(args[0]) < config.MAX_SHORT_ID_LIST_NUM:
        short_id = int(args[0])
        id = utils.restore_short_id(short_id, self._google_user.jid)
      else:
        short_id = None
        id = int(args[0])
      id_str = '#' + str(short_id) if short_id else str(id)
      try:
        status = self._api.get_status(id)
      except twitter.TwitterError, e:
        if 'No status found' in e.message:
          return _('STATUS_NOT_FOUND') % id_str
      message = u'@%s %s' % (status['user']['screen_name'], ' '.join(args[1:]))
      if len(message) > twitter.CHARACTER_LIMIT:
        return _('WORDS_COUNT_EXCEED') % (len(message), twitter.CHARACTER_LIMIT)
      try:
        self._api.post_update(message, id)
      except twitter.TwitterError, e:
        if 'Status is a duplicate' in e.message:
          return _('STATUS_DUPLICATE')
      return _('SUCCESSFULLY_REPLY_TO') % status['user']['screen_name']
    raise NotImplementedError

  def func_time(self, args):
    length = len(args)
    if not length:
      return _('INTERVAL') % str(self._google_user.interval)
    elif length == 1 and args[0].isdigit():
      self._google_user.interval = int(args[0])
      return _('INTERVAL') % str(self._google_user.interval)
    raise NotImplementedError

  def func_dm(self, args):
    length = len(args)
    if not length or (length == 1 and args[0][0].lower() == 'p' and args[0][1:].isdigit()):
      page = 1 if not length else args[0][1:]
      statuses = self._api.get_direct_messages(page=int(page))
      return _('DIRECT_MESSAGES') + _('PAGE') % str(page) + '\n\n' + utils.parse_statuses(statuses)
    elif length > 1 and ' '.join(args[1:]):
      message = ' '.join(args[1:])
      if len(message) > twitter.CHARACTER_LIMIT:
        return _('WORDS_COUNT_EXCEED') % (len(message), twitter.CHARACTER_LIMIT)
      try:
        self._api.post_direct_message(args[0], message)
      except twitter.TwitterError, e:
        if 'Not found' in e.message:
          return _('USER_NOT_FOUND') % args[0]
        elif 'You cannot send messages to users who are not following you' in e.message:
          return _('MESSAGE_TO_NOT_FOLLOWED')
      return _('SUCCESSFULLY_MESSAGE') % args[0]
    raise NotImplementedError

  def func_follow(self, args):
    if len(args) == 1:
      try:
        self._api.create_friendship(args[0])
      except twitter.TwitterError, e:
        if 'is already on your list' in e.message:
          return _('ALREADY_FOLLOWED') % args[0]
        elif 'You have been blocked' in e.message:
          return _('BLOCKED') % args[0]
        elif 'Not found' in e.message:
          return _('USER_NOT_FOUND') % args[0]
      return _('SUCCESSFULLY_FOLLOW') % args[0]
    raise NotImplementedError

  def func_unfollow(self, args):
    if len(args) == 1:
      try:
        self._api.destroy_friendship(args[0])
      except twitter.TwitterError, e:
        if 'You are not friends with' in e.message:
          return _('You are not friends with %s') % args[0]
        elif 'Not found' in e.message:
          return _('USER_NOT_FOUND') % args[0]
      return _('SUCCESSFULLY_UNFOLLOW') % args[0]
    raise NotImplementedError

  def func_if(self, args):
    if len(args) == 1:
      try:
        result = self._api.exists_friendship(self._google_user.enabled_user, args[0])
      except twitter.TwitterError, e:
        if 'Could not find both specified users' in e.message:
          return _('USER_NOT_FOUND') % args[0]
      if result:
        return _('FOLLOWING_YOU') % args[0]
      else:
        return _('NOT_FOLLOWING_YOU') % args[0]
    raise NotImplementedError

  def func_block(self, args):
    if len(args) == 1:
      try:
        self._api.create_block(args[0])
      except twitter.TwitterError, e:
        if 'Not found' in e.message:
          return _('USER_NOT_FOUND') % args[0]
      return _('SUCCESSFULLY_BLOCK') % args[0]
    raise NotImplementedError

  def func_unblock(self, args):
    if len(args) == 1:
      try:
        self._api.destroy_block(args[0])
      except twitter.TwitterError, e:
        if 'Not found' in e.message:
          return _('USER_NOT_FOUND') % args[0]
      return _('SUCCESSFULLY_UNBLOCK') % args[0]
    raise NotImplementedError

  def func_del(self, args):
    length = len(args)
    if not length or (length == 1 and (args[0].isdigit() or (args[0] and args[0][0] == '#' and args[0][1:].isdigit()))):
      if not length:
        short_id = None
        id = self._user['status']['id']
      elif args[0][0] == '#':
        short_id = int(args[0][1:])
        id = utils.restore_short_id(short_id, self._google_user.jid)
      elif int(args[0]) < config.MAX_SHORT_ID_LIST_NUM:
        short_id = int(args[0])
        id = utils.restore_short_id(short_id, self._google_user.jid)
      else:
        short_id = None
        id = long(args[0])
      id_str = '#' + str(short_id) if short_id else str(id)
      try:
        response = self._api.destroy_status(id)
      except twitter.TwitterError, e:
        if 'No status found' in e.message:
          return _('STATUS_NOT_FOUND') % id_str
        elif "You may not delete another user's status" in e.message:
          return _('DELETE_ANOTHER_USER_STATUS')
      return _('STATUS_DELETED') % (id_str, response['text'])
    raise NotImplementedError

  def func_on(self, args):
    if len(args):
      for a in args:
        if a == 'home':
          self._google_user.display_timeline |= MODE_HOME
        elif a == 'mention':
          self._google_user.display_timeline |= MODE_MENTION
        elif a == 'dm':
          self._google_user.display_timeline |= MODE_DM
        elif a == 'list':
          self._google_user.display_timeline |= MODE_LIST
    modes = []
    if self._google_user.display_timeline & MODE_LIST:
      modes.append('list')
    if self._google_user.display_timeline & MODE_HOME:
      modes.append('home')
    if self._google_user.display_timeline & MODE_MENTION:
      modes.append('mention')
    if self._google_user.display_timeline & MODE_DM:
      modes.append('dm')
    return _('ON_MODE') % ', '.join(modes)

  def func_off(self, args):
    if len(args):
      for a in args:
        if a == 'home':
          self._google_user.display_timeline &= ~MODE_HOME
        elif a == 'mention':
          self._google_user.display_timeline &= ~MODE_MENTION
        elif a == 'dm':
          self._google_user.display_timeline &= ~MODE_DM
        elif a == 'list':
          self._google_user.display_timeline &= ~MODE_LIST
    return self.func_on([])

  def func_live(self, args):
    length = len(args)
    if not length:
      if self._google_user.list_user and self._google_user.list_id and self._google_user.list_name:
        return _('LIVE_MODE') % (self._google_user.list_user + '/' + self._google_user.list_name)
      return _('USE_LIVE')
    elif 1 <= length <= 2:
      if length == 1:
        path = args[0].split('/')
        if len(path) == 1:
          user = self._google_user.enabled_user
          list_id = path[0]
        elif len(path) == 2:
          user = path[0]
          list_id = path[1]
        else:
          raise NotImplementedError
      else:
        user = args[0]
        list_id = args[1]
      try:
        response = self._api.get_list(user, list_id)
      except twitter.TwitterError, e:
        if 'Not found' in e.message:
          return _('LIST_NOT_FOUND') % (list_id if user == self._google_user.enabled_user else user + '/' + list_id)
      self._google_user.list_user = response['user']['screen_name']
      self._google_user.list_id = response['id']
      self._google_user.list_name = response['slug']
      return _('LIVE_MODE') % (self._google_user.list_user + '/' + self._google_user.list_name)
    raise NotImplementedError

  def func_fav(self, args):
    length = len(args)
    if not length or (length == 1 and (args[0][0].lower() == 'p' and args[0][1:].isdigit())):
      page = args[0][1:] if length else 1
      statuses = self._api.get_favorites(page=int(page))
      return _('FAVOURITES') + _('PAGE') % str(page) + '\n\n' + utils.parse_statuses(statuses)
    elif length == 1 and (args[0].isdigit() or (args[0] and args[0][0] == '#' and args[0][1:].isdigit())):
      if args[0][0] == '#':
        short_id = int(args[0][1:])
        id = utils.restore_short_id(short_id, self._google_user.jid)
      elif int(args[0]) < config.MAX_SHORT_ID_LIST_NUM:
        short_id = int(args[0])
        id = utils.restore_short_id(short_id, self._google_user.jid)
      else:
        short_id = None
        id = long(args[0])
      id_str = '#' + str(short_id) if short_id else str(id)
      try:
        self._api.create_favorite(id)
      except twitter.TwitterError, e:
        if 'No status found' in e.message:
          return _('STATUS_NOT_FOUND') % id_str
      return _('FAVOURITED') % id_str
    raise NotImplementedError

  def func_unfav(self, args):
    if len(args) == 1 and (args[0].isdigit() or (args[0] and args[0][0] == '#' and args[0][1:].isdigit())):
      if args[0][0] == '#':
        short_id = int(args[0][1:])
        id = utils.restore_short_id(short_id, self._google_user.jid)
      elif int(args[0]) < config.MAX_SHORT_ID_LIST_NUM:
        short_id = int(args[0])
        id = utils.restore_short_id(short_id, self._google_user.jid)
      else:
        short_id = None
        id = long(args[0])
      id_str = '#' + str(short_id) if short_id else str(id)
      try:
        self._api.destroy_favorite(id)
      except twitter.TwitterError, e:
        if 'No status found' in e.message:
          return _('STATUS_NOT_FOUND') % id_str
      return _('UNFAVOURITED') % id_str
    raise NotImplementedError

  def func_home(self, args):
    length = len(args)
    if not length:
      page = 1
    elif length == 1 and args[0][0].lower() == 'p' and args[0][1:].isdigit():
      page = args[0][1:]
    else:
      raise NotImplementedError
    statuses = self._api.get_home_timeline(page=int(page))
    return _('TIMELINE') + _('PAGE') % str(page) + '\n\n' + utils.parse_statuses(statuses)

  def func_timeline(self, args):
    length = len(args)
    if not length or (length == 1 and (args[0][0].lower() == 'p' and args[0][1:].isdigit())):
      screen_name = self._user['screen_name']
      page = args[0][1:] if length else 1
    elif length == 1 or (length == 2 and (args[1][0].lower() == 'p' and args[1][1:].isdigit())):
      screen_name = args[0]
      page = args[1][1:] if length == 2 else 1
    else:
      raise NotImplementedError
    try:
      statuses = self._api.get_user_timeline(screen_name=screen_name, page=int(page))
    except twitter.TwitterError, e:
      if 'Not found' in e.message:
        return _('USER_NOT_FOUND') % screen_name
      elif 'Not authorized' in e.message:
        return _('PROTECTED_USER')
    return _('USER_TIMELINE') % screen_name + _('PAGE') % str(page) + '\n\n' + utils.parse_statuses(statuses)

  def func_list(self, args):
    length = len(args)
    if length == 1 or (length == 2 and (args[1][0].lower() == 'p' and args[1][1:].isdigit())):
      path = args[0].split('/')
      if len(path) == 1:
        user = self._google_user.enabled_user
        list_id = path[0]
      elif len(path) == 2:
        user = path[0]
        list_id = path[1]
      else:
        raise NotImplementedError
      page = args[1][1:] if length == 2 else 1
    elif length == 2 or (length == 3 and (args[2][0].lower() == 'p' and args[2][1:].isdigit())):
      user = args[0]
      list_id = args[1]
      page = args[2][1:] if length == 3 else 1
    else:
      raise NotImplementedError
    try:
      statuses = self._api.get_list_statuses(user=user, id=list_id, page=int(page))
    except twitter.TwitterError, e:
      if 'Not found' in e.message:
        return _('LIST_NOT_FOUND') % args[0]
    return _('LIST') % (user + '/' + str(list_id)) + _('PAGE') % str(page) + '\n\n' + utils.parse_statuses(statuses)

  def func_ra(self, args):
    if len(args) > 1 and (
    args[0].isdigit() or (args[0] and args[0][0] == '#' and args[0][1:].isdigit()) and ' '.join(args[1:])):
      if args[0][0] == '#':
        short_id = int(args[0][1:])
        id = utils.restore_short_id(short_id, self._google_user.jid)
      elif int(args[0]) < config.MAX_SHORT_ID_LIST_NUM:
        short_id = int(args[0])
        id = utils.restore_short_id(short_id, self._google_user.jid)
      else:
        short_id = None
        id = int(args[0])
      id_str = '#' + str(short_id) if short_id else str(id)
      try:
        status = self._api.get_status(id)
      except twitter.TwitterError, e:
        if 'No status found' in e.message:
          return _('STATUS_NOT_FOUND') % id_str
      mention_users = [status['user']['screen_name']]
      if 'user_mentions' in status['entities']:
        for u in status['entities']['user_mentions']:
          name = u['screen_name']
          if name != self._user['screen_name'] and name not in mention_users:
            mention_users.append(name)
      message = u'%s %s' % (' '.join(['@' + x for x in mention_users]), ' '.join(args[1:]))
      if len(message) > twitter.CHARACTER_LIMIT:
        return _('WORDS_COUNT_EXCEED') % (len(message), twitter.CHARACTER_LIMIT)
      try:
        self._api.post_update(message, id)
      except twitter.TwitterError, e:
        if 'Status is a duplicate' in e.message:
          return _('STATUS_DUPLICATE')
      return _('SUCCESSFULLY_REPLY_TO') % ', '.join(mention_users)
    raise NotImplementedError

  def func_re(self, args):
    if len(args) == 1 and (args[0] and args[0].isdigit() or (args[0][0] == '#' and args[0][1:].isdigit())):
      if args[0][0] == '#':
        short_id = int(args[0][1:])
        id = utils.restore_short_id(short_id, self._google_user.jid)
      elif int(args[0]) < config.MAX_SHORT_ID_LIST_NUM:
        short_id = int(args[0])
        id = utils.restore_short_id(short_id, self._google_user.jid)
      else:
        short_id = None
        id = int(args[0])
      id_str = '#' + str(short_id) if short_id else str(id)
      try:
        self._api.create_retweet(id)
      except twitter.TwitterError, e:
        if 'No status found' in e.message:
          return _('STATUS_NOT_FOUND') % id_str
      return _('SUCCESSFULLY_RETWEET') % id_str
    raise NotImplementedError

  def func_rt(self, args):
    length = len(args)
    if length >= 1 and (args[0].isdigit() or (args[0] and args[0][0] == '#' and args[0][1:].isdigit())):
      if args[0][0] == '#':
        short_id = int(args[0][1:])
        id = utils.restore_short_id(short_id, self._google_user.jid)
      elif int(args[0]) < config.MAX_SHORT_ID_LIST_NUM:
        short_id = int(args[0])
        id = utils.restore_short_id(short_id, self._google_user.jid)
      else:
        short_id = None
        id = int(args[0])
      id_str = '#' + str(short_id) if short_id else str(id)
      try:
        status = self._api.get_status(id)
      except twitter.TwitterError, e:
        if 'No status found' in e.message:
          return _('STATUS_NOT_FOUND') % id_str
        else:
          logging.error(e)
          return ''
      if length > 1:
        user_msg = ' '.join(args[1:])
      else:
        user_msg = ''
      if user_msg and user_msg[-1].isalnum():
        user_msg += ' '
      message = u'%sRT @%s:%s' % (user_msg, status['user']['screen_name'], status['text'])
      if len(message) > twitter.CHARACTER_LIMIT:
        message = message[:138] + '..'
      try:
        json = self._api.post_update(message, id)
      except twitter.TwitterError, e:
        if 'Status is a duplicate' in e.message:
          return _('STATUS_DUPLICATE')
        else:
          logging.error('RT Error: %s' % e.message)
          return ''
      else:
        return _('SUCCESSFULLY_RT') % (id_str, json['text'])
    raise NotImplementedError

  def func_timezone(self, args):
    length = len(args)
    if not length:
      return _('CURRENT_TIMEZONE') % self._google_user.timezone
    elif length == 1:
      try:
        pytz.timezone(args[0])
      except pytz.UnknownTimeZoneError:
        return _('INVALID_TIMEZONE')
      self._google_user.timezone = args[0]
      return _('SET_TIMEZONE_SUCCESSFULLY')
    raise NotImplementedError

  def func_locale(self, args):
    length = len(args)
    if not length:
      return _('CURRENT_LOCALE') % LOCALES[self._google_user.locale]
    elif length == 1:
      if args[0] not in LOCALES:
        return _('INVALID_LOCALE')
      global _locale
      _locale = args[0]
      self._google_user.locale = args[0]
      return _('SET_LOCALE_SUCCESSFULLY')
    raise NotImplementedError

  def func_retweet(self, args):
    length = len(args)
    if not length or length == 1:
      if length == 1:
        value = args[0].lower()
        if value in ('true', '1', 'yes'):
          value = True
        elif value in ('false', '0', 'no'):
          value = False
        else:
          raise NotImplementedError
        self._google_user.official_retweet = value
      return _('RETWEET_MODE') if self._google_user.official_retweet else _('RT_MODE')
    raise NotImplementedError

  def func_bold(self, args):
    length = len(args)
    if not length or length == 1:
      if length == 1:
        value = args[0].lower()
        if value in ('true', '1', 'yes'):
          value = True
        elif value in ('false', '0', 'no'):
          value = False
        else:
          raise NotImplementedError
        self._google_user.bold_username = value
      return _('BOLD_MODE_ON') if self._google_user.bold_username else _('BOLD_MODE_OFF')
    raise NotImplementedError

  def func_reverse(self, args):
    length = len(args)
    if not length or length:
      if length == 1:
        value = args[0].lower()
        if value in ('true', '1', 'yes'):
          value = True
        elif value in ('false', '0', 'no'):
          value = False
        else:
          raise NotImplementedError
        self._google_user.reverse = value
      return _('REVERSE_MODE_ON') if self._google_user.reverse else _('REVERSE_MODE_OFF')
    raise NotImplementedError

  def func_msgtpl(self, args):
    if len(args):
      tpl = ' '.join(args)
      while tpl[-2::] == r'\n':
        tpl = tpl[:len(tpl) - 2] + '\n'
      self._google_user.msg_template = tpl
    return _('MSG_TEMPLATE') % self._google_user.msg_template

  def func_datefmt(self, args):
    if len(args):
      self._google_user.date_format = ' '.join(args)
    return _('DATE_TEMPLATE') % self._google_user.date_format

  def func_prefix(self, args):
    length = len(args)
    if length <= 1:
      if length:
        self._google_user.command_prefix = args[0]
      return _('COMMAND_PREFIX') % self._google_user.command_prefix
    raise NotImplementedError

  def func_switch(self, args):
    length = len(args)
    if length > 1:
      raise NotImplementedError
    else:
      twitter_users = TwitterUser.get_by_jid(self._google_user.jid)
      twitter_users_name = [u.twitter_name for u in twitter_users if u.twitter_name is not None]
      if not length:
        return _('NOW_USING') % self._google_user.enabled_user + '\n'\
        + _('ALL_TWITTER_USERS_NAME') % '\n'.join(twitter_users_name)
      else:
        twitter_users_name_ci = [x.lower() for x in twitter_users_name]
        twitter_name_ci = args[0].lower()
        if twitter_name_ci in twitter_users_name_ci:
          i = twitter_users_name_ci.index(twitter_name_ci)
          self._google_user.enabled_user = twitter_users_name[i]
          return _('ENABLED_TWITTER_USER_CHANGED') % self._google_user.enabled_user
        else:
          return _('NOT_ASSOCIATED_TWITTER_USER')

  def func_user(self, args):
    length = len(args)
    if length > 1:
      raise NotImplementedError
    else:
      if not length:
        user = self._user['screen_name']
      else:
        user = args[0]
      try:
        result = self._api.get_user(user)
      except twitter.TwitterError, e:
        if 'Not found' in e.message:
          return _('USER_NOT_FOUND') % args[0]
      result['profile_image_url'] = result['profile_image_url'].replace('_normal.', '.')
      for x in result:
        if result[x] is None:
          result[x] = ''
      if 'status' in result:
        result['status'] = result['status']['text']
      else:
        result['status'] = ''
      if result['following']:
        result['following'] = _('YOU_FOLLOWING') % result['screen_name']
      elif result['follow_request_sent']:
        result['following'] = _('YOU_HAVE_REQUESTED') % result['screen_name']
      else:
        result['following'] = _('YOU_DONT_FOLLOW') % result['screen_name']
      return Template(_('USER_PROFILE')).safe_substitute(result)

  def func_remove(self, args):
    length = len(args)
    msg = ''
    if length <= 1:
      if not length:
        user = self._google_user.enabled_user
      else:
        user = args[0]
      if user != '':
        twitter_user = TwitterUser.get_by_twitter_name(user, self._google_user.jid)
        if twitter_user is not None:
          twitter_user.delete()
          memcache.delete(self._google_user.jid + ':' + user, namespace='twitter_name')
          if self._google_user.enabled_user == user:
            self._google_user.enabled_user = ''
          msg += _('TWITTER_USER_DELETED') % user
      msg += _('SPECIFY_ANOTHER_USER')
      return msg
    raise NotImplementedError

  def func_oauth(self, args):
    length = len(args)
    if not length or length == 2:
      consumer = oauth.Consumer(config.OAUTH_CONSUMER_KEY, config.OAUTH_CONSUMER_SECRET)
      client = oauth.Client(consumer)
      resp = client.request(twitter.REQUEST_TOKEN_URL, "GET")
      if not resp:
        return _('NETWORK_ERROR')
      self._request_token = dict(cgi.parse_qsl(resp))
      oauth_token = self._request_token['oauth_token']
      redirect_url = "%s?oauth_token=%s" % (twitter.AUTHORIZATION_URL, oauth_token)
      if not length:
        TwitterUser.add(self._google_user.jid, oauth_token)
        return _('OAUTH_URL') % redirect_url
      import oauth_proxy

      pin = oauth_proxy.login_oauth(redirect_url, args[0], args[1])
      if pin == '':
        return _('NETWORK_ERROR')
      elif pin is None:
        return _('WRONG_USER_OR_PASSWORD')
      return self.func_bind([pin], oauth_token)
    else:
      raise NotImplementedError

  def func_bind(self, args, oauth_token=None):
    if len(args) == 1:
      jid = self._google_user.jid
      if oauth_token is None:
        twitter_user = TwitterUser.get_by_twitter_name(None, jid)
        if twitter_user is None:
          return _('INVALID_PIN_CODE') % ''
        oauth_token = twitter_user.access_token_key
      token = oauth.Token(oauth_token)
      token.set_verifier(args[0])
      consumer = oauth.Consumer(config.OAUTH_CONSUMER_KEY, config.OAUTH_CONSUMER_SECRET)
      client = oauth.Client(consumer, token)
      resp = client.request(twitter.ACCESS_TOKEN_URL, "POST")
      if not resp:
        return _('NETWORK_ERROR')
      access_token = dict(cgi.parse_qsl(resp))
      if 'oauth_token' not in access_token:
        return _('INVALID_PIN_CODE') % args[0]
      if oauth_token is None:
        twitter_user.delete()
      TwitterUser.add(jid, access_token['oauth_token'], access_token['oauth_token_secret'], access_token['screen_name'])
      if self._google_user.enabled_user == '':
        self._google_user.enabled_user = access_token['screen_name']
      if IdList.get_by_jid(jid, self._google_user.shard) is None:
        IdList.add(jid, self._google_user.shard)
      return _('SUCCESSFULLY_BIND') % access_token['screen_name']
    else:
      raise NotImplementedError

  def func_help(self, args):
    length = len(args)
    if not length:
      return _('ALL_COMMANDS')
    elif length == 1:
      command = args[0].lower()
      if command in SHORT_COMMANDS:
        command = SHORT_COMMANDS[command]
      if command == 'help':
        return _('ALL_COMMANDS')
      if command == 'locale':
        return _('HELP_LOCALE') % '\n'.join(k + ':' + LOCALES[k] for k in LOCALES)
      func_name = 'func_' + command
      if func_name in dir(self):
        return _('HELP_' + command.upper())
      else:
        return ''


def main():
  application = webapp.WSGIApplication([('/_ah/xmpp/message/chat/', XMPP_handler)])
  run_wsgi_app(application)

if __name__ == "__main__":
  main()