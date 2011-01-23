#!/usr/bin/python
import twitter
import utils

from db import *
from mylocale import gettext
from time import time
from google.appengine.ext import webapp
from google.appengine.api import xmpp
from google.appengine.ext.webapp.util import run_wsgi_app

class worker_handler(webapp.RequestHandler):
    def get(self):
        return

    def post(self):
        jids = self.request.get_all('jid')
        for jid in jids:
            google_user = GoogleUser.get_by_jid(jid)
            _ = lambda x: gettext(x, locale=google_user.locale)
            twitter_user = TwitterUser.get_by_twitter_name(google_user.enabled_user, google_user.jid)
            api = twitter.Api(consumer_key=config.OAUTH_CONSUMER_KEY,
                              consumer_secret=config.OAUTH_CONSUMER_SECRET,
                              access_token_key=twitter_user.access_token_key,
                              access_token_secret=twitter_user.access_token_secret)
            try:
                self._user = api.verify_credentials()
                if 'screen_name' not in self._user:
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
            last_msg_id = google_user.last_msg_id if google_user.last_msg_id else None
            last_mention_id = google_user.last_mention_id if google_user.last_mention_id else None
            last_dm_id = google_user.last_dm_id if google_user.last_dm_id else None
            last_list_id = google_user.last_list_id if google_user.last_list_id else None

            if google_user.display_timeline & MODE_DM:
                try:
                    statuses = api.get_direct_messages(since_id=last_dm_id)
                    content = utils.parse_statuses(statuses)
                    if content.strip():
                        xmpp.send_message(google_user.jid, _('DIRECT_MESSAGES') + '\n\n' + content)
                        IdList.flush(google_user.jid)
                        if statuses[-1]['id'] > last_dm_id:
                            google_user.last_dm_id = statuses[-1]['id']
                except BaseException:
                    err = cStringIO.StringIO('')
                    traceback.print_exc(file=err)
                    logging.error(google_user.jid + ' DM:\n' + err.getvalue())

            if google_user.display_timeline & MODE_MENTION:
                try:
                    statuses = api.get_mentions(since_id=last_mention_id)
                    content = utils.parse_statuses(statuses)
                    if content.strip():
                        xmpp.send_message(google_user.jid, _('MENTIONS') + '\n\n' + content)
                        IdList.flush(google_user.jid)
                        if statuses[-1]['id'] > last_mention_id:
                            google_user.last_mention_id = statuses[-1]['id']
                except BaseException:
                    err = cStringIO.StringIO('')
                    traceback.print_exc(file=err)
                    logging.error(google_user.jid + ' Mention:\n' + err.getvalue())

            if google_user.display_timeline & MODE_HOME:
                try:
                    statuses = api.get_home_timeline(since_id=last_msg_id)
                    content = utils.parse_statuses(statuses)
                    if content.strip():
                        xmpp.send_message(google_user.jid, _('TIMELINE') + '\n\n' + content)
                        IdList.flush(google_user.jid)
                        if statuses[-1]['id'] > last_msg_id:
                            google_user.last_msg_id = statuses[-1]['id']
                except BaseException:
                    err = cStringIO.StringIO('')
                    traceback.print_exc(file=err)
                    logging.error(google_user.jid + ' Home:\n' + err.getvalue())

            if google_user.display_timeline & MODE_LIST:
                try:
                    statuses = api.get_list_statuses(user=google_user.list_user, id=google_user.list_id, since_id=last_list_id)
                    content = utils.parse_statuses(statuses)
                    if content.strip():
                        xmpp.send_message(google_user.jid, _('LIST') % (google_user.list_user + '/' + google_user.list_name) + '\n\n' + content)
                        IdList.flush(google_user.jid)
                        if statuses[-1]['id'] > last_list_id:
                            google_user.last_list_id = statuses[-1]['id']
                except BaseException, e:
                    if 'Not found' not in e.message:
                        err = cStringIO.StringIO('')
                        traceback.print_exc(file=err)
                        logging.error(google_user.jid + ' List:\n' + err.getvalue())
            google_user.last_update = int(time())
            Db.set_datastore(google_user)

def main():
    application = webapp.WSGIApplication([('/worker', worker_handler)])
    run_wsgi_app(application)

if __name__ == "__main__":
    main()