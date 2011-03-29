#!/usr/bin/python
import config
import counter
import time
import sys

from google.appengine.api import memcache
from google.appengine.ext import db

_short_id_list = dict()

MODE_DM = 8
MODE_MENTION = 4
MODE_LIST = 2
MODE_HOME = 1
MODE_NONE = 0

class MyModel(db.Model):
  def put(self, **kwargs):
    while db.WRITE_CAPABILITY:
      try:
        return super(MyModel, self).put(**kwargs)
      except db.Timeout:
        pass

  def delete(self, **kwargs):
    while db.WRITE_CAPABILITY:
      try:
        return super(MyModel, self).delete(**kwargs)
      except db.Timeout:
        pass

  @classmethod
  def get_by_key_name(cls, key_names, parent=None, **kwargs):
    while db.READ_CAPABILITY:
      try:
        return super(MyModel, cls).get_by_key_name(key_names=key_names, parent=parent, **kwargs)
      except db.Timeout:
        pass


class Session(MyModel):
  shard = db.IntegerProperty(required=True)

  @staticmethod
  def get_all(shard=None, cursor=None):
    while True:
      query = Session.all()
      if cursor is not None:
        query.with_cursor(cursor)
      if shard is not None:
        query.filter('shard =', int(shard))
      try:
        for q in query:
          yield q
      except db.Timeout:
        cursor = query.cursor()
      else:
        break


class GoogleUser(MyModel):
  enabled_user = db.StringProperty(default='')
  shard = db.IntegerProperty(required=True)
  interval = db.IntegerProperty(default=3)
  last_update = db.IntegerProperty(default=0) # remain count for update
  retry = db.IntegerProperty(default=0) # continuouse retry for fail
  last_list_id = db.IntegerProperty(default=0)
  last_msg_id = db.IntegerProperty(default=0)
  last_mention_id = db.IntegerProperty(default=0)
  last_dm_id = db.IntegerProperty(default=0)
  bold_username = db.BooleanProperty(default=True)
  command_prefix = db.StringProperty(default='-')
  date_format = db.StringProperty(default=config.DEFAULT_TIME_FORMAT)
  locale = db.StringProperty(default=config.DEFAULT_LANGUAGE)
  timezone = db.StringProperty(default=config.DEFAULT_TIMEZONE)
  msg_template = db.StringProperty(default=config.DEFAULT_TEMPLATE, multiline=True)
  display_timeline = db.IntegerProperty(default=MODE_DM | MODE_MENTION)
  list_user = db.StringProperty(default='')
  list_id = db.IntegerProperty(default=0)
  list_name = db.StringProperty(default='')
  official_retweet = db.BooleanProperty(default=True)
  reverse = db.BooleanProperty(default=False)

  _jid = None

  def get_jid(self):
    if self._jid is None:
      try:
        self._jid = self.key().name()
      except db.NotSavedError:
        self._jid = ''
    return self._jid

  def set_jid(self, value):
    self._jid = value

  jid = property(get_jid, set_jid)

  @staticmethod
  def add(jid):
    counter.increment('total')
    shard = counter.get_count('total') % config.CRON_NUM
    google_user = GoogleUser(key_name=jid, shard=shard, last_update=int(time.time()))
    google_user.jid = jid
    Db.set_datastore(google_user)
    return google_user

  @staticmethod
  def get_by_jid(jid):
    user = memcache.get(jid, 'jid')
    if user is None:
      user = GoogleUser.get_by_key_name(jid)
      if user:
        Db.set_cache(user)
      else:
        user = None
    return user

  @staticmethod
  def get_all(shard=None, cursor=None):
    while True:
      query = GoogleUser.all().filter('enabled_user >', '')
      if cursor is not None:
        query.with_cursor(cursor)
      if shard is not None:
        query.filter('shard =', int(shard))
      try:
        for q in query:
          yield q
      except db.Timeout:
        cursor = query.cursor()
      else:
        break

  @staticmethod
  def disable(jid):
    user = GoogleUser.get_by_jid(jid)
    if user:
      user.enabled_user = ''
      Db.set_datastore(user)


