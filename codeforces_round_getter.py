import requests
import os
import json
import time


def cf_api_test():
    # return [{(str)name, (int)stime, (int)etime, (str)link}]
    os.environ['NO_PROXY'] = 'codeforces.com'
    url = ' https://codeforces.com/api/contest.list'
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0'
    headers = {'User-Agent': user_agent}
    url_get = requests.get(url, headers=headers, timeout=10)
    url_get_par = json.loads(url_get.text)
    res = []
    n = 100
    now = time.localtime()
    now = time.mktime(now)
    for i in range(1, n):
        name = url_get_par["result"][i]["name"]
        stime = url_get_par["result"][i]["startTimeSeconds"]
        etime = stime + 2.5 * 60 * 60
        link = 'https://codeforces.com'

        if stime - now < 0:
            break

        res.append({'name': name, 'stime': stime, 'etime': etime, 'link': link})

    return res



if __name__ == '__main__':
    for each in cf_api_test():
        print(each)
