# Import necessary modules
from rasa_nlu.training_data import load_data
from rasa_nlu.config import RasaNLUModelConfig
from rasa_nlu.model import Trainer
from rasa_nlu import config
from Tieba import Tieba
from enum import Enum
import cn2an
import re
import random
import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import json
from urllib.parse import urlencode


'''
用于管理当前状态的枚举类
'''
class State(Enum):
    FREE = 1
    IN_TIEBA = 2
    IN_GET_POSTS = 3
    IN_POST = 4


class Dialog:
    def __init__(self, model_path="config_spacy.yml", data='train.md'):
        # Create a trainer that uses this config
        trainer = Trainer(config.load("config_spacy.yml"))
        # Load the training data
        training_data = load_data('train.md')
        # Create an interpreter by training the model
        self.interpreter = trainer.train(training_data)
        trainer = Trainer(config.load("config_spacy.yml"))
        self.tieba_interpreter = trainer.train(load_data("tieba_train.md"))
        self.tieba = Tieba()
        self.respond_dict = {"TIEBA": self.respond_tieba, "default": self.respond_default,
                             "get_posts": self.tieba.get_posts, "turn_to_post": self.tieba.turn_to_post,
                             "LAUNCH": self.launch, "QUERY": self.query, "ROUTE": self.route}

        self.state = State.FREE
        self.message_trace = []


    def interpret(self, message):
        '''
        通过训练好的rasa模型，对收到的信息进行解释
        :param message: 收到的信息
        :return: 回复的信息
        '''
        if self.state == State.FREE:
            return self.interpreter.parse(message)
        if self.state in [State.IN_TIEBA, State.IN_GET_POSTS]:
            print("在贴吧里")
            return self.tieba_interpreter.parse(message)

    def respond(self, message):
        '''
        对收到的信息做出回复，额外记录上一条消息来进行返回操作
        :param message: 收到的信息
        :return: 回复的信息
        '''
        state = self.state
        ans = self._respond(message)
        if "返回" not in message:
            self.message_trace.append({"message":message, "state": state})
        return ans

    def _respond(self, message):
        '''
        对收到的信息做出回复
        :param message: 收到的信息
        :return: 回复的信息
        '''
        if "返回" in message:
            if len(self.message_trace) >= 2:
                self.message_trace.pop(-1)
                self.state = self.message_trace[-1]["state"]
                return self.respond(self.message_trace[-1]["message"])
            message = "退出"
        if "退出" in message:
            self.state = State.FREE
            self.tieba = Tieba()
            return "已退出"
        interpreted_message = self.interpret(message)
        if self.state == State.FREE:
            intent = interpreted_message["intent"]
            entities = interpreted_message["entities"]
            if intent["name"] in self.respond_dict:
                f = self.respond_dict[intent["name"]]
                return f(entities)
            f = self.respond_dict["default"]
            return f(entities)


        if self.state == State.IN_TIEBA:
            intent = interpreted_message["intent"]
            entities = interpreted_message["entities"]
            if (intent is None and "吧" in entities[0]["value"]) or intent["name"] == "GETPOSTS":
                tieba_name = "".join(entities[0]["value"].split())
                tieba_name = tieba_name[:-1]
                self.state = State.IN_GET_POSTS
                posts = self.tieba.get_posts(tieba_name)
                ans = "   ".join(tieba_name)+"\n"
                for post in posts:
                    ans += "\n"
                    if post["author_name"] == "":
                        post["author_name"] = "匿名"
                    ans += post["author_name"] + ": " + post["title"] + "\n  "
                    ans += post["abstract"] + "\n"
                    ans += post["time"]
                    ans += "\n"

                return ans

        if self.state == State.IN_GET_POSTS:
            return self.respond_turn_to_post(message)

        if self.state == State.IN_POST:
            return self.respond_turn_to_page(message)



    def respond_tieba(self, entities):
        '''
        进入贴吧模式的回复
        :param entities: 分析出的实体集
        :return: 进入贴吧模式的回复
        '''
        self.state = State.IN_TIEBA
        return "{}".format("已进入贴吧模式")

    def respond_default(self, entities=None):
        '''
        默认回复
        :param entities: 分析出的实体集
        :return: 默认的回复
        '''
        return random.choice(["抱歉，我听不懂您在说什么", "抱歉，我不知道您在说什么", "你在说什么?"])

    def respond_turn_to_post(self, message):
        '''
        进行转到帖子的回复
        :param message: 收到的信息
        :return: 转到帖子的回复
        '''
        pattern = r"[\d零一二三四五六七八九十]+\.?[\d零一二三四五六七八九十]*"
        nos = re.findall(pattern, message)
        if len(nos) > 1:
            return self.respond_default()
        no = nos[0]
        no = cn2an.cn2an(no)
        if "倒数" in message:
            no = -no
        ans = self.tieba.turn_to_post(no)
        if ans is None:
            return "不好意思，进入帖子请输入范围内的编号"
        self.state = State.IN_POST
        data = self.tieba.turn_to_post(no)
        ans = ""
        for datum in data:
            ans += "\n**************************************\n"
            ans += "{} ({}级:{})\n".format(datum["name"], datum["level_no"], datum["level_name"])
            ans += "  {}\n".format(datum["content"])
        ans += "第{}/{}页\n".format(self.tieba.page_no, self.tieba.tot_pages)
        return ans

    def respond_turn_to_page(self, message):
        '''
        帖子翻页
        :param message: 收到的信息
        :return: 转到相应页
        '''
        pattern = r"[\d零一二三四五六七八九十]+\.?[\d零一二三四五六七八九十]*"
        nos = re.findall(pattern, message)
        if len(nos) > 1:
            return self.respond_default()
        no = nos[0]
        no = cn2an.cn2an(no)
        ans = self.tieba.turn_to_post(no)
        if ans is None:
            return "不好意思，翻页请输入正常的数字范围"
        self.state = State.IN_POST

        data = self.tieba.turn_to_page(no)
        ans = ""
        for datum in data:
            ans += "\n*************\n"
            ans += "{} ({}级:{})\n".format(datum["name"], datum["level_no"], datum["level_name"])
            ans += "  {}\n".format(datum["content"])
        ans += "第{}/{}页\n".format(self.tieba.page_no, self.tieba.tot_pages)
        return ans

    def launch(self, entities):
        '''
        执行Launch操作
        :param entities:解释出的实体集
        :return: Launch后的返回信息
        '''
        if entities is None or len(entities)==0 or "value" not in entities[0]:
            return "抱歉，无权限执行此操作"
        return "抱歉，无权限打开{}".format(entities[0]["value"])

    def query(self, entities):
        '''
        执行query操作
        :param entities:解释出的实体集
        :return: query后的返回信息
        '''
        if entities is None or len(entities) == 0 or "value" not in entities[0]:
            return "抱歉，不清楚您的查询对象，请更加具体"
        url = "https://www.baidu.com/s"
        url_parts = urllib.parse.urlparse(url)
        url_parts = list(url_parts)
        query = dict(urllib.parse.parse_qsl(url_parts[4]))
        if len(entities) == 2 and entities[0]["entity"] in ["Src", "startLoc_city"] \
                and entities[1]["entity"] in ["Dest", "endLoc_city"]:
            query.update({"wd": "{}到{}".format(entities[0]["value"], entities[1]["value"])})
            url_parts[4] = urlencode(query)
            url = urllib.parse.urlunparse(url_parts)
            return url
        query.update({"wd": "{}".format(entities[0]["value"])})
        url_parts[4] = urlencode(query)
        url = urllib.parse.urlunparse(url_parts)
        return url

    def route(self, entities):
        '''
        执行route操作
        :param entities:解释出的实体集
        :return: route后的返回信息
        '''
        print(entities)
        if entities is None or len(entities) != 1:
            return self.query(entities)
        entities[0]["value"] = "到"+entities[0]["value"]
        entities[0]["value"] = "".join(entities[0]["value"].split())
        return self.query(entities)


'''
dialog = Dialog()

while True:
    response = dialog.respond(input("CLIENT: "))
    print(response)
'''