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
quality = 116
appkey = 'iVGUTjsxvpLeuDCf'
secretkey = 'aHRmhWMLkdeMuILqORnYZocwMBpMEOdt'


def get_cid(html: str) -> str:
    """获取 cid 参数
    1. 定位 cid 参数位置。
    2. 判断此视频是否有多个分 P。
    3. 若页面有多个 cid 则获取当前页面的 cid。
    """
    title = re.findall(r'<h1 title="(.*?)"', html)[0]
    cid_part = ''.join(re.findall(r'"pages":\[(.*?)\],', html)) #  若出错,重新定位 cid.
    cids = ast.literal_eval(cid_part)  # len(cid_str)==1 返回字典,否则返回元组.
    if type(cids) == type({}):
        cid = cids['cid']
    elif type(cids) == type(()):  # 多个视频,判断当前页面 cid.
        if "?p=" in url:
            which_cid = int((url.split('?p=')[1:])[0])
            cid = cids[which_cid - 1]['cid']  # 减 1 是因为从 0 开始.
            title = F"{title}_{cids[which_cid - 1]['part']}"
        else:
            cid = cids[0]['cid']  # 下载第一个视频.
            title = F"{title}_{cids[0]['part']}"
    else:
        cid = ''.join(re.findall(r'cid=(\d+)&aid', html))  # 特殊页面，特殊处理.

    return cid, title


def get_dl_urls(cid: str) -> list:
    """构造参数获取视频资源服务器链接
    1. 构造请求链接。
    2. 获得返回的 json 数据。
    3. 从 json 文件中解析视频下载地址。
    """
    url_params = (
        F"appkey={appkey}&cid={cid}&otype=json&qn={quality}&quality={quality}&type=")
    sign = hashlib.md5((url_params+secretkey).encode('utf-8')).hexdigest()
    durl_api = api[0] + url_params + F"&sign={sign}"
    video_params = requests.get(durl_api,headers=headers).json() 
    durl = video_params['durl']
    video_urls = list()
    for i in range(0, len(durl)):
        video_urls.append(video_params['durl'][i]['url'])

    return video_urls


def dl_video(video_urls: list, title: str)-> None:
    """下载视频
    1. 判断是否存在 Bilivideo 文件夹，不存在则自动创建
    2. 下载 video_urls 中的视频链接。
    3. 下载完成后判断当前视频是否被分割成多段，如果被分割则使用合并工具。
    """
    cur_path = (os.popen('pwd').read()).strip('\n')
    file_path = cur_path + '/Bilivideo/'
    find_dir = os.popen("ls").read()
    if "Bilivideo" not in find_dir:
        print(F"未找到存放文件夹，已自动创建，路径为 {file_path}")
        os.system("mkdir Bilivideo")
    print(F"{title},开始下载...")
    num = 0
    merge_list = list()
    for url in video_urls:
        video = requests.get(url, headers=headers, stream=True)
        with open(file_path + F"{ title }_{num}.flv", 'wb') as f:
            total_length = int(video.headers.get('content-length'))
            download_lenghth = 0
            for data in video.iter_content(chunk_size=4096):
                download_lenghth = download_lenghth + len(data)
                f.write(data)
                done = int(40 * download_lenghth / total_length)
                sys.stdout.write(
                    f"\r|{'█' * done}{'-' * (40-done)}| {done*2.5}%|剩余 {len(video_urls)-num-1}")
                sys.stdout.flush()
        merge_list.append(F"{ title }_{num}.flv")
        num = num + 1
    if len(merge_list) < 2:
        print( F"\n下载完成,文件位置：{file_path}{title} ")
    else:
        mv = MergeVideo()
        mv.merge(merge_list)


def main():
    """程序流程
    1. 接收视频地址,判断地址类型
    2. 获取必需参数:quality,appkey,secretkey，cid
    3. 根据参数构造服务器请求链接，获得视频链接列表。
    4. 下载视频。
    5. 判断视频是否需要合并。
    """
    try:
        while 1:
            url = input("请输入视频地址:")
            if bili_url[0] in url:
                break
            else:
                print("链接错误,请重新输入")
    except KeyboardInterrupt:
        print("\n新的一天，要继续加油^_^")
        sys.exit()
    headers['Referer'] = url
    html = requests.get(url, headers=headers, cookies=cookies, verify=True).text
    cid, title = get_cid(html)
    video_urls = get_dl_urls(cid)
    dl_video(video_urls, title)

if __name__ == '__main__':
    main()












