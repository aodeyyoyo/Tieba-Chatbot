import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import json
from urllib.parse import urlencode


class Tieba:
    def __init__(self):
        self.logged_in = False
        self.session = requests.Session()
        self.tieba_name = None
        self.tieba_url = None
        self.response = None
        self.post_lis = None
        self.post_url = None
        self.page_no = 1
        self.tot_pages = 1

    def get_count_text(self, bs):
        '''
        对帖子的bs对象分析，获得计数字符串
        :param bs: 目标贴吧的beautifulsoup对象
        :return: 计数字符串
        '''
        div = bs.find("div", {"id": "content_leftList", "class": "content_leftList j-content-leftList clearfix"})
        count_div = div.find("div", {"class": "th_footer_l"})
        count_text = count_div.text
        count_text = count_text.split()
        count_text[-1] = ","+count_text[-1]
        count_text = "".join(count_text)
        return count_text

    def get_post_info(self, li):
        '''
        对目标帖子简介的li进行分析，得到帖子信息字符串
        :param li: 目标帖子简介的li对象
        :return: 帖子简介字符串
        '''
        ans = {}
        data = json.loads(li["data-field"])
        ans["author_name"] = data["author_name"]
        ans["author_nickname"] = data["author_nickname"]
        ans["title"] = li.find("a", {"rel": "noreferrer"}).text
        ans["abstract"] = li.find("div", {"class": "threadlist_abs threadlist_abs_onlyline"}).text.strip()
        ans["time"] = li.find("span",{"class": "threadlist_reply_date pull_right j_reply_data"}).text.strip()

        return ans

    def get_post_authors(self, bs):
        '''
        在进入某个帖子后，获得所有作者信息
        :param bs: 帖子的BeautifulSoup对象
        :return: 作者列表
        '''

        divs = bs.find_all("div", {"class": "d_author"})
        ans = []
        for div in divs:
            name = div.find("li", {"class", "d_name"}).a.text
            href = urllib.parse.urljoin(self.post_url, div.find("li", {"class", "d_name"}).a["href"])
            level_name = div.find("div", {"class": "d_badge_title"}).text
            level_no = div.find("div", {"class": "d_badge_lv"}).text
            ans.append({"name": name, "href": href, "level_name": level_name, "level_no": level_no})
        return ans

    def get_post_contents(self, bs):
        '''
        在进入某个帖子后，获得所有回帖内容
        :param bs: 帖子的BeautifulSoup对象
        :return: 回帖内容列表
        '''
        divs = bs.find_all("div", {"class": "p_content"})
        ans = []
        for div in divs:
            div = div.cc.find_all("div")[-1]
            content = div.text[1:-1].strip()
            ans.append({"content": content})

        return ans

    def log_in(self, username, password):
        pass

    def get_posts(self, tieba_name):
        '''
        获取某个贴吧的热帖
        :param tieba_name: 要获取帖子的贴吧名
        :return: 访问失败时返回安全码，否则返回帖子列表
        '''
        self.tieba_url = f"https://tieba.baidu.com/f?ie=utf-8&kw={tieba_name}"
        self.response = self.session.get(self.tieba_url)
        if self.response.status_code != 200:
            return self.response.status_code
        bs = BeautifulSoup(self.response.text, features="html.parser")
        div = bs.find("div", {"id": "content_leftList", "class": "content_leftList j-content-leftList clearfix"})
        count_text = self.get_count_text(bs)
        lis = div.find_all("li", {"class": "j_thread_list clearfix"})
        self.post_lis = lis
        ans = []
        for li in lis:
            ans.append(self.get_post_info(li))
        self.tieba_name = tieba_name
        return ans

    def turn_to_post(self, li_no=None, post_url=None):
        '''
        根据指定的帖子编号(get_poses得到的列表中位置)，跳转到对应的帖子
        :param li_no: get_poses得到的列表中帖子位置
        :return: 相关帖子信息
        '''
        url = ""
        if li_no != None:
            if li_no > 0:
                li_no -= 1
            if li_no < -len(self.post_lis) or li_no >= len(self.post_lis):
                return None
            url = self.post_lis[li_no].find("a", {"rel": "noreferrer"})["href"]
            url = urllib.parse.urljoin(self.tieba_url, url)
        elif post_url != None:
            url = post_url
        else:
            return None
        if post_url is None:
            self.post_url = url
        response = self.session.get(url)
        if response.status_code != 200:
            return None
        if post_url is None:
            self.page_no = 1
        bs = BeautifulSoup(response.text, features="html.parser")
        li = bs.find("li", {"class": "l_reply_num"})
        if li_no is not None:
            self.tot_pages = int(li.find_all("span")[-1].text)
            print(self.tot_pages, "设置总页数")
        authors = self.get_post_authors(bs)
        contents = self.get_post_contents(bs)
        #print(authors)
        #print(contents)
        posts = []
        for i in range(len(authors)):
            posts.append({"name": authors[i]["name"],
                          "level_name": authors[i]["level_name"], "level_no": authors[i]["level_no"],
                          "content": contents[i]["content"]})
        return posts

    def turn_to_page(self, page_no):
        '''
        在进入某一帖子后，进行翻页
        :param page_no:
        :return:
        '''
        print("翻页:", page_no)
        if page_no > self.tot_pages or page_no<1:
            print(page_no, self.tot_pages)
            return None
        url_parts = urllib.parse.urlparse(self.post_url)
        url_parts = list(url_parts)
        query = dict(urllib.parse.parse_qsl(url_parts[4]))
        query.update({"pn": f"{page_no}"})
        url_parts[4] = urlencode(query)
        url = urllib.parse.urlunparse(url_parts)
        self.page_no = page_no
        print("翻页:",url)
        return self.turn_to_post(post_url=url)

'''
tieba = Tieba()
tieba.get_posts("抗压背锅")
print(tieba.turn_to_post(1))
print(tieba.tot_pages)
if tieba.tot_pages > 1:
    print(tieba.turn_to_page(2))
'''