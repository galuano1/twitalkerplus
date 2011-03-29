#!/usr/bin/python
import datetime
import urllib
import urllib2
import oauth
import urlparse
import simplejson

from db import *
from email.utils import parsedate
from google.appengine.api import urlfetch
from google.appengine.api import memcache

CHARACTER_LIMIT = 140

REQUEST_TOKEN_URL = 'https://api.twitter.com/oauth/request_token'

ACCESS_TOKEN_URL = 'https://api.twitter.com/oauth/access_token'

AUTHORIZATION_URL = 'https://api.twitter.com/oauth/authorize'

SIGNIN_URL = 'https://api.twitter.com/oauth/authenticate'

BASE_URL = 'https://api.twitter.com/1'

class TwitterError(Exception):
  pass


class TwitterAuthenticationError(TwitterError):
  pass


class TwitterInternalServerError(TwitterError):
  pass


class Api(object):
  def __init__(self, consumer_key=None, consumer_secret=None, access_token_key=None, access_token_secret=None,
               input_encoding=None, request_headers=None, base_url=None):
    self._urllib = urllib2
    self._input_encoding = input_encoding
    self._oauth_consumer = None
    self._initialize_request_headers(request_headers)
    if base_url is None:
      self.base_url = BASE_URL
    else:
      self.base_url = base_url
    self.set_credentials(consumer_key, consumer_secret, access_token_key, access_token_secret)

  def set_credentials(self, consumer_key, consumer_secret, access_token_key=None, access_token_secret=None):
    self._consumer_key = consumer_key
    self._consumer_secret = consumer_secret
    self._access_token_key = access_token_key
    self._access_token_secret = access_token_secret
    self._oauth_consumer = None
    if consumer_key is not None and consumer_secret is not None\
       and access_token_key is not None and access_token_secret is not None:
      self._signature_method_hmac_sha1 = oauth.SignatureMethod_HMAC_SHA1()
      self._oauth_token = oauth.Token(key=access_token_key, secret=access_token_secret)
      self._oauth_consumer = oauth.Consumer(key=consumer_key, secret=consumer_secret)

  def clear_credentials(self):
    self._consumer_key = None
    self._consumer_secret = None
    self._access_token_key = None
    self._access_token_secret = None
    self._oauth_consumer = None

  def get_home_timeline(self, page=None, since_id=None, include_rts=1, include_entities=1, async=False):
    parameters = {}
    if page:
      parameters['page'] = page
    if since_id:
      parameters['since_id'] = since_id
    if include_rts:
      parameters['include_rts'] = 1
    if include_entities:
      parameters['include_entities'] = 1
    url = '%s/statuses/home_timeline.json' % self.base_url
    return self._fetch_url(url, parameters=parameters, async=async)

  def get_friends_timeline(self, count=None, page=None, since_id=None, retweets=1, include_entities=1):
    url = '%s/statuses/friends_timeline.json' % self.base_url
    parameters = {}
    if count:
      parameters['count'] = count
    if page:
      parameters['page'] = int(page)
    if since_id:
      parameters['since_id'] = since_id
    if retweets:
      parameters['include_rts'] = 1
    if include_entities:
      parameters['include_entities'] = 1
    return self._fetch_url(url, parameters=parameters)

  def get_user_timeline(self, user_id=None, screen_name=None, since_id=None, max_id=None, count=None,
                        page=None, include_rts=1, include_entities=1):
    parameters = {}
    url = '%s/statuses/user_timeline.json' % self.base_url
    if user_id:
      parameters['user_id'] = user_id
    elif screen_name:
      parameters['screen_name'] = screen_name
    if since_id:
      parameters['since_id'] = long(since_id)
    if max_id:
      parameters['max_id'] = long(max_id)
    if count:
      parameters['count'] = int(count)
    if page:
      parameters['page'] = int(page)
    if include_rts:
      parameters['include_rts'] = 1
    if include_entities:
      parameters['include_entities'] = 1
    return self._fetch_url(url, parameters=parameters)

  def get_status(self, id, include_entities=1):
    data = memcache.get(str(id), namespace='status')
    if data is None:
      url = '%s/statuses/show/%s.json' % (self.base_url, id)
      parameters = dict()
      if include_entities:
        parameters['include_entities'] = 1
      data = self._fetch_url(url, parameters=parameters)
    return data

  def destroy_status(self, id):
    url = '%s/statuses/destroy/%s.json' % (self.base_url, id)
    return self._fetch_url(url, post_data={'id': id})

  def post_update(self, status, in_reply_to_status_id=None):
    url = '%s/statuses/update.json' % self.base_url
    data = {'status': status.encode('UTF-8')}
    if in_reply_to_status_id:
      data['in_reply_to_status_id'] = in_reply_to_status_id
    data = self._fetch_url(url, post_data=data)
    Db.set_cache(data)
    return data

  def get_user_retweets(self, count=None, since_id=None, include_entities=1):
    url = '%s/statuses/retweeted_by_me.json' % self.base_url
    parameters = {}
    if count:
      parameters['count'] = count
    if since_id:
      parameters['since_id'] = since_id
    if include_entities:
      parameters['include_entities'] = 1
    return self._fetch_url(url, parameters=parameters)

  def get_retweets(self, statusid):
    url = '%s/statuses/retweets/%s.json' % (self.base_url, statusid)
    parameters = {'include_entities': 1, 'include_rts': 1}
    return self._fetch_url(url, parameters=parameters)

  def get_friends(self, user=None, cursor=-1):
    parameters = {'cursor': cursor}
    url = '%s/statuses/friends.json' % self.base_url
    if user:
      parameters['screen_name'] = user
    return self._fetch_url(url, parameters=parameters)

  def get_friend_IDs(self, user=None, cursor=-1):
    url = '%s/friends/ids.json' % self.base_url
    parameters = {'cursor': cursor}
    if user:
      parameters['screen_name'] = user
    return self._fetch_url(url, parameters=parameters)

  def get_follower_IDs(self, userid=None, cursor=-1):
    url = 'http://twitter.com/followers/ids.json'
    parameters = {'cursor': cursor}
    if userid:
      parameters['user_id'] = userid
    json = self._fetch_url(url, parameters=parameters)
    return json

  def get_followers(self, page=None):
    url = '%s/statuses/followers.json' % self.base_url
    parameters = {}
    if page:
      parameters['page'] = page
    return self._fetch_url(url, parameters=parameters)

  def users_lookup(self, user_id=None, screen_name=None, users=None):
    url = '%s/users/lookup.json' % self.base_url
    parameters = {}
    uids = list()
    if user_id:
      uids.extend(user_id)
    if users:
      uids.extend([u.id for u in users])
    if len(uids):
      parameters['user_id'] = ','.join(["%s" % u for u in uids])
    if screen_name:
      parameters['screen_name'] = ','.join(screen_name)
    return self._fetch_url(url, parameters=parameters)

  def get_user(self, user):
    url = '%s/users/show/%s.json' % (self.base_url, user)
    return self._fetch_url(url)

  def get_direct_messages(self, since_id=None, page=None, include_entities=1, async=False):
    url = '%s/direct_messages.json' % self.base_url
    parameters = {}
    if since_id:
      parameters['since_id'] = since_id
    if page:
      parameters['page'] = page
    if include_entities:
      parameters['include_entities'] = include_entities
    return self._fetch_url(url, parameters=parameters, async=async)

  def post_direct_message(self, user, text):
    url = '%s/direct_messages/new.json' % self.base_url
    data = {'text': text.encode('UTF-8'), 'user': user}
    return self._fetch_url(url, post_data=data)

  def destroy_direct_message(self, id):
    url = '%s/direct_messages/destroy/%s.json' % (self.base_url, id)
    return self._fetch_url(url, post_data={'id': id})

  def create_friendship(self, user):
    url = '%s/friendships/create.json' % self.base_url
    return self._fetch_url(url, parameters={'screen_name': user}, http_method='POST')

  def destroy_friendship(self, user):
    url = '%s/friendships/destroy.json' % self.base_url
    return self._fetch_url(url, parameters={'screen_name': user}, http_method='POST')

  def exists_friendship(self, user_a, user_b):
    url = '%s/friendships/exists.json' % self.base_url
    return self._fetch_url(url, parameters={'user_a': user_a, 'user_b': user_b})

  def create_favorite(self, id):
    url = '%s/favorites/create/%s.json' % (self.base_url, id)
    return self._fetch_url(url, post_data={'id': id})

  def destroy_favorite(self, id):
    url = '%s/favorites/destroy/%s.json' % (self.base_url, id)
    return self._fetch_url(url, post_data={'id': id})

  def get_favorites(self, user=None, page=None):
    parameters = {}
    if page:
      parameters['page'] = page
    if user:
      url = '%s/favorites/%s.json' % (self.base_url, user)
    else:
      url = '%s/favorites.json' % self.base_url
    return self._fetch_url(url, parameters=parameters)

  def get_mentions(self, since_id=None, max_id=None, page=None, include_entities=1, async=False):
    url = '%s/statuses/mentions.json' % self.base_url
    parameters = {}
    if since_id:
      parameters['since_id'] = since_id
    if max_id:
      parameters['max_id'] = max_id
    if page:
      parameters['page'] = page
    if include_entities:
      parameters['include_entities'] = include_entities
    return self._fetch_url(url, parameters=parameters, async=async)

  def create_list(self, user, name, mode=None, description=None):
    url = '%s/%s/lists.json' % (self.base_url, user)
    parameters = {'name': name}
    if mode is not None:
      parameters['mode'] = mode
    if description is not None:
      parameters['description'] = description
    return self._fetch_url(url, post_data=parameters)

  def destroy_list(self, user, id):
    url = '%s/%s/lists/%s.json' % (self.base_url, user, id)
    return self._fetch_url(url, post_data={'_method': 'DELETE'})

  def create_retweet(self, id):
    url = '%s/statuses/retweet/%s.json' % (self.base_url, id)
    return self._fetch_url(url, post_data={'id': id})

  def create_subscription(self, owner, list):
    url = '%s/%s/%s/subscribers.json' % (self.base_url, owner, list)
    return self._fetch_url(url, post_data={'list_id': list})

  def destroy_subscription(self, owner, list):
    url = '%s/%s/%s/subscribers.json' % (self.base_url, owner, list)
    return self._fetch_url(url, post_data={'_method': 'DELETE', 'list_id': list})

  def get_subscriptions(self, user, cursor=-1):
    if not self._oauth_consumer:
      raise TwitterError("twitter.Api instance must be authenticated")

    url = '%s/%s/lists/subscriptions.json' % (self.base_url, user)
    parameters = {'cursor': cursor}
    return self._fetch_url(url, parameters=parameters)

  def get_lists(self, user, cursor=-1):
    url = '%s/%s/lists.json' % (self.base_url, user)
    parameters = {'cursor': cursor}
    return self._fetch_url(url, parameters=parameters)

  def get_list(self, user, id):
    url = '%s/%s/lists/%s.json' % (self.base_url, user, id)
    return self._fetch_url(url)

  def get_list_statuses(self, user, id, since_id=None, max_id=None, page=None, include_entities=1, async=False):
    url = '%s/%s/lists/%s/statuses.json' % (self.base_url, user, id)
    parameters = {}
    if since_id:
      parameters['since_id'] = since_id
    if max_id:
      parameters['max_id'] = max_id
    if page:
      parameters['page'] = page
    if include_entities:
      parameters['include_entities'] = include_entities
    return self._fetch_url(url, parameters=parameters, async=async)

  def create_block(self, user):
    url = '%s/blocks/create.json' % self.base_url
    return self._fetch_url(url, parameters={'screen_name': user}, http_method='POST')

  def report_spam(self, user):
    url = '%s/report_spam.json' % self.base_url
    return self._fetch_url(url, parameters={'screen_name': user}, http_method='POST')

  def destroy_block(self, user):
    url = '%s/blocks/destroy.json' % self.base_url
    return self._fetch_url(url, parameters={'screen_name': user}, http_method='POST')


  def verify_credentials(self):
    '''Returns a twitter.User instance if the authenticating user is valid.

    Returns:
        A twitter.User instance representing that user if the
        credentials are valid, None otherwise.
    '''
    url = '%s/account/verify_credentials.json' % self.base_url
    return self._fetch_url(url)

  def set_x_twitter_headers(self, client, url, version):
    self._request_headers['X-Twitter-Client'] = client
    self._request_headers['X-Twitter-Client-URL'] = url
    self._request_headers['X-Twitter-Client-Version'] = version

  def get_rate_limit_status(self):
    url = '%s/account/rate_limit_status.json' % self.base_url
    return self._fetch_url(url)

  def maximum_hit_frequency(self):
    rate_status = self.get_rate_limit_status()
    reset_time = rate_status.get('reset_time', None)
    limit = rate_status.get('remaining_hits', None)
    if reset_time and limit:
      reset = datetime.datetime(*parsedate(reset_time)[:7])
      delta = reset + datetime.timedelta(hours=1) - datetime.datetime.utcnow()
      max_frequency = int(delta.seconds / limit)
      return max_frequency
    return 0

  def _build_url(self, url, path_elements=None, extra_params=None):
    (scheme, netloc, path, params, query, fragment) = urlparse.urlparse(url)
    if path_elements:
      p = [i for i in path_elements if i]
      if not path.endswith('/'):
        path += '/'
      path += '/'.join(p)
    if extra_params and len(extra_params) > 0:
      extra_query = self._encode_parameters(extra_params)
      if query:
        query += '&' + extra_query
      else:
        query = extra_query
    return urlparse.urlunparse((scheme, netloc, path, params, query, fragment))

  def _initialize_request_headers(self, request_headers):
    if request_headers:
      self._request_headers = request_headers
    else:
      self._request_headers = {}

  def _encode(self, s):
    if self._input_encoding:
      return unicode(s, self._input_encoding).encode('utf-8')
    else:
      return unicode(s).encode('utf-8')

  def _encode_parameters(self, parameters):
    if parameters is None:
      return None
    else:
      return urllib.urlencode(dict([(k, self._encode(v)) for k, v in parameters.items() if v is not None]))

  def _encode_post_data(self, post_data):
    if post_data is None:
      return None
    else:
      return urllib.urlencode(dict([(k, self._encode(v)) for k, v in post_data.items()]))

  def _check_for_twitter_error(self, data):
    if type(data) == dict and 'error' in data:
      if 'Could not authenticate' in data['error']:
        raise TwitterAuthenticationError(data['error'])
      raise TwitterError(data['error'])

  def _fetch_url(self, url, post_data=None, parameters=None, http_method='GET', async=False):
    extra_params = {}
    if parameters is not None:
      extra_params.update(parameters)
    if post_data:
      http_method = "POST"
    headers = {'Accept-Encoding': 'gzip'}
    if self._oauth_consumer is not None:
      if post_data and http_method == "POST":
        parameters = post_data.copy()
      req = oauth.Request.from_consumer_and_token(self._oauth_consumer, token=self._oauth_token,
                                                  http_method=http_method, http_url=url,
                                                  parameters=parameters)
      req.sign_request(self._signature_method_hmac_sha1, self._oauth_consumer, self._oauth_token)
      if http_method == "POST":
        encoded_post_data = req.to_postdata()
      else:
        encoded_post_data = None
        url = req.to_url()
    else:
      url = self._build_url(url, extra_params=extra_params)
      encoded_post_data = self._encode_post_data(post_data)
    rpc = urlfetch.create_rpc()
    urlfetch.make_fetch_call(rpc, url, payload=encoded_post_data, method=http_method, headers=headers)
    if async:
      return rpc
    else:
      return self._process_result(rpc)

  def _process_result(self, rpc):
    try:
      response = rpc.get_result()
    except Exception:
      return None
    try:
      json = simplejson.loads(response.content)
    except ValueError:
      return None
    except BaseException, e:
      if '500 Internal Server Error' in response.content:
        raise TwitterInternalServerError('500 Internal Server Error')
      else:
        raise TwitterError(e.message)
    self._check_for_twitter_error(json)
    return json
