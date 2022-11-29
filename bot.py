import boto3
from boto3.dynamodb.conditions import Key, Attr

import telegram
from telegram import Update
from telegram.ext import Updater,CommandHandler,CallbackContext
updater = Updater(token='5705330965:AAGL4og7NmJDKrvKck6kkBLYZrgOlSS0lig', use_context=True)
dispatcher = updater.dispatcher

def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hi! Please identify yourself using the ident command with the random key passed in.")
def update(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id,text="Processing")
    if len(context.args) == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text="No param specified")
        return
    first_arg=context.args[0]
    dynamodb = boto3.resource('dynamodb')
    login_table = dynamodb.Table("login")
    response=login_table.scan(
        FilterExpression=Attr("ident_str").eq(first_arg)
    )
    print(response)
    if response["Count"] == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text="No user has been found")
        return
    username = response["Items"][0]['username']
    response = login_table.update_item(Key = {'username':username},UpdateExpression="SET chatid = :c REMOVE ident_str",
                                       ExpressionAttributeValues={
                                           ':c':update.effective_chat.id
                                       },
                                       )
    context.bot.send_message(chat_id=update.effective_chat.id, text="You have sucessfully registered with the system.")
def search(update: Update, context: CallbackContext):
    pass
def add_alert(update: Update, context: CallbackContext):
    pass
def send_alert(update: Update, context: CallbackContext):
    pass
def remove_alert(update: Update, context: CallbackContext):
    pass
start_handler = CommandHandler('start', start)
ident_handler = CommandHandler('identity', update)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(ident_handler)
updater.start_polling()
updater.idle()

