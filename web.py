#!/usr/bin/python
import os
import functools

from constant import *
from mylocale import gettext
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

class cron_handler(webapp.RequestHandler):
    def get(self):
        locales = self.request.accept_language.best_matches('en-us')
        for locale in locales:
            locale = locale.lower()
            if locale in LOCALES:
                _ = functools.partial(gettext, locale=locale)
                break
        self.response.out.write(_('WEB') % os.environ['APPLICATION_ID'])

def main():
    application = webapp.WSGIApplication([('/', cron_handler)])
    run_wsgi_app(application)

if __name__ == "__main__":
    main()