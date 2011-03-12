#!/usr/bin/python
import config

def gettext(message, locale=config.DEFAULT_LANGUAGE):
  if locale not in globals():
    __import__('mylocale.' + locale)
  str_list = globals()[locale].str_list
  if message in str_list:
    translated_message = str_list[message]
  else:
    if config.DEFAULT_LANGUAGE in globals():
      __import__('mylocale.' + config.DEFAULT_LANGUAGE)
    str_list = globals()[config.DEFAULT_LANGUAGE].str_list
    translated_message = str_list[message] if message in str_list else message
  return translated_message
