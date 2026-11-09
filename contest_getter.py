import datetime
import html
import pprint
import re
import traceback

import pytz
import requests
import os
import json
import time
from bs4 import BeautifulSoup

UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0'


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


def http_request(method: str, url: str, headers: dict = None, timeout: int = 15, retries: int = 3, **kwargs):
    """带 UA / 超时 / 重试的请求，避免一次网络抖动就让整个源失败。"""
    h = {'User-Agent': UA}
    if headers:
        h.update(headers)
    last_err = None
    for attempt in range(retries):
        try:
            resp = requests.request(method, url, headers=h, timeout=timeout, **kwargs)
            resp.raise_for_status()
            return resp
        except Exception as err:  # noqa: BLE001
            last_err = err
            if attempt + 1 < retries:
                time.sleep(1 + attempt)
    raise last_err


def http_get(url: str, **kwargs):
    return http_request('GET', url, **kwargs)


def fetch_cf_contest() -> list[Contest]:
    os.environ['NO_PROXY'] = 'codeforces.com'
    url = 'https://codeforces.com/api/contest.list'
    url_get = http_get(url, timeout=10)
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


_CST = datetime.timezone(datetime.timedelta(hours=8))
_LG_LINK_RE = re.compile(r'^/contest/(\d+)(?:[/?#].*)?$')
# 洛谷页面上的开赛时间形如 “2026-11-14 08:00:00 ~ 2026-11-14 12:30:00”，一律按北京时间解析
_LG_TIME_RE = re.compile(
    r'(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}(?::\d{2})?)\s*[~～]\s*'
    r'(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}(?::\d{2})?)')


def _lg_ts(date_part: str, time_part: str) -> int:
    text = f'{date_part} {time_part}'
    fmt = '%Y-%m-%d %H:%M:%S' if time_part.count(':') == 2 else '%Y-%m-%d %H:%M'
    return int(datetime.datetime.strptime(text, fmt).replace(tzinfo=_CST).timestamp())


def _luogu_parse_json(text: str):
    """洛谷 2026-03 之前 /contest/list?_contentOnly=1 返回 JSON，保留兼容分支。"""
    try:
        payload = json.loads(text)
    except ValueError:
        return None
    for key in ('currentData', 'data'):
        if isinstance(payload, dict) and isinstance(payload.get(key), dict):
            payload = payload[key]
    block = payload.get('contests') if isinstance(payload, dict) else None
    if isinstance(block, dict):
        contests = block.get('result') or block.get('contests')
    elif isinstance(block, list):
        contests = block
    else:
        contests = None
    if not contests:
        return None
    res = []
    for item in contests:
        try:
            stime, etime = int(item['startTime']), int(item['endTime'])
            res.append(Contest('luogu', item['name'], stime, etime, etime - stime,
                               f'https://www.luogu.com.cn/contest/{item["id"]}'))
        except (KeyError, TypeError, ValueError):
            continue
    return res or None


def _luogu_parse_html(text: str) -> list[Contest]:
    """解析服务端渲染的 /contest/list 页面（洛谷 2026-03 之后的新前端）。"""
    soup = BeautifulSoup(text, 'html.parser')
    current_time = time.time()
    res, seen = [], set()
    for a in soup.find_all('a', href=_LG_LINK_RE):
        href = a['href']
        cid = _LG_LINK_RE.match(href).group(1)
        name = a.get_text(' ', strip=True)
        if cid in seen or not name:
            continue
        # 时间可能在 <small>/<span> 里，也可能只是祖先节点里的一段文本：
        # 由近及远地找，谁先只命中“唯一一段”时间就用谁，避免张冠李戴。
        match, node = None, a
        for _ in range(5):
            node = node.parent
            if node is None:
                break
            found = _LG_TIME_RE.findall(node.get_text(' ', strip=True))
            if len(found) == 1:
                match = found[0]
                break
            if len(found) > 1:
                break
        if match is None:
            continue
        stime, etime = _lg_ts(match[0], match[1]), _lg_ts(match[2], match[3])
        if current_time > etime:
            continue
        seen.add(cid)
        res.append(Contest('luogu', name, stime, etime, etime - stime,
                           'https://www.luogu.com.cn' + href))
    res.sort(key=lambda x: x.stime)
    return res


