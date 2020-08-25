from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram.ext.filters import Filters
from dialog import Dialog

dialog = Dialog()

def respond(update, context):
    msg = update.message["text"]
    response = dialog.respond(msg)
    update.message.reply_text(response)

token = '*************' #token不直接放出
updater = Updater(token, use_context=True, request_kwargs={
    'proxy_url': "http://127.0.0.1:10809"
})
updater.dispatcher.add_handler(MessageHandler(callback=respond, filters=Filters.all))

print("ready")
updater.start_polling()
updater.idle()
