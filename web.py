#!/usr/bin/python
import os

from mylocale import gettext, LOCALES
from functools import partial
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

class cron_handler(webapp.RequestHandler):
  def get(self):
    _ = gettext
    locales = self.request.accept_language.best_matches('en-us')
    for locale in locales:
      locale = locale.lower()
      if locale in LOCALES:
        _ = partial(gettext, locale=locale)
        break
    self.response.out.write(_('WEB') % os.environ['APPLICATION_ID'])

  def head(self):
    return

  def post(self):
    return


class wave_handler(webapp.RequestHandler):
  def get(self, *args):
    return

  def head(self, *args):
    return

  def post(self, *args):
    return


def main():
  application = webapp.WSGIApplication([('/', cron_handler),
                                        ('/_wave/robot/profile', wave_handler)])
  run_wsgi_app(application)

if __name__ == "__main__":
  main()