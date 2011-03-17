#!/usr/bin/python
# -*- encoding: utf-8 -*-
str_list = {
  'WEB': '<html><head><title>TwiTalkerPlus</title></head><body>Please add <b>%s@appspot.com</b> as your GTalk friend, then use -oauth command to authenticate.<br />More info please refer to -help command.<br /><a href="http://twitter.com/gh05tw01f">Author</a>&nbsp;<a href="https://github.com/gh05tw01f/twitalkerplus">Source</a></body></html>'
  ,
  'NO_AUTHENTICATION': 'No authentication for your Twitter',
  'INTERNAL_SERVER_ERROR': 'Twitter Internal Server Error!',
  'TIMELINE': '*Timeline:* ',
  'MENTIONS': '*Mentions:* ',
  'DIRECT_MESSAGES': '*Direct Messages:* ',
  'LIST': '*%s List:* ',
  'SUCCESSFULLY_REPLY_TO': 'Successfully reply to %s',
  'SUCCESSFULLY_UPDATE_STATUS': 'Successfully update status',
  'PAGE': 'Page %s',
  'STATUS_NOT_FOUND': 'Status %s not found',
  'WORDS_COUNT_EXCEED': 'Words count %s exceeed %s characters.',
  'STATUS_DUPLICATE': 'Status duplicate.',
  'STATUSES_CONVERSATION': '*Statuses conversation:*',
  'INVALID_COMMAND': 'Invalid command.',
  'INTERVAL': 'Interval is %s minute(s).',
  'MESSAGE_TO_NOT_FOLLOWED': 'You cannot send messages to users who are not following you.',
  'SUCCESSFULLY_MESSAGE': 'Successfully send message to %s :)',
  'ALREADY_FOLLOWED': 'You have already followed %s :)',
  'BLOCKED': 'You have been blocked by %s :(',
  'SUCCESSFULLY_FOLLOW': 'Successfully followed %s :)',
  'SUCCESSFULLY_UNFOLLOW': 'Successfully unfollowed %s',
  'USER_NOT_FOUND': 'User %s not Found.',
  'FOLLOWING_YOU': '%s is following you :)',
  'NOT_FOLLOWING_YOU': '%s is not following you :(',
  'SUCCESSFULLY_BLOCK': 'Successfully block %s',
  'SUCCESSFULLY_UNBLOCK': 'Successfully unblock %s',
  'STATUS_DELETED': 'Status %s is deleted, content is:\n%s',
  'DELETE_ANOTHER_USER_STATUS': "You may not delete another user's status.",
  'ON_MODE': 'You turned on update for %s.\nAll parts are list, home, mention, dm.',
  'LIVE_MODE': 'List of live mode is assigned with list %s.',
  'USE_LIVE': 'Please first set list used in LIVE mode with live command.',
  'LIST_NOT_FOUND': 'List %s is not found.',
  'FAVOURITED': 'Status %s is favorited :)',
  'UNFAVOURITED': 'Status %s is unfavorited.',
  'FAVOURITES': '*Favorites:* ',
  'USER_TIMELINE': '*User %s Timeline:* ',
  'SUCCESSFULLY_RETWEET': 'Successfully retweet %s :)',
  'SUCCESSFULLY_RT': 'Successfully RT %s as following: :)\n%s',
  'CURRENT_TIMEZONE': 'Your current timezone is %s',
  'INVALID_TIMEZONE': 'Timezone is invalid.',
  'SET_TIMEZONE_SUCCESSFULLY': 'Successfully set your timezone :)',
  'INVALID_LOCALE': 'Invalid or non-existent language.',
  'CURRENT_LOCALE': u'Current language is %s',
  'SET_LOCALE_SUCCESSFULLY': 'Successfully set your language :)',
  'RETWEET_MODE': 'Official retweets now will be displayed in retweet style.',
  'RT_MODE': 'Official retweets now will be displayed in RT style.',
  'BOLD_MODE_ON': 'Username will be bold.',
  'BOLD_MODE_OFF': 'Username will not be bold.',
  'MSG_TEMPLATE': 'Status template is\n%s',
  'DATE_TEMPLATE': 'Date format is\n%s',
  'NOW_USING': 'Now you are using %s.',
  'ALL_TWITTER_USERS_NAME': 'All twitter users associated with your Google account are listed below:\n%s',
  'ENABLED_TWITTER_USER_CHANGED': 'Now enabled twitter user of your Google account is %s',
  'NOT_ASSOCIATED_TWITTER_USER': 'Twitter user is not associated with your account.',
  'PROTECTED_USER': 'Protected user or suspended user.',
  'USER_PROFILE': '$screen_name ( $name ) Profile:\nAvatar URL:$profile_image_url\nWeb: $url\nLocation: $location\nTweets: $statuses_count\nFollowing: $friends_count\nFollowed: $followers_count\nBio: $description\nLatest Tweet: $status\n$following'
  ,
  'YOU_FOLLOWING': 'You have followed %s.',
  'YOU_HAVE_REQUESTED': 'You have sent follow request to %s.',
  'YOU_DONT_FOLLOW': 'You don\'t follow %s.',
  'COMMAND_PREFIX': 'Command prefix is %s',
  'TWITTER_USER_DELETED': '%s is not associated with you anymore. ',
  'SPECIFY_ANOTHER_USER': 'Please specify another twitter user with "switch" command.',
  'OAUTH_URL': 'Please visit below url to get PIN code:\n%s\nthen you should use "-bind PIN" command to actually bind your Twitter.'
  ,
  'INVALID_PIN_CODE': 'Invalid PIN code %s.',
  'SUCCESSFULLY_BIND': 'Successfully bind you with Twitter user %s.',
  'NETWORK_ERROR': 'Network error.',
  'WRONG_USER_OR_PASSWORD': 'Wrong username or password.',
  'ALL_COMMANDS': """Now TwiTalkerPlus supports following commands, you can use -?/-h/-help COMMAND to look up details(arguments in brackets are optional):
    Operations:
    -@/-r-/-reply: reply to status
    -d/-dm: send direct message or view direct message
    -rt: RT status
    -re: official retweet status
    -ra: replay to all for status
    -m/-msg: view conversation for status
    -u/-user: view user
    -del: del status
    -ho/-home: view home timeline
    -tl/-timeline: view user's timeline
    -lt/-list: view list's statuses
    -f/-fav: favorite status or view favorites
    -uf/-unfav: unfavorite status
    -fo/-follow: follow user
    -unfo/-unfollow: unfollow user
    -if: determine whether user follow you
    -b/-block: block user
    -ub/-unblock: unblock user
    Settings:
    -on: view or turn on updates
    -off: view or turn off updates
    -live: specify list of live
    -s/-switch: switch among users
    -time: change time interval
    -msgtpl: change message template
    -datefmt: change date format
    -retweet: toggle retweet display
    -locale: change language
    -timezone: change timezone
    -bold: toggle bold
    -prefix: change prefix
    Authentication:
    -oauth: start oauth authentication
    -bind: bind user
    -remove: remove twitter user
    Help:
    -?/-h/-help: show this help
    If you find some bug, please contact me @gh05tw01f, thx~
    """,
  'HELP_OAUTH': 'USAGE: -oauth [username password[\nGet OAuth authorization url to grant PIN code. If you supply username and password, it can help you bypass oauth.'
  ,
  'HELP_BIND': 'USAGE: -bind PIN_CODE\nSupply PIN code from Twitter after using -oauth and visiting url so TwiTalkerPlus will bind you with your Twitter account.'
  ,
  'HELP_REMOVE': 'USAGE: -remove [username[\nRemove relation between twitter account and you. If username is not given, current twitter username will be used instead.'
  ,
  'HELP_ON': 'USAGE: -on [PART]\nTurn on part of notifications. If part is not given, show what part are turned on.',
  'HELP_OFF': 'USAGE: -off [PART]\nTurn off part of notifications. If part is not given, show what part are turned on.',
  'HELP_LIVE': 'USAGE: -live [LISTNAME]\nSpecify list for live update. You should give listname to specify list you want to monitor. Listname accepts following format:\ngh05tw01f joke\ngh05tw01f/joke\njoke (this will use your own username instead). \nIf listname is not given, display current list instead.'
  ,
  'HELP_REPLY': 'USAGE(1): -r/-@/-reply ID CONTENT\nReply given-ID status. ID can be a long ID like 2866000224794214 or a short id like #12. Pound is NOT necessary for short id.\nUSAGE(2): -r/-@/-reply [p4]\nFetch mentions and display for you. p4 means page 4 which is not necessary.'
  ,
  'HELP_DM': 'USAGE(1): -d/-dm USERNAME CONTENT\nPost direct message to specified user with content.\nUSAGE(2): -d/-dm p4\nFetch direct messages and display for you. p4 means page 4 which is NOT necessary.'
  ,
  'HELP_RT': 'USAGE: -rt ID [CONTENT]\nRT status with you content. ID can be a long ID like 2866000224794214 or a short id like #12. Pound is NOT necessary for short id. Words exceed 140 will be TRIMED OFF!'
  ,
  'HELP_RE': 'USAGE: -re ID\nRT status with official retweet. CAN NOT APPEND COMMENT.',
  'HELP_RA': 'USAGE: -ra ID CONTENT\nReply given-ID status with all users mentioned. ID can be a long ID like 2866000224794214 or a short id like #12. Pound is NOT necessary for short id.'
  ,
  'HELP_MSG': 'USAGE: -m/-msg ID\nDisplay tweet converson for specified ID. ID can be a long ID like 2866000224794214 or a short id like #12. Pound is NOT necessary for short id.'
  ,
  'HELP_USER': 'USAGE: -u/-user [username]\nDisplay information of specified user. If username is not given, your current twitter username will be used instead.'
  ,
  'HELP_DEL': 'USAGE: -del [ID]\nDelete specified status. ID can be a long ID like 2866000224794214 or a short id like #12. If ID is not given, it will delete your most recent status. \nWARNING: it DOES NOT encourage you use -del repeated to delete all your status, no-id usage is just an emergency method for wrong status.'
  ,
  'HELP_HOME': 'USAGE: -home [p4]\nFetch timeline and display for you. p4 means page 4 which is not necessary.',
  'HELP_TIMELINE': 'USAGE: -tl/-timeline [USERNAME] [p4]\nFetch specified user\'s timeline and display for you. p4 means page 4 which is not necessary. If username is not given, will use your own username instead.'
  ,
  'HELP_LIST': 'USAGE: -lt/-list [LISTNAME]\nFetch speicied list and display all statuses of it for you. p4 means page 4 which is not necessary.\nListname accepts following format:\ngh05tw01f joke\ngh05tw01f/joke\njoke (this will use your own username instead).'
  ,
  'HELP_FAV': 'USAGE(1): -f/-fav ID\nFavorite given-ID status. ID can be a long ID like 2866000224794214 or a short id like #12. Pound is NOT necessary for short id.\nUSAGE(2): -f/-fav [p4]\nFetch favorites and display for you. p4 means page 4 which is not necessary.'
  ,
  'HELP_UNFAV': 'USAGE: -uf/-unfav ID\nUnfavorite give-ID status. ID can be a long ID like 2866000224794214 or a short id like #12. Pound is NOT necessary for short id.'
  ,
  'HELP_FOLLOW': 'USAGE: -fo/-follow USERNAME\nFollow specified user.',
  'HELP_UNFOLLOW': 'USAGE: -unfo/-unfollow USERNAME\nUnfollow specified user.',
  'HELP_IF': 'USAGE: -if USERNAME\nDetermine whether specified user follow you or not.',
  'HELP_BLOCK': 'USAGE: -b/-block USERNAME\nBlock specified user.',
  'HELP_UNBLOCK': 'USAGE: -ub/-unblock USERNAME\nUnblock specified user.',
  'HELP_SWITCH': 'USAGE: -s/-switch [USERNAME]\nSwitch user that relate with you. If no username is given, list all users relate to you.'
  ,
  'HELP_TIME': 'USAGE: -time [MINUTES]\nChange time interval between two updates, in minutes. If no minutes is given, display current interval instead.'
  ,
  'HELP_MSGTPL': 'USAGE: -msgtpl [TEMPLATE]\nChange status template. Currently only support keywords below\n$username -> username of status or direct message\n$content -> content of status or direct message\n$id -> long id like 2866000224794214\n$shortid -> short id like #12\n$time -> time of status or direct message, can be changed via -datefmt command\n$source -> source of status\nIt does NOT encourage you use underline after keyword because underline will also be recognized as one part of keyword.\nYou can use one or multiple \\n in the end of template to announce a blank line.\nIf template string is not given, display current template instead.'
  ,
  'HELP_DATEFMT': 'USAGE: -datefmt [FORMAT]\nChange datetime format. Format should follow principle below:\nhttp://docs.python.org/release/2.5.4/lib/module-time.html#l2h-2826\nIf format is not given, display current format instead.'
  ,
  'HELP_RETWEET': 'USAGE: -retweet [VALUE]\nToggle display of official retweet in two mode: 1) like normal status, no showing who retweets and username is user\'s name of original tweet. 2) like traditional RT, showing who retweet this and username is his username.\nValue accepts following:\n1) yes|true|1\n2) no|false|0\nIf no value is given ,display current value.'
  ,
  'HELP_TIMEZONE': 'USAGE: -timezone [TIMEZONE]\nChange timezone of current account.\nThe full list of locale can be viewed at http://en.wikipedia.org/wiki/List_of_tz_database_time_zones\nPlease use column TZ.\nIf no timezone is given, display current timezone.'
  ,
  'HELP_LOCALE': 'USAGE: -locale [LOCALE]\nChange language. Currently TwiTalkerPlus support following languages:\n%s',
  'HELP_BOLD': 'USAGE: -bold [VALUE]\nToggle bold for username and mentions containing your username.\nValue accepts following: yes|true|1 no|false|0\nIf no value is given ,display current value.'
  ,
  'HELP_PREFIX': 'USAGE: -prefix [PREFIX]\nChange command prefix. Default is a hyphen.\nCAUTIONS: CHANGE THIS SETTING AFTER YOU KNOW WHAT YOU ARE DOING, IT MAY BREAK EVERYTHING AND CANT BE RESTORED.\nIf no prefix is given, display current instead.'
  ,
  }