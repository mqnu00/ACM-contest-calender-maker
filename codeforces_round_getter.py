import requests
import os
import json
import time


class Contest:

    def __init__(self, oj: str, name: str, stime: str, etime: str, dtime: str, link):
        self.oj = oj
        self.name = name
        self.stime = stime
        self.etime = etime
        self.dtime = dtime
        self.link = link

    def __str__(self):
        return json.dumps(self.__dict__, ensure_ascii=False)


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
    res.sort(key=lambda x:x.stime)
    return res


if __name__ == '__main__':
    # for each in fetch_cf_contest():
    #     print(each)
    for each in fetch_luogu_contest():
        print(each)
