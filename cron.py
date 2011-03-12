#!/usr/bin/python
from db import *
from time import time
from google.appengine.api import taskqueue
from google.appengine.api import xmpp
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.runtime import DeadlineExceededError

MAX_RETRY = 3

class cron_handler(webapp.RequestHandler):
  def get(self, cron_id):
    def add_task_by_jid(jid):
      self.jids.append(jid)
      if len(self.jids) >= USERS_NUM_IN_TASK:
        flush_jids()
      if len(self.tasks) >= 100:
        flush_tasks()

    def flush_jids():
      if self.jids:
        self.tasks.append(taskqueue.Task(url='/worker', params={'jid': self.jids}))
        self.jids = list()

    def flush_tasks():
      def db_op():
        for _ in xrange(MAX_RETRY):
          try:
            self.queues[self.queue_pointer].add(self.tasks)
          except taskqueue.TransientError:
            continue
          break

      if self.tasks:
        db.run_in_transaction(db_op)
        self.tasks = list()
        self.queue_pointer = (self.queue_pointer + 1) % TASK_QUEUE_NUM

    cron_id = int(cron_id)
    self.queues = [taskqueue.Queue('fetch' + str(id)) for id in xrange(TASK_QUEUE_NUM)]
    self.queue_pointer = cron_id % TASK_QUEUE_NUM
    self.tasks = list()
    self.jids = list()
    data = GoogleUser.get_all(shard=cron_id)
    try:
      for u in data:
        if u.display_timeline or u.msg_template.strip():
          time_delta = int(time()) - u.last_update
          if time_delta >= u.interval * 60 - 30:
            try:
              flag = xmpp.get_presence(u.jid)
            except xmpp.Error:
              flag = False
            if not flag:
              continue
            Db.set_cache(u)
            add_task_by_jid(u.jid)
      flush_jids()
      flush_tasks()
    except DeadlineExceededError:
      self.response.clear()
      self.response.set_status(500)
      self.response.out.write("This operation could not be completed in time...")

def main():
  application = webapp.WSGIApplication([('/cron(\d+)', cron_handler)], debug=True)
  run_wsgi_app(application)

if __name__ == "__main__":
  main()