class TwitterUser(MyModel):
  access_token_key = db.StringProperty(required=True)
  access_token_secret = db.StringProperty()
  twitter_name = db.StringProperty()
  google_user = db.StringProperty(required=True)

  @staticmethod
  def get_by_jid(jid):
    cursor = None
    while True:
      query = TwitterUser.all().filter('google_user =', jid).with_cursor(cursor)
      try:
        for q in query:
          yield q
      except db.Timeout:
        cursor = query.cursor()
      except db.NotSavedError:
        raise GeneratorExit
      else:
        break

  @staticmethod
  def add(jid, access_token_key, access_token_secret=None, twitter_name=None):
    try:
      twitter_user = TwitterUser.get_by_twitter_name(twitter_name, jid)
      if twitter_user is not None:
        twitter_user.delete()
    except db.NotSavedError:
      pass
    twitter_user = TwitterUser(access_token_key=access_token_key, access_token_secret=access_token_secret,
                               twitter_name=twitter_name, google_user=jid)
    Db.set_datastore(twitter_user)

  @staticmethod
  def get_by_twitter_name(name, jid):
    key_name = name if name is not None else ''
    user = memcache.get(jid + ':' + key_name, 'twitter_name')
    if user is None:
      while db.READ_CAPABILITY:
        try:
          user = TwitterUser.all().filter('google_user =', jid).filter('twitter_name =', name).fetch(1)
        except db.Timeout:
          pass
        else:
          break
      if user:
        user = user[0]
        Db.set_cache(user)
      else:
        user = None
    return user


class IdList(MyModel):
  short_id_list = list()
  short_id_list_str = db.TextProperty(default='')
  list_pointer = db.IntegerProperty(default=0)

  @staticmethod
  def add(jid, shard):
    data = ','.join('0' for _ in xrange(config.MAX_SHORT_ID_LIST_NUM))
    cls = type('IdList%d' % shard, (IdList,), {})
    short_id_list = cls(key_name=jid, short_id_list_str=data)
    Db.set_datastore(short_id_list)
    return short_id_list

  @staticmethod
  def get_by_jid(jid, shard):
    if jid in _short_id_list:
      short_id_list = _short_id_list[jid]
    else:
      cls = type('IdList%d' % shard, (IdList,), {})
      setattr(sys.modules[__name__], cls.__name__, cls)
      short_id_list = memcache.get(jid, 'short_id_list')
      if short_id_list is None:
        cls = type('IdList%d' % shard, (IdList,), {})
        short_id_list = cls.get_by_key_name(jid)
      if short_id_list is None:
        short_id_list = IdList.add(jid, shard)
      else:
        Db.set_cache(short_id_list)
      short_id_list.short_id_list = short_id_list.short_id_list_str.split(',')
      global _short_id_list
      _short_id_list[jid] = short_id_list
    return short_id_list

  @staticmethod
  def set(jid, new_id_list):
    global _short_id_list
    new_id_list.short_id_list_str = ','.join(new_id_list.short_id_list)
    _short_id_list[jid] = new_id_list

  @staticmethod
  def flush(jid):
    if jid in _short_id_list:
      Db.set_datastore(_short_id_list[jid])
      del _short_id_list[jid]


class Db:
  @staticmethod
  def set_cache(data):
    def cache_set(*args, **kwargs):
      for _ in xrange(config.MAX_RETRY):
        if memcache.set(*args, **kwargs):
          break

    if isinstance(data, GoogleUser):
      return cache_set(data.jid, data, time=180, namespace='jid')
    elif isinstance(data, TwitterUser):
      key_name = data.twitter_name if data.twitter_name is not None else ''
      return cache_set(key_name, data, time=180, namespace='twitter_name')
    elif isinstance(data, IdList):
      setattr(sys.modules[__name__], data.__class__.__name__, data.__class__)
      return cache_set(data.key().name(), data, time=180, namespace='short_id_list')
    elif type(data) is dict and 'id_str' in data:
      return cache_set(data['id_str'], data, time=86400, namespace='status')
    return False

  @staticmethod
  def set_datastore(data):
    def datastore_set(model):
      try:
        data.put()
      except db.BadKeyError:
        pass

    if data.is_saved():
      Db.set_cache(data)
      db.run_in_transaction(datastore_set, data)
    else:
      db.run_in_transaction(datastore_set, data)
      Db.set_cache(data)
