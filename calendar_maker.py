import traceback

import icalendar

import contest_getter
from icalendar import Calendar, Event, Timezone
import datetime
from pathlib import Path
import os
import time


def calender_maker(contest_method, calendar_name):
    cal = Calendar()

    cal.add('prodid', '-//test.us//iCalendar Event//EN  ')  # 软件信息
    cal.add('version', '2.0')  # 遵循的iCalendar版本号
    cal.add('X-WR-CALNAME', calendar_name)  # 日历名
    # cal.add('X-WR-TIMEZONE', 'UTC+8')  # 时区标记
    cal.add('X-WR-CALDESC', calendar_name + '.created by chigua_demolu.')  # 日历描述

    timezone = Timezone()
    timezone.add('timezone', 'Asia/Shanghai')
    timezone.add('tzid', 'Asia/Shanghai')
    timezone.add('tzname', 'China Standard Time')
    timezone.add('tzoffsetfrom', datetime.timedelta(hours=8))
    timezone.add('tzoffsetto', datetime.timedelta(hours=8))
    timezone.add('dtstart', datetime.datetime(2024, 1, 1))
    timezone.add('rrule', {'FREQ': 'YEARLY'})

    # 将时区组件添加到日历中
    cal.add_component(timezone)

    # 获取竞赛信息
    content = contest_method()
    # 保存目录
    direct = Path.cwd()
    direct = direct / "calendar"
    for each in content:
        # 开始时间
        stime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(each.stime))
        stime = datetime.datetime.strptime(stime, "%Y-%m-%d %H:%M:%S")
        # 结束时间
        etime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(each.etime))
        etime = datetime.datetime.strptime(etime, "%Y-%m-%d %H:%M:%S")
        event = Event()
        # 比赛名
        event.add('summary', each.name)
        # 比赛描述
        event.add('description', each.link)
        event.add('dtstart', stime)
        event.add('dtend', etime)
        # 事件的唯一标识
        event['uid'] = each.name
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
    try:
        calender_maker(contest_getter.fetch_cf_contest, 'codeforces-contest')
        calender_maker(contest_getter.fetch_luogu_contest, 'luogu-contest')
        calender_maker(contest_getter.fetch_atcoder_contest, 'atcoder-contest')
        calender_maker(contest_getter.fetch_nowcoder_contest, 'nowcoder-contest')
        calender_maker(contest_getter.fetch_leetcode_contest, 'leetcode-contest')
    except Exception as e:
        traceback.print_exc()
    finally:
        pass