def fetch_luogu_contest() -> list[Contest]:
    # 2026-03 起洛谷把 /contest/list 换成了 SPA 前端（columba），
    # ?_contentOnly=1 不再返回 JSON 而是一段 HTML 外壳，老代码 json.loads 直接抛 JSONDecodeError。
    # 现在以解析服务端渲染的列表页为主，JSON 接口仍留作兼容分支。
    url = 'https://www.luogu.com.cn/contest/list'
    url_get = http_get(url, headers={'Accept': 'text/html,application/json'})
    res = _luogu_parse_json(url_get.text) or _luogu_parse_html(url_get.text)
    if not res:
        raise RuntimeError('luogu: 列表页没有解析出任何比赛，页面结构可能又变了')
    return res


def fetch_atcoder_contest() -> list[Contest]:
    url = 'https://atcoder.jp/contests/'
    response = http_get(url).text
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
    response = http_get(url)
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

    res.sort(key=lambda x: x.stime)
    return res


def fetch_leetcode_contest() -> list[Contest]:
    url = 'https://leetcode.com/graphql'
    headers = {
        'Referer': 'https://leetcode.cn/',
        'Content-Type': 'application/json',
    }
    data = {
        'operationName': None,
        'variables': {},
        'query': '''
        {
            allContests {
                title
                titleSlug
                startTime
                duration
                isVirtual
            }
        }
        '''
    }
    response = http_request('POST', url, headers=headers, data=json.dumps(data))

    contests = json.loads(response.text)["data"]["allContests"]
    res = []
    for info in contests:

        if info["isVirtual"]:
            continue
        elif info["startTime"] + info["duration"] < time.time():
            continue

        contest = Contest(oj='leetcode')
        contest.dtime = info["duration"]
        contest.stime = info["startTime"]
        contest.etime = contest.stime + contest.dtime
        contest.name = info["title"]
        contest.link = 'https://leetcode.cn/contest/' + info["titleSlug"]
        res.append(contest)

    res.sort(key=lambda x: x.stime)
    return res


FETCHERS = [
    ('atcoder', fetch_atcoder_contest),
    ('luogu', fetch_luogu_contest),
    ('codeforces', fetch_cf_contest),
    ('nowcoder', fetch_nowcoder_contest),
    ('leetcode', fetch_leetcode_contest),
]


def collect():
    """逐个源抓取：某个源挂掉只跳过它，其余照常，不再「一处失败、全盘不写」。"""
    res, failed = [], []
    for oj, fetch in FETCHERS:
        try:
            items = fetch()
            if not items:
                raise RuntimeError('返回 0 场比赛')
            res += items
            print(f'[ok] {oj}: {len(items)} 场比赛')
        except Exception:
            failed.append(oj)
            print(f'::warning::{oj} 抓取失败，已跳过')
            traceback.print_exc()
    res.sort(key=lambda x: x.stime)
    return res, failed


if __name__ == '__main__':
    res, failed = collect()
    if not res:
        # 全部失败时不要写 contest.json，避免把上一次的好数据覆盖成空的
        raise SystemExit('所有源都抓取失败，contest.json 保持不变')
    data = {
        "refreshTimeStamp": int(time.time()),
        "refreshTimeCH": datetime.datetime.utcfromtimestamp(time.time()).replace(tzinfo=pytz.utc).astimezone(
            pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S'),
        "timezone": "utc+8",
        "OJType": ['codeforces', 'atcoder', 'luogu', 'nowcoder', 'leetcode'],
        "contests": [i.__dict__ for i in res]
    }
    with open('contest.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=4))
    print(f'contest.json 已写入：{len(res)} 场比赛，refreshTimeCH={data["refreshTimeCH"]}')
    if failed:
        print('本次失败的源: ' + ', '.join(failed))
