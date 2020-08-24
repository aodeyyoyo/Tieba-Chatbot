'''import telepot
import telegram.utils.request
from telepot.loop import MessageLoop


proxy_url = "http://127.0.0.1:10809"
proxy = telegram.utils.request.Request(proxy_url=proxy_url)
telepot.api.set_proxy(proxy_url)
bot = telepot.Bot(token='1105635246:AAF0mhBhv4DDk23CMLEQ8oxv42nnz9LOX3U')
bot.send_message(chat_id=1295413309, text="爹")

def handle(msg):
    bot.send_message("你妈死了")

MessageLoop(bot, handle).run_forever()
'''
from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram.ext.filters import Filters


def hello(update, context):
    msg = update.message["text"]
    update.message.reply_text(
        '别叫')


updater = Updater('1105635246:AAF0mhBhv4DDk23CMLEQ8oxv42nnz9LOX3U', use_context=True, request_kwargs={
    'proxy_url': "http://127.0.0.1:10809"
})

updater.dispatcher.add_handler(MessageHandler(callback=hello, filters=Filters.all))

updater.start_polling()
updater.idle()