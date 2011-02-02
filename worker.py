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
            last_msg_id = google_user.last_msg_id
            msg_list = []
            home_statuses = []
            home_mention_statuses = []

            if google_user.display_timeline & MODE_HOME:
                home_rpc = api.get_home_timeline(since_id=last_msg_id, async=True)
            else:
                home_rpc = api.get_home_timeline(since_id=google_user.last_mention_id, async=True)
            if google_user.display_timeline & MODE_LIST:
                list_rpc = api.get_list_statuses(user=google_user.list_user, id=google_user.list_id, since_id=google_user.last_list_id, async=True)
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
                    content = utils.parse_statuses(home_statuses)
                    if content.strip():
                        msg_list.append(_('TIMELINE') + '\n\n' + content)
                        IdList.flush(google_user.jid)
                        if home_statuses[-1]['id'] > last_msg_id:
                            google_user.last_msg_id = home_statuses[-1]['id']
                except twitter.TwitterInternalServerError:
                    pass
                except BaseException:
                    err = StringIO('')
                    traceback.print_exc(file=err)
                    logging.error(google_user.jid + ' Home:\n' + err.getvalue())
            if google_user.display_timeline & MODE_LIST:
                try:
                    statuses = api._process_result(list_rpc)
                    content = utils.parse_statuses(statuses)
                    if content.strip():
                        msg_list.append(_('LIST') % (google_user.list_user + '/' + google_user.list_name) + '\n\n' + content)
                        IdList.flush(google_user.jid)
                        if statuses[-1]['id'] > google_user.last_list_id:
                            google_user.last_list_id = statuses[-1]['id']
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
                    if not google_user.display_timeline & MODE_HOME:
                        try:
                                home_statuses = api._process_result(home_rpc)
                        except twitter.TwitterInternalServerError:
                            pass
                        except BaseException:
                            err = StringIO('')
                            traceback.print_exc(file=err)
                            logging.error(google_user.jid + ' Home:\n' + err.getvalue())
                    if home_statuses:
                        if home_statuses[0]['id'] > google_user.last_mention_id:
                            google_user.last_mention_id = home_statuses[0]['id']
                        at_username = '@'+google_user.enabled_user
                        home_mention_statuses = [x for x in home_statuses if at_username in x['text']]
                    del home_statuses
                    if home_mention_statuses:
                        statuses += home_mention_statuses
                        statuses.sort(cmp=lambda x,y: cmp(x['id'], y['id']))
                        last = statuses[-1]['id']
                        for i in range(len(statuses)-2, -1, -1):
                            if last == statuses[i]['id']:
                                del statuses[i]
                            else:
                                last = statuses[i]['id']
                    content = utils.parse_statuses(statuses)
                    if content.strip():
                        msg_list.append(_('MENTIONS') + '\n\n' + content)
                        IdList.flush(google_user.jid)
                        if statuses[-1]['id'] > google_user.last_mention_id:
                            google_user.last_mention_id = statuses[-1]['id']
                except twitter.TwitterInternalServerError:
                    pass
                except BaseException:
                    err = StringIO('')
                    traceback.print_exc(file=err)
                    logging.error(google_user.jid + ' Mention:\n' + err.getvalue())
            if google_user.display_timeline & MODE_DM:
                try:
                    statuses = api._process_result(dm_rpc)
                    content = utils.parse_statuses(statuses)
                    if content.strip():
                        msg_list.append(_('DIRECT_MESSAGES') + '\n\n' + content)
                        IdList.flush(google_user.jid)
                        if statuses[-1]['id'] > google_user.last_dm_id:
                            google_user.last_dm_id = statuses[-1]['id']
                except twitter.TwitterInternalServerError:
                    pass
                except BaseException:
                    err = StringIO('')
                    traceback.print_exc(file=err)
                    logging.error(google_user.jid + ' DM:\n' + err.getvalue())

            if msg_list:
                xmpp.send_message(google_user.jid, '=================================================\n'.join(msg_list))
            google_user.last_update = int(time())
            Db.set_datastore(google_user)

def main():
    application = webapp.WSGIApplication([('/worker', worker_handler)])
    run_wsgi_app(application)

if __name__ == "__main__":
    main()