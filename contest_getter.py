import datetime
import html
import pprint

import pytz
import requests
import os
import json
import time
from bs4 import BeautifulSoup


class Contest:

    def __init__(self, oj: str = None, name: str = None, stime: int = None, etime: int = None, dtime: int = None,
                 link: str = None):
        self.oj = oj
        self.name = name
        self.stime = stime
        self.etime = etime
        self.dtime = dtime
        self.link = link

    def __str__(self):
        return json.dumps(self.__dict__, ensure_ascii=False, indent=4)

    def __repr__(self):
        return json.dumps(self.__dict__, ensure_ascii=False, indent=4)


def fetch_cf_contest() -> list[Contest]:
    os.environ['NO_PROXY'] = 'codeforces.com'
    url = 'https://codeforces.com/api/contest.list'
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0'
    headers = {'User-Agent': user_agent}
    url_get = requests.get(url, headers=headers, timeout=10)
    url_get_par = json.loads(url_get.text)
    res = []
    n = 100
    for i in range(1, n):
        info = url_get_par["result"][i]
        if info["phase"] == 'FINISHED':
            break
        name = info["name"]
        stime = info["startTimeSeconds"]
        dtime = info["durationSeconds"]
        etime = stime + dtime
        link = f'https://codeforces.com/contest/{info["id"]}'
        contest = Contest('codeforces', name, stime, etime, dtime, link)

        res.append(contest)

    res.sort(key=lambda x: x.stime)
    return res


def fetch_luogu_contest() -> list[Contest]:
    url = 'https://www.luogu.com.cn/contest/list?page=1&_contentOnly=1'
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0'
    headers = {'User-Agent': user_agent}
    url_get = requests.get(url, headers=headers, timeout=10)
    url_get_par = json.loads(url_get.text)
    contests = url_get_par["currentData"]["contests"]["result"]
    current_time = time.time()
    res = []
    for i in contests:
        if current_time > i["endTime"]:
            break
        contest = Contest(
            oj='luogu',
            name=i['name'],
            stime=i["startTime"],
            etime=i["endTime"],
            dtime=i["endTime"] - i["startTime"],
            link=f'https://www.luogu.com.cn/contest/{i["id"]}'
        )
        res.append(contest)
    res.sort(key=lambda x: x.stime)
    return res


def fetch_atcoder_contest() -> list[Contest]:
    url = 'https://atcoder.jp/contests/'
    response = requests.get(url).text
    content = BeautifulSoup(response, 'html.parser')
    content = content.find('div', id='contest-table-upcoming')
    res: list[Contest] = []
    check = True
    for row in content.find_all('tr'):
        if check:
            check = False
            continue
        contest = Contest(oj='atcoder')
        cells = row.find_all('td')
        for i in range(0, len(cells)):
            if i == 0:

                datetime_str = cells[i].find('time').text
                # 将字符串转换为datetime对象
                # 注意：+0900表示UTC+9:00时区，需要转换为UTC时间
                dt = datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S%z")

                # 转换为UTC时间
                dt_utc = dt.astimezone(datetime.timezone.utc)

                # 将datetime对象转换为时间戳
                timestamp = int(time.mktime(dt_utc.timetuple()))

                contest.stime = timestamp + 8 * 60 * 60

            elif i == 1:

                link = 'https://atcoder.jp' + cells[i].find('a').get('href')
                contest.link = link
                contest.name = cells[i].find('a').text

            elif i == 2:

                nums = [int(num) for num in cells[i].text.split(':')]
                contest.dtime = nums[0] * 3600 + nums[1] * 60
                contest.etime = contest.stime + contest.dtime
        res.append(contest)

    res.sort(key=lambda x: x.stime)
    return res


def fetch_nowcoder_contest() -> list[Contest]:
    url = 'https://ac.nowcoder.com/acm/contest/vip-index?topCategoryFilter=13'
    response = requests.get(url)
    content = BeautifulSoup(response.text, 'html.parser')
    content = content.find('div', class_='platform-mod js-current')

    res = []
    for info in content.find_all('div', class_='platform-item js-item'):
        info = json.loads(html.unescape(info.get('data-json')))
        contest = Contest(oj='nowcoder')
        contest.dtime = int(info['contestDuration'] / 1000)
        contest.stime = int(info['contestStartTime'] / 1000)
        contest.etime = int(info['contestEndTime'] / 1000)
        contest.name = info['contestName']
        contest.link = f'https://ac.nowcoder.com/acm/contest/{info["contestId"]}'
        res.append(contest)

    res.sort(key=lambda x:x.stime)
    return res


if __name__ == '__main__':
    res = fetch_atcoder_contest() + fetch_luogu_contest() + fetch_cf_contest() + fetch_nowcoder_contest()
    res.sort(key=lambda x: x.stime)
    for i in range(0, len(res)):
        res[i] = res[i].__dict__
    res = {
        "refreshTimeStamp": int(time.time()),
        "refreshTimeCH": datetime.datetime.utcfromtimestamp(time.time()).replace(tzinfo=pytz.utc).astimezone(
            pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S'),
        "timezone": "utc+8",
        "OJType": ['codeforces', 'atcoder', 'luogu', 'nowcoder'],
        "contests": res
    }
    # for i in res['contests']:
    #     print(datetime.datetime.fromtimestamp(i['stime']), i['name'])
    # pprint.pprint(res)
    with open('contest.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(res, ensure_ascii=False, indent=4))
