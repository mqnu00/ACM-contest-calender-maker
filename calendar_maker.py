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
    if not content:
        # 抓取结果为空时保留旧日历，绝不把它覆盖成一个空文件
        raise RuntimeError(f'{calendar_name}: 抓取结果为 0 场，保留旧日历')
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

    data = cal.to_ical()
    target = os.path.join(direct, calendar_name + '.ics')
    if os.path.exists(target):
        with open(target, 'rb') as old:
            if old.read() == data:
                print(f'{calendar_name}: 内容无变化，跳过写入')
                return
    # 先写临时文件再改名，避免订阅端读到只写了一半的日历
    tmp = target + '.tmp'
    with open(tmp, 'wb') as f:
        f.write(data)
    os.replace(tmp, target)
    print(f'{calendar_name}: 已更新 {len(content)} 场比赛')


CALENDARS = [
    (contest_getter.fetch_cf_contest, 'codeforces-contest'),
    (contest_getter.fetch_luogu_contest, 'luogu-contest'),
    (contest_getter.fetch_atcoder_contest, 'atcoder-contest'),
    (contest_getter.fetch_nowcoder_contest, 'nowcoder-contest'),
    (contest_getter.fetch_leetcode_contest, 'leetcode-contest'),
]

if __name__ == '__main__':
    failed = []
    for contest_method, calendar_name in CALENDARS:
        # 各平台互不影响：某个源挂了只跳过它，其余日历照常更新
        try:
            calender_maker(contest_method, calendar_name)
        except Exception:
            failed.append(calendar_name)
            print(f'::warning::{calendar_name} 生成失败，已保留旧文件')
            traceback.print_exc()
    if len(failed) == len(CALENDARS):
        raise SystemExit('所有日历都生成失败')
    if failed:
        print('本次失败的日历: ' + ', '.join(failed))