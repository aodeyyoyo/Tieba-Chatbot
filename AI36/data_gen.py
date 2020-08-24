import requests
from bs4 import BeautifulSoup
import urllib.parse
import json
from urllib.parse import urlencode
import re

def get_tiebalist():
    categories = {"客户端网游": "http://tieba.baidu.com/sign/index?kw=%D0%C7%BC%CA2",
     "主机及单机游戏": "http://tieba.baidu.com/sign/index?kw=%C4%A7%CA%DE%D5%F9%B0%D4",
     "动漫相关": "http://c.tieba.baidu.com/sign/index?kw=robot%E9%AD%82"}
    ans = []
    for url in categories.values():
        for i in range(1, 11):
            new_url = url+"&pn={}".format(i)
            print(new_url)
            response = requests.get(url)
            bs = BeautifulSoup(response.text, "html.parser")
            tds = bs.find_all("td", {"class": "forum_name"})
            for td in tds:
                ans.append(td.text)
    return ans

def get_turn_to_post():
    data = {}
    with open("tieba_train_2.md", "a", encoding="utf-8") as file:
        data["rasa_nlu_data"] = {}
        samples = []
        fms = ["请跳转到{}个帖子", "请看第{}个帖子", "看第{}个帖子", "给爷翻到第{}个帖子", "第{}个帖子", "我要看第{}个帖子",
               "去第{}个帖子"]
        fms += [x.replace("个", "号") for x in fms]
        nos = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, "一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]
        no_to_value = {}
        for i, no in enumerate(nos):
            no_to_value[no] = str(i%10+1)
        for fm in fms:
            for no in nos:
                no = str(no)
                file.write("- ")
                if no.isdigit():
                    no = "[{}](magnitude)".format(no)
                else:
                    no = "[{}](magnitude:{})".format(no, no_to_value[no])
                file.write(fm.format(no)+"\n")


get_turn_to_post()
exit()

tieba_name_list = json.load(open("tieba_list.json", "r"))
get_posts_formats = ["打开{}", "给老子打开{}", "请打开{}", "马上打开{}", "给爷打开{}", "滚去{}", "我想看{}", "{}", "人家要打开{}呢"
                     , "人家要打开{}呢QAQ", "打开{}好嘛", "打开{}嘛~", "帮我打开一下{}", "请打开一下{}"]
with open("tieba_train.md", "w", encoding="utf-8") as file:
    file.write("## intent:GETPOSTS\n")
    for fm in get_posts_formats:
        for tieba_name in tieba_name_list:
            tieba_name = "[{}](name)".format(tieba_name+"吧")
            file.write("- "+fm.format(tieba_name)+"\n")

