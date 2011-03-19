#!/usr/bin/python
import twitter
import utils
import logging
import traceback
import config

from StringIO import StringIO
from db import Db, GoogleUser, TwitterUser, IdList, MODE_HOME, MODE_LIST, MODE_MENTION, MODE_DM
from mylocale import gettext
from time import time
from google.appengine.ext import webapp
from google.appengine.api import xmpp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

class worker_handler(webapp.RequestHandler):
  def get(self):
    jids = self.request.get_all('jid')
    self.process(jids)

  def post(self):
    jids = self.request.get_all('jid')
    self.process(jids)

  def process(self, jids):
    self.response.out.write(str(jids))
    if not db.WRITE_CAPABILITY:
      return
    for jid in jids:
      try:
        google_user = GoogleUser.get_by_jid(jid)
      except db.Error:
        continue
      _ = lambda x: gettext(x, locale=google_user.locale)
      try:
        twitter_user = TwitterUser.get_by_twitter_name(google_user.enabled_user, google_user.jid)
      except db.Error:
        continue
      if twitter_user is None:
        google_user.enabled_user = ''
        Db.set_datastore(google_user)
        continue
      api = twitter.Api(consumer_key=config.OAUTH_CONSUMER_KEY,
                        consumer_secret=config.OAUTH_CONSUMER_SECRET,
                        access_token_key=twitter_user.access_token_key,
                        access_token_secret=twitter_user.access_token_secret)
      try:
        self._user = api.verify_credentials()
        if not self._user or 'screen_name' not in self._user:
          raise twitter.TwitterError
      except twitter.TwitterError:
        google_user.retry += 1
        if google_user.retry >= config.MAX_RETRY:
          GoogleUser.disable(jid=google_user.jid)
          xmpp.send_message(google_user.jid, _('NO_AUTHENTICATION'))
        else:
          Db.set_cache(google_user)
        continue
      finally:
        if google_user.retry > 0:
          google_user.retry = 0
          Db.set_cache(google_user)
      if twitter_user.twitter_name != self._user['screen_name']:
        twitter_user.twitter_name = self._user['screen_name']
        Db.set_cache(twitter_user)
        google_user.enabled_user = self._user['screen_name']
        Db.set_cache(google_user)
      utils.set_jid(google_user.jid)
      home_statuses = []
      home_mention_statuses = []
      all_statuses = []

      if google_user.display_timeline & MODE_HOME:
        home_rpc = api.get_home_timeline(since_id=google_user.last_msg_id, async=True)
      elif google_user.display_timeline & MODE_MENTION:
        home_rpc = api.get_home_timeline(since_id=google_user.last_mention_id, async=True)
      else:
        home_rpc = None
      if google_user.display_timeline & MODE_LIST:
        list_rpc = api.get_list_statuses(user=google_user.list_user, id=google_user.list_id,
                                         since_id=google_user.last_list_id, async=True)
      else:
        list_rpc = None
      if google_user.display_timeline & MODE_MENTION:
        mention_rpc = api.get_mentions(since_id=google_user.last_mention_id, async=True)
      else:
        mention_rpc = None
      if google_user.display_timeline & MODE_DM:
        dm_rpc = api.get_direct_messages(since_id=google_user.last_dm_id, async=True)
      else:
        dm_rpc = None
      if google_user.display_timeline & MODE_HOME:
        try:
          home_statuses = api._process_result(home_rpc)
          if home_statuses:
            all_statuses.extend(home_statuses)
            if home_statuses[0]['id'] > google_user.last_msg_id:
              google_user.last_msg_id = home_statuses[0]['id']
        except twitter.TwitterInternalServerError:
          pass
        except BaseException:
          err = StringIO('')
          traceback.print_exc(file=err)
          logging.error(google_user.jid + ' Home:\n' + err.getvalue())
      if google_user.display_timeline & MODE_LIST:
        try:
          statuses = api._process_result(list_rpc)
          if statuses:
            all_statuses.extend(statuses)
            if statuses[0]['id'] > google_user.last_list_id:
              google_user.last_list_id = statuses[0]['id']
        except twitter.TwitterInternalServerError:
          pass
        except BaseException, e:
          if 'Not found' not in e.message:
            err = StringIO('')
            traceback.print_exc(file=err)
            logging.error(google_user.jid + ' List:\n' + err.getvalue())
      if google_user.display_timeline & MODE_MENTION:
        try:
          statuses = api._process_result(mention_rpc)
          if statuses:
            all_statuses.extend(statuses)
          if not google_user.display_timeline & MODE_HOME:
            try:
              home_statuses = api._process_result(home_rpc)
            except twitter.TwitterInternalServerError:
              pass
            except BaseException:
              err = StringIO('')
              traceback.print_exc(file=err)
              logging.error(google_user.jid + ' Home:\n' + err.getvalue())
            else:
              if home_statuses:
                if home_statuses[0]['id'] > google_user.last_mention_id:
                  google_user.last_mention_id = home_statuses[0]['id']
                at_username = '@' + google_user.enabled_user
                home_mention_statuses = [x for x in home_statuses if at_username in x['text']]
              if home_mention_statuses:
                all_statuses.extend(home_mention_statuses)
              if home_statuses and home_statuses[0]['id'] > google_user.last_mention_id:
                google_user.last_mention_id = home_statuses[0]['id']
              if statuses and statuses[0]['id'] > google_user.last_mention_id:
                google_user.last_mention_id = statuses[0]['id']
        except twitter.TwitterInternalServerError:
          pass
        except BaseException:
          err = StringIO('')
          traceback.print_exc(file=err)
          logging.error(google_user.jid + ' Mention:\n' + err.getvalue())
      if all_statuses:
        all_statuses.sort(cmp=lambda x, y: cmp(x['id'], y['id']))
        last = all_statuses[-1]['id']
        for i in range(len(all_statuses) - 2, -1, -1):
          if last == all_statuses[i]['id']:
            del all_statuses[i]
          else:
            last = all_statuses[i]['id']
        content = utils.parse_statuses(all_statuses, filter_self=True, reverse=False)
        if content.strip():
          IdList.flush(google_user.jid)
          xmpp.send_message(google_user.jid, content)
      if google_user.display_timeline & MODE_DM:
        try:
          statuses = api._process_result(dm_rpc)
          content = utils.parse_statuses(statuses)
          if content.strip():
            xmpp.send_message(google_user.jid, _('DIRECT_MESSAGES') + '\n\n' + content)
            if statuses[-1]['id'] > google_user.last_dm_id:
              google_user.last_dm_id = statuses[-1]['id']
        except twitter.TwitterInternalServerError:
          pass
        except BaseException:
          err = StringIO('')
          traceback.print_exc(file=err)
          logging.error(google_user.jid + ' DM:\n' + err.getvalue())
      google_user.last_update = int(time())
      Db.set_datastore(google_user)


def main():
  application = webapp.WSGIApplication([('/worker', worker_handler)])
  run_wsgi_app(application)

if __name__ == "__main__":
  main()