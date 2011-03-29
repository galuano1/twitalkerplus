#!/usr/bin/python
# -*- encoding: utf-8 -*-
str_list = {
  'WEB': u'<html><head><title>TwiTalkerPlus</title></head><body>请添加<b>%s@appspot.com</b>作为GTalk好友，然后使用-oauth命令认证。<br />更多命令帮助请用-help命令查询。<br /><a href="http://twitter.com/gh05tw01f">作者</a>&nbsp;<a href="https://github.com/gh05tw01f/twitalkerplus">源代码</a></body></html>'
  ,
  'NO_AUTHENTICATION': u'没有权限访问您的Twitter账户。',
  'INTERNAL_SERVER_ERROR': u'Twitter服务器内部错误',
  'TIMELINE': u'*时间线：* ',
  'MENTIONS': u'*提到我的：* ',
  'DIRECT_MESSAGES': u'*私信：* ',
  'LIST': u'*列表 %s：* ',
  'SUCCESSFULLY_REPLY_TO': u'成功回复 %s :)',
  'SUCCESSFULLY_UPDATE_STATUS': u'成功发表状态 :)',
  'PAGE': u'第%s页',
  'STATUS_NOT_FOUND': u'状态 %s 不存在',
  'WORDS_COUNT_EXCEED': u'字数%s超过%s字。',
  'STATUS_DUPLICATE': u'发推重复。',
  'STATUSES_CONVERSATION': u'*推对话：*',
  'INVALID_COMMAND': u'无效命令。',
  'INTERVAL': u'时间间隔：%s 分钟',
  'MESSAGE_TO_NOT_FOLLOWED': u'你不能向没有跟随你的用户发送私信。',
  'SUCCESSFULLY_MESSAGE': u'成功发送私信到%s :)',
  'ALREADY_FOLLOWED': u'你已经跟随%s :)',
  'BLOCKED': u'你已经被%s屏蔽 :(',
  'SUCCESSFULLY_FOLLOW': u'成功跟随%s :)',
  'SUCCESSFULLY_UNFOLLOW': u'成功取消跟随%s',
  'USER_NOT_FOUND': u'用户%s不存在。',
  'FOLLOWING_YOU': u'%s 正在跟随你 :)',
  'NOT_FOLLOWING_YOU': u'%s 没有跟随你 :(',
  'SUCCESSFULLY_BLOCK': u'成功屏蔽%s',
  'SUCCESSFULLY_UNBLOCK': u'成功解除屏蔽%s',
  'SUCCESSFULLY_SPAM': u'成功举报%s为垃圾用户',
  'STATUS_DELETED': u'状态%s已删除，内容为：\n%s',
  'DELETE_ANOTHER_USER_STATUS': u'不能删除其他人的状态',
  'ON_MODE': u'你已打开%s的更新。\n所有可打开的更新有list（列表）, home（主页）, mention（提及）, dm（私信）。',
  'LIVE_MODE': u'LIVE模式的列表指定为%s。',
  'USE_LIVE': u'请先用live命令设置用于LIVE模式的列表。',
  'LIST_NOT_FOUND': u'列表%s不存在。',
  'FAVOURITED': u'状态%s已收藏 :)',
  'UNFAVOURITED': u'状态%s已被取消收藏',
  'FAVOURITES': u'*收藏：* ',
  'USER_TIMELINE': u'*用户%s的时间线：* ',
  'SUCCESSFULLY_RETWEET': u'成功转发%s :)',
  'SUCCESSFULLY_RT': u'成功RT%s :) 内容为：\n%s',
  'CURRENT_TIMEZONE': u'你当前的时区为%s',
  'INVALID_TIMEZONE': u'时区不正确。',
  'SET_TIMEZONE_SUCCESSFULLY': u'设置时区成功 :)',
  'INVALID_LOCALE': u'无效或不支持的语言',
  'CURRENT_LOCALE': u'当前语言为：%s',
  'SET_LOCALE_SUCCESSFULLY': u'设置语言成功 :)',
  'RETWEET_MODE': u'官方转发现在起将显示为官方样式。',
  'RT_MODE': u'官方转发现在起将显示为RT样式。',
  'BOLD_MODE_ON': u'用户名将被用粗体显示。',
  'BOLD_MODE_OFF': u'用户名将不再用粗体显示。',
  'REVERSE_MODE_ON': u'推将不再以倒序显示',
  'REVERSE_MODE_OFF': u'推将以倒序显示',
  'MSG_TEMPLATE': u'状态的模板为：\n%s',
  'DATE_TEMPLATE': u'时间显示格式为：\n%s',
  'NOW_USING': u'你当前正在使用%s。',
  'ALL_TWITTER_USERS_NAME': u'所有与当前Google帐号关联的Twitter帐号如下：\n%s',
  'ENABLED_TWITTER_USER_CHANGED': u'当前你的Google帐号中启用的Twitter帐号为：%s',
  'NOT_ASSOCIATED_TWITTER_USER': u'输入的Twitter用户未与当前Google帐号关联。',
  'PROTECTED_USER': u'受保护用户或被暂定使用用户。',
  'USER_PROFILE': u'$screen_name ( $name ) 档案:\n头像地址:$profile_image_url\n网址: $url\n所在地: $location\n推数: $statuses_count\n跟随: $friends_count\n被跟随: $followers_count\n个人简介: $description\n最新状态: $status\n$following'
  ,
  'YOU_FOLLOWING': u'你已经跟随%s。',
  'YOU_HAVE_REQUESTED': u'你已经发送跟随申请给%s。',
  'YOU_DONT_FOLLOW': u'你没有跟随%s。',
  'COMMAND_PREFIX': u'命令前缀是 %s',
  'TWITTER_USER_DELETED': u'%s不再与你相关联。',
  'SPECIFY_ANOTHER_USER': u'请使用switch命令指定另外一个用户。',
  'OAUTH_URL': u'请访问以下网址获取PIN码:\n%s\n然后使用"-bind PIN码"命令绑定。',
  'INVALID_PIN_CODE': u'无效PIN码%s。',
  'SUCCESSFULLY_BIND': u'成功绑定Twitter账户%s。',
  'NETWORK_ERROR': u'网络错误。',
  'WRONG_USER_OR_PASSWORD': u'错误的用户名或密码。',
  'ALL_COMMANDS': u"""TwiTalkerPlus目前支持以下命令，你可以通过-?/-h/-help COMMAND查询每条命令的详细用法（方括号代表参数可选）:
    操作类:
    -@/-r-/-reply： 回复推
    -d/-dm：发送或查看私信
    -ho/-home：查看首页时间线
    -rt：RT推
    -re：官方RT推
    -ra：回复推中提到的所有人
    -m/-msg：查看推对话
    -u/-user：查看用户页面
    -del：删除推
    -tl/-timeline：查看用户时间线
    -f/-fav：收藏推或查看已收藏的推
    -uf/-unfav：取消收藏推
    -fo/-follow：跟随用户
    -unfo/-unfollow：取消跟随用户
    -if：判断对方是否跟随你
    -b/-block：屏蔽用户
    -ub/-unblock：取消屏蔽用户
    -spam：举报垃圾用户
    -lt/-list：查看列表中的推
    -s/-switch：切换用户
    设置类:
    -on：查看或开启元件更新
    -off：查看或关闭元件更新
    -live：指定列表更新的列表
    -time：指定更新间隔
    -msgtpl：指定推模板
    -datefmt：指定时间格式
    -retweet：指定官方RT显示方式
    -locale：指定语言
    -timezone：指定时区
    -bold：指定用户名是否加粗
    -prefix：指定命令前缀
    -reverse：指定推是否倒序显示
    认证类:
    -oauth：开始OAuth认证
    -bind：绑定PIN码完成认证
    -remove：解除关联
    帮助:
    -?/-h/-help：显示本帮助
    如果在使用中发现有BUG，请及时联系我@gh05tw01f 谢谢～
    """,
  'HELP_OAUTH': u'用法： -oauth [用户名 密码]\n获取用于OAuth的链接。如果你提供用户名和密码，可以免去上Twitter网站认证的过程。',
  'HELP_BIND': u'用法： -bind PIN码\n提供PIN码用以完成OAuth认证。PIN码可以通过访问用-oauth命令获取到的链接后获得。',
  'HELP_REMOVE': u'用法： -remove [用户名]\n取消指定用户与当前帐号的关联关系。',
  'HELP_ON': u'用法： -on [元件]\n开启指定元件的更新。如果不指定元件，则显示当前已开启的元件。',
  'HELP_OFF': u'用法： -off [元件]\n关闭所有更新提示。如果不指定元件，则显示当前已开启的元件。',
  'HELP_LIVE': u'用法： -live [列表名字]\n指定列表更新中的列表。你需要事先指定列表名字。目前列表名字接受以下格式：\n用户名 列表名\n用户名/列表名\n列表名 （这种将使用当前用户作为用户名）\n如果不指定列表，则显示当前列表。'
  ,
  'HELP_REPLY': u'用法(1)： -r/-@/-reply ID 内容\n回复指定ID的推。ID可以是类似2866000224794214的长ID，也可以是类似#12的短ID，短ID前的井号可选。\n用法(2)： -r/-@/-reply [p页码]\n显示提及你的推。p页码参数可选。'
  ,
  'HELP_DM': u'用法(1)： -d/-dm 用户名 内容\n向指定用户发送私信。\n用法(2)： -d/-dm [p页码]\n显示私信。p页码参数可选。',
  'HELP_RT': u'用法： -rt ID [内容]\nRT指定的推并附带自己的内容。 ID可以是类似2866000224794214的长ID，也可以是类似#12的短ID，短ID前的井号可选。英文内容后将自动添加空格。超过140字将被自动截断。'
  ,
  'HELP_RE': u'用法： -re ID\n官方RT指定的推。ID可以是类似2866000224794214的长ID，也可以是类似#12的短ID，短ID前的井号可选。',
  'HELP_RA': u'用法： -ra ID 内容\n回复指定的推中提及的所有人。ID可以是类似2866000224794214的长ID，也可以是类似#12的短ID，短ID前的井号可选。',
  'HELP_MSG': u'用法： -m/-msg ID\n显示指定的推涉及的推对话。ID可以是类似2866000224794214的长ID，也可以是类似#12的短ID，短ID前的井号可选。',
  'HELP_USER': u'用法： -u/-user [用户名]\n显示指定用户的信息。如果不指定用户名，将显示当前用户',
  'HELP_DEL': u'用法： -del [ID]\n删除指定的推。ID可以是类似2866000224794214的长ID，也可以是类似#12的短ID，短ID前的井号可选。如果不指定ID，将删除当前用户最新的推。\n警告：不鼓励通过反复使用-del命令来删除自己的推，不加参数的用法建议只用于紧急删除之前发送错误的推。'
  ,
  'HELP_HOME': u'用法： -home [p页码]\n显示首页时间线。p页码参数可选。',
  'HELP_TIMELINE': u'用法： -tl/-timeline [用户名] [p页码]\n显示指定用户的时间线，p页码参数可选。如果不指定用户，则显示当前用户的。',
  'HELP_LIST': u'用法： -lt/-list 列表名 [p页码]\n显示指定列表的时间线更新，p页码参数可选。\n目前列表名字接受以下格式：\n用户名 列表名\n用户名/列表名\n列表名 （这种将使用当前用户作为用户名）',
  'HELP_FAV': u'用法(1)： -f/-fav ID\n收藏指定的推。ID可以是类似2866000224794214的长ID，也可以是类似#12的短ID，短ID前的井号可选。\n用法(2)： -f/-fav [p页码]\n显示已收藏的推，p页码参数可选。'
  ,
  'HELP_UNFAV': u'用法： -uf/-unfav ID\n取消收藏指定的推。ID可以是类似2866000224794214的长ID，也可以是类似#12的短ID，短ID前的井号可选。',
  'HELP_FOLLOW': u'用法： -fo/-follow 用户名\n跟随指定的用户。',
  'HELP_UNFOLLOW': u'用法： -unfo/-unfollow 用户名\n取消跟随指定的用户。',
  'HELP_IF': u'用法： -if 用户名\n判断指定用户是否跟随了你。',
  'HELP_BLOCK': u'用法： -b/-block 用户名\n屏蔽指定用户。',
  'HELP_UNBLOCK': u'用法： -ub/-unblock 用户名\n取消屏蔽指定用户。',
  'HELP_SPAM': u'用法： -spam 用户名\n举报指定用户为垃圾用户。',
  'HELP_SWITCH': u'用户： -s/-switch [用户名]\n切换当前使用的Twitter用户为指定用户。如果不指定用户名，则显示所有已经绑定的用户。',
  'HELP_TIME': u'用法：: -time [时间]\n更改两次更新之间间隔的时间，单位是分钟。如果不指定时间，则显示当前时间间隔。',
  'HELP_MSGTPL': u'用法： -msgtpl [模板字符串]\n修改每条推的模板。当前支持以下关键字：\n$username -> 推或私信的发送用户\n$content -> 推或私信的内容\n$id -> 类似2866000224794214的长ID\n$shortid -> 类似#12的短ID（带井号显示）\n$time -> 推或私信的时间，格式可以用-datefmt命令修改\n$source -> 推的来源\n不建议在关键字后面紧跟下划线，因为下划线也会被识别为关键字的一部分。\n你可以在模板结尾处添加若干\\n来声明结尾的转行和空行。\n如果不指定模板，则显示当前模板。'
  ,
  'HELP_DATEFMT': u'用法： -datefmt [格式]\n修改时间显示的格式。格式需要遵从以下网址中提到的规则：\nhttp://docs.python.org/release/2.5.4/lib/module-time.html#l2h-2826\n如果没有指定格式，则显示当前格式。'
  ,
  'HELP_RETWEET': u'用法： -retweet [值]\n在两种官方RT的显示风格中切换： 1) 显示为普通推，用户名为原推的用户名。 2) 把官方RT显示为传统RT，用户名为RT的人。\n值可以是以下：\n1) yes|true|1\n2) no|false|0\n如果没有指定值，则显示当前值。'
  ,
  'HELP_TIMEZONE': u'用法： -timezone [时区名字]\n修改时区。\n完整的时区列表可以在以下网址查询：\nhttp://en.wikipedia.org/wiki/List_of_tz_database_time_zones\n请使用TZ栏的名字.\n如果不指定时区，则显示当前时区。'
  ,
  'HELP_LOCALE': u'用法： -locale [语言]\n修改语言。当前支持以下语言：\n%s',
  'HELP_BOLD': u'用法： -bold [值]\n切换是否加粗推的用户名和推中你的用户名（仅对GTalk官方客户端有效）\n值可以是以下：\n是) yes|true|1\n否) no|false|0\n如果没有指定值，则显示当前值。'
  ,
  'HELP_PREFIX': u'用法： -prefix [前缀]\n修改每条命令前用于识别的前缀。默认的前缀是英文短连词线。\n警告：你最好搞清楚你在做什么后再修改，否则很可能弄得一团糟并且无法恢复。\n如果不指定前缀，则显示当前前缀。'
  ,
  'HELP_REVERSE': u'用法： -reverse [值]\n切换是否把推倒序显示（默认是倒序）\n值可以是以下：\n是) yes|true|1\n否) no|false|0\n如果没有指定值，则显示当前值。'
  ,
  }