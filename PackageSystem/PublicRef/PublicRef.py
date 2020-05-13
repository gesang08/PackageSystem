#!usr/bin/env python3
#encoding:utf8

import time,datetime
def current_time_python2():
    t = time.strftime("%Y年%m月%d日 %H:%M:%S  ", time.localtime(time.time()))
    return t

def current_time():
    t = time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y='-', m='-', d='', h=':', f=':', s='')
    return t
def currentTime():
    t = time.strftime('%Y{y}%m{m}%d{d}%H{h}%M{f}%S{s}').format(y='', m='', d='', h='', f='', s='')
    return t

curTime = currentTime()

if __name__ == '__main__':
    print(current_time())
    print(curTime)
    print(time.strftime('%Y{y}%m{m}%d{d}').format(y='', m='', d=''))

    if str(datetime.datetime.now()) > '2019-12-25 01:06:07.004518':
        print(datetime.datetime.now())