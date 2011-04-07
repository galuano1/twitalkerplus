#!/usr/bin/python
import twitter
import config
import utils
import logging
import traceback
from mylocale import gettext
from time import time
from StringIO import StringIO
from google.appengine.api import xmpp
from google.appengine.api.capabilities import CapabilitySet
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.runtime.apiproxy_errors import DeadlineExceededError, CapabilityDisabledError
from db import Db, GoogleUser, TwitterUser, IdList, Session, MODE_HOME, MODE_LIST, MODE_MENTION, MODE_DM

class cron_handler(webapp.RequestHandler):
  def get(self, cron_id):
    cron_id = int(cron_id)
    data = Session.get_all(shard=cron_id)
    for u in data:
      jid = u.key().name()
      try:
        self.process(u)
      except CapabilityDisabledError:
        xmpp.send_presence(jid, presence_show=xmpp.PRESENCE_SHOW_AWAY)
      else:
        xmpp.send_presence(jid)

  def process(self, u):
      jid = u.key().name()
      try:
        flag = xmpp.get_presence(jid)
      except (xmpp.Error, DeadlineExceededError):
        flag = True
      if not flag:
        u.delete()
        return
      google_user = GoogleUser.get_by_jid(jid)
      if google_user is None:
        u.delete()
        return
      time_delta = int(time()) - google_user.last_update
      if time_delta < google_user.interval * 60 - 30:
        return
      _ = lambda x: gettext(x, locale=google_user.locale)
      twitter_user = TwitterUser.get_by_twitter_name(google_user.enabled_user, google_user.jid)
      if twitter_user is None:
        google_user.enabled_user = ''
        Db.set_datastore(google_user)
        return
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
        return
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
      at_username = '@' + google_user.enabled_user

      if google_user.display_timeline & MODE_HOME or google_user.display_timeline & MODE_MENTION:
        home_rpc = api.get_home_timeline(since_id=google_user.last_msg_id, async=True)
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
      if google_user.display_timeline & MODE_MENTION:
        try:
          statuses = api._process_result(mention_rpc)
          if statuses:
            all_statuses.extend(statuses)
            if statuses[0]['id'] > google_user.last_mention_id:
              google_user.last_mention_id = statuses[0]['id']
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
                if home_statuses[0]['id'] > google_user.last_msg_id:
                  google_user.last_msg_id = home_statuses[0]['id']
                home_mention_statuses = [x for x in home_statuses if
                                         at_username in x['text'] and x['id'] > google_user.last_mention_id]
              if home_mention_statuses:
                all_statuses.extend(home_mention_statuses)
        except twitter.TwitterInternalServerError:
          pass
        except BaseException:
          err = StringIO('')
          traceback.print_exc(file=err)
          logging.error(google_user.jid + ' Mention:\n' + err.getvalue())
      if google_user.display_timeline & MODE_LIST:
        try:
          statuses = api._process_result(list_rpc)
          if statuses:
            if statuses[0]['id'] > google_user.last_list_id:
              google_user.last_list_id = statuses[0]['id']
            for i in range(len(statuses) - 1, -1, -1):
              if at_username in statuses[i]['text'] and statuses[i]['id'] <= google_user.last_mention_id:
                del statuses[i]
            all_statuses.extend(statuses)
        except twitter.TwitterInternalServerError:
          pass
        except BaseException, e:
          if 'Not found' not in e.message:
            err = StringIO('')
            traceback.print_exc(file=err)
            logging.error(google_user.jid + ' List:\n' + err.getvalue())
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
          while CapabilitySet('xmpp').is_enabled():
            try:
              xmpp.send_message(google_user.jid, content)
            except xmpp.Error:
              pass
            else:
              break
      if google_user.display_timeline & MODE_DM:
        try:
          statuses = api._process_result(dm_rpc)
          content = utils.parse_statuses(statuses)
          if content.strip():
            while CapabilitySet('xmpp').is_enabled():
              try:
                xmpp.send_message(google_user.jid, _('DIRECT_MESSAGES') + '\n\n' + content)
              except xmpp.Error:
                pass
              else:
                break
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
  application = webapp.WSGIApplication([('/cron(\d+)', cron_handler)], debug=True)
  run_wsgi_app(application)

if __name__ == "__main__":
  main()