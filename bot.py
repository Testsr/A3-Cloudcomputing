import boto3
from boto3.dynamodb.conditions import Key, Attr

import telegram
from telegram import Update
from telegram.ext import Updater,CommandHandler,CallbackContext,ConversationHandler
updater = Updater(token='5705330965:AAGL4og7NmJDKrvKck6kkBLYZrgOlSS0lig', use_context=True)
dispatcher = updater.dispatcher
dynamodb = boto3.resource('dynamodb')
login_table = dynamodb.Table("login")
def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="""
    Hi! Please identify yourself using the identity command .""")
def update(update: Update, context: CallbackContext):
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
    if len(context.args) == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Wrong number of Params.")
        return
    stock_item=context.args[0]
    if stock_item=='':
        return None
    params = (stock_item,)
    query1 = "SELECT * from asx_stocks where stock_name=%s;"
    query2 = "SELECT * from asx_stocks where stock_code=%s;"

    with psycopg.connect(stock_table_url) as conn:
        results1=conn.execute(query1,params).fetchall()
        results2=conn.execute(query2,params).fetchall()
        if len(results1)>0:
            return results1
        elif len(results2)>0:
            return results2
        else:
            return []
    pass
def add(update: Update, context: CallbackContext):
    response=login_table.scan(
        FilterExpression=Attr("chatid").eq(update.effective_chat.id)
    )
    if response["Count"] == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Please use the ident command to identify yourself.")
        return
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Hi there, what stock would you like to watch?")


def remove(update: Update, context: CallbackContext):
    if len(context.args) == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text="No param specified")
    response = login_table.scan(
        FilterExpression=Attr("chatid").eq(update.effective_chat.id)
    )
    if response["Count"] == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text="No user has been found")
        return

    pass
def help(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="""
                             
                             """)

    pass
def main():
    start_handler = CommandHandler('start', start)
    ident_handler = CommandHandler('identity', update)
    add_handler = CommandHandler('add', add)
    remove_handler = CommandHandler('remove', remove)
    search_handler = CommandHandler('search', search)
    help_handler = CommandHandler('help', help)
    add_conv_handler = ConversationHandler(entry_points=[add_handler],
                                           states={

                                           })

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(ident_handler)
    dispatcher.add_handler(add_conv_handler)

    updater.start_polling()
    updater.idle()
main()
