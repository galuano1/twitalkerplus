#!/usr/bin/python
import re

from pytz.gae import pytz
from string import Template
from datetime import datetime
from db import IdList, Db, GoogleUser
from email.utils import parsedate
from xml.sax.saxutils import unescape
from google.appengine.ext import db
from constant import MAX_MENTION_ID_LIST_NUM, MAX_SHORT_ID_LIST_NUM

_jid = None
_user = None

def set_jid(jid):
  global _jid
  global _user
  _jid = jid
  _user = GoogleUser.get_by_jid(jid)

def parse_status(status):
  if 'retweeted_status' in status and _user.official_retweet:
    status = status['retweeted_status']
  msg_dict = {'content': unescape(status['text']), 'id': str(status['id'])}
  if 'user' in status:
    msg_dict['username'] = status['user']['screen_name']
    Db.set_cache(status)
  elif 'sender' in status:
    msg_dict['username'] = status['sender_screen_name']
  else:
    msg_dict['username'] = ''
  if msg_dict['username'] and _user.bold_username:
    msg_dict['username'] = '*%s*' % msg_dict['username']
  username = _user.enabled_user
  username_at = "@" + username
  short_id = None
  if username_at in msg_dict['content']:
    if _user.bold_username:
      msg_dict['content'] = msg_dict['content'].replace(username_at, '*%s*' % username_at)
    if 'user' in status:
      short_id = generate_short_id(status['id'], True)
  else:
    if 'user' in status:
      short_id = generate_short_id(status['id'], False)
  msg_dict['shortid'] = '#' + str(short_id) if short_id is not None else ''
  utc = pytz.utc
  t = parsedate(status['created_at'])[:6]
  t = datetime(*t)
  utc_dt = utc.localize(t)
  tz = pytz.timezone(_user.timezone)
  t = tz.normalize(utc_dt.astimezone(tz))
  msg_dict['time'] = t.strftime(_user.date_format.encode('UTF-8')).decode('UTF-8')
  if 'source' in status:
    source = re.match(r'<a .*>(.*)</a>', status['source'])
    msg_dict['source'] = source.group(1) if source else status['source']
  else:
    msg_dict['source'] = ''
  return Template(unicode(_user.msg_template)).safe_substitute(msg_dict)

def parse_statuses(statuses, reverse=True, filter_self=False):
  if statuses:
    msgs = list()
    if reverse:
      statuses.reverse()
    for status in statuses:
      if filter_self and 'user' in status and status['user']['screen_name'] == _user.enabled_user:
        continue
      msgs.append(parse_status(status))
    return '\n'.join(msgs)
  return ''


def generate_short_id(id, is_mention=False):
  if not db.WRITE_CAPABILITY:
    return None
  id = str(id)
  id_list = IdList.get_by_jid(_jid, _user.shard)
  if id in id_list.short_id_list:
    return id_list.short_id_list.index(id)
  else:
    if is_mention:
      short_id_list_pointer = id_list.mention_list_pointer
    else:
      short_id_list_pointer = id_list.timeline_list_pointer
    if is_mention:
      short_id_list_pointer %= MAX_MENTION_ID_LIST_NUM
    else:
      short_id_list_pointer = (short_id_list_pointer % MAX_SHORT_ID_LIST_NUM) + MAX_MENTION_ID_LIST_NUM
    id_list.short_id_list[short_id_list_pointer] = id
    short_id_list_pointer += 1
    if is_mention:
      id_list.mention_list_pointer = short_id_list_pointer % MAX_MENTION_ID_LIST_NUM
    else:
      id_list.timeline_list_pointer = (short_id_list_pointer - MAX_MENTION_ID_LIST_NUM) % MAX_SHORT_ID_LIST_NUM
    IdList.set(_jid, id_list)
    return short_id_list_pointer - 1

def restore_short_id(short_id, jid):
  if short_id < MAX_SHORT_ID_LIST_NUM + MAX_MENTION_ID_LIST_NUM:
    id_list = IdList.get_by_jid(jid, _user.shard)
    id = id_list.short_id_list[short_id]
    if id:
      return int(id)
  return None
