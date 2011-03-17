import urllib

from twitter import SIGNIN_URL
from xml.dom import minidom
from google.appengine.api import urlfetch

def login_oauth(web_url, username, password):
  try:
    result = urlfetch.fetch(web_url)
  except urlfetch.Error:
    return ''
  dom = minidom.parseString(result.content)
  inputs = dom.getElementsByTagName('input')
  authenticity_token = ''
  oauth_token = ''
  for input in inputs:
    attr = input.getAttribute('name')
    if attr == 'authenticity_token':
      authenticity_token = input.getAttribute('value')
    elif attr == 'oauth_token':
      oauth_token = input.getAttribute('value')
    if authenticity_token and oauth_token:
      break
  str = urllib.urlencode({'authenticity_token': authenticity_token, 'oauth_token': oauth_token,
                          'session[username_or_email]': username, 'session[password]': password})
  try:
    result = urlfetch.fetch(SIGNIN_URL, str, urlfetch.POST)
  except urlfetch.Error:
    return ''
  dom = minidom.parseString(result.content)
  divs = dom.getElementsByTagName('div')
  oauth_pin = None
  for div in divs:
    if div.getAttribute('id') == 'oauth_pin':
      for node in div.childNodes:
        if node.nodeType == node.TEXT_NODE:
          oauth_pin = node.data.strip()
          break
      break
  return oauth_pin