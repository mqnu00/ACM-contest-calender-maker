from codeforces_round_getter import fetch_cf_contest
from icalendar import Calendar, Event
import datetime
from pathlib import Path
import os
import time


def calender_maker(contest_method, calendar_name):
    cal = Calendar()

    cal.add('prodid', '-//test.us//iCalendar Event//EN  ')      #软件信息
    cal.add('version', '2.0')                                   #遵循的iCalendar版本号
    cal.add('X-WR-CALNAME', calendar_name)                      #日历名
    cal.add('X-WR-TIMEZONE', 'UTC+8')                           #时区标记
    cal.add('X-WR-CALDESC', calendar_name + '.created by chigua_demolu.')   #日历描述

    # 获取竞赛信息
    content = contest_method()
    # 保存目录
    direct = Path.cwd()
    for each in content:
        #开始时间
        stime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(each['stime']))
        stime = datetime.datetime.strptime(stime, "%Y-%m-%d %H:%M:%S")
        #结束时间
        etime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(each['etime']))
        etime = datetime.datetime.strptime(etime, "%Y-%m-%d %H:%M:%S")
        event = Event()
        #比赛名
        event.add('summary', each['name'])
        #比赛描述
        event.add('description', each['name'] + ' from:' + each['link'])
        event.add('dtstart', stime)
        event.add('dtend', etime)
        #事件的唯一标识
        event['uid'] = each['name']
        cal.add_component(event)

    try:
        direct.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print("Folder already exists")
    else:
        print("Folder was created")

    f = open(os.path.join(direct, calendar_name + '.ics'), 'wb')
    f.write(cal.to_ical())
    f.close()


if __name__ == '__main__':
    calender_maker(fetch_cf_contest, 'codeforces-round')