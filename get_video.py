# /usr/env/bin python3
import re
import hashlib
import json
import ast
import os
import sys
import requests
from merge_video import MergeVideo

bili_url = [
    "www.bilibili.com/video", 
    "www.bilibili.com/bangumi"]  

api = [
    "https://interface.bilibili.com/v2/playurl?",
    "https://bangumi.bilibili.com/player/web_api/v2/playurl?",
    "https://api.bilibili.com/x/player/playurl/token?",]

headers = {
    "Accept": "Accept: text/html,application/xhtml+xml,"+
        "application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Charset": "UTF-8,*;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    'Referer': "",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/"+
        "537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36"}

cookies = {}

"""接收视频地址,判断地址类型"""
try:
    while 1:
        url = input("请输入视频地址:")
        if bili_url[0] in url:
            break
        elif bili_url[1] in url:
            print("番剧暂时无法下载，正在努力破解^-^")
            sys.exit()
        else:
            print("链接错误,请重新输入")

except KeyboardInterrupt:
    print("\n新的一天，要继续加油^_^")
    sys.exit()

"""获取必需参数"""
headers['Referer'] = url
html = requests.get(url, headers=headers, cookies=cookies, verify=True).text
quality = 116
appkey = 'iVGUTjsxvpLeuDCf'
secretkey = 'aHRmhWMLkdeMuILqORnYZocwMBpMEOdt'
title = re.findall(r'<h1 title="(.*?)"', html)[0]

if bili_url[0] in url:
    cid_part = ''.join(re.findall(r'"pages":\[(.*?)\],', html)) #  若出错,重新定位 cid.
    cids = ast.literal_eval(cid_part)  # len(cid_str)==1 返回字典,否则返回元组.
    if type(cids) == type({}):
        cid = cids['cid']
    elif type(cids) == type(()):  # 多个视频,判断当前页面 cid.
        if "?p=" in url:
            which_cid = int((url.split('?p=')[1:])[0])
            cid = cids[which_cid - 1]['cid']  # 减 1 是因为从 0 开始.
            title = cids[which_cid - 1]['part']
        else:
            cid = cids[0]['cid']  # 下载第一个视频.
            title = cids[0]['part']
    else:
        cid = ''.join(re.findall(r'cid=(\d+)&aid', html))  # 特殊页面，特殊处理.

elif bili_url[1] in url:
    aid = re.search(r'aid":(.*?),"cid"', html).group(1)
    season_type = re.findall(r'season_type":(\d+),', html)[0]
    cid = re.search(r'cid":(.*?),"cover"', html).group(1)
    print(F"{api[2]}aid={aid}&cid={cid}")
    utoken = requests.get(F"{api[2]}aid={aid}&cid={cid}", headers=headers,cookies=cookies).text
    utoken = ast.literal_eval(utoken)
    utoken = utoken['data']['token']
    print(aid, season_type, cid, utoken)

else:
    print("链接有误,只接受番剧和视频链接!")
    sys.exit()

"""构造参数获取链接"""
if bili_url[0] in url:
    url_params = (
        F"appkey={appkey}&cid={cid}&otype=json&qn={quality}&quality={quality}&type=")
    sign = hashlib.md5((url_params+secretkey).encode('utf-8')).hexdigest()
    durl_api = api[0] + url_params + F"&sign={sign}"
else:
    url_params = (
        F"appkey={appkey}&cid={cid}&module=bangumi&otype=json&qn={quality}&quality={quality}&season_type={season_type}&type=" )
    sign = hashlib.md5((url_params+secretkey).encode('utf-8')).hexdigest()
    durl_api = api[1] + url_params + F"&sign={sign}"
    durl_api = durl_api + F"&utoken={utoken}"

video_params = requests.get(durl_api,headers=headers).json() 
durl = video_params['durl']
video_urls = list()
for i in range(0, len(durl)):
    video_urls.append(video_params['durl'][i]['url'])

"""准备下载工作"""
cur_path = (os.popen('pwd').read()).strip('\n')
file_path = cur_path + '/Bilivideo/'
find_dir = os.popen("ls").read()
if "Bilivideo" not in find_dir:
    print(F"未找到存放文件夹，已自动创建，路径为 {file_path}")
    os.system("mkdir Bilivideo")

"""开始下载"""
print(F"{title},开始下载...")
num = 0
merge_list = list()

for url in video_urls:
    video = requests.get(url, headers=headers, stream=True)
    with open(file_path + F"{ title }_{num}.flv", 'wb') as fileput:
        total_length = video.headers.get('content-length')
        total_length = int(total_length)
        download_lenghth = 0
        for data in video.iter_content(chunk_size=4096):
            download_lenghth = download_lenghth + len(data)
            fileput.write(data)
            done = int(40 * download_lenghth / total_length)
            sys.stdout.write(
                F"\r\037[0;36m|{'█' * done}{'-' * (40-done)}| {done*2.5}%|剩余下载数量 {len(durl)-num-1}\033[0m")
            sys.stdout.flush()
    merge_list.append(F"{ title }_{num}.flv")
    num = num + 1

"""合并视频"""
if len(durl) < 2:
    print( F"\n下载完成,文件位置：{file_path}{title} ")

else:
    mv = MergeVideo()
    mv.merge(merge_list)






























