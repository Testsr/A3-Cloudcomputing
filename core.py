import boto3
import httpx
import psycopg
import decimal
from boto3.dynamodb.conditions import Key, Attr
import os
from datetime import datetime
dynamodb = boto3.resource('dynamodb')

# cond = ["greater",price]
def main():
    # reieteve the data
    stock_url_temp = os.environ["asx_stock_url"]
    with psycopg.connect("postgresql://postgres:CmXKfwocyDjBI7VIM2ub@datastore-asx.cygdlm2jaqpj"
                         ".us-east-1.rds.amazonaws.com:5432/postgres") as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT stock_code from asx_stocks")
            stock_codes = cur.fetchall()

    for stock_code in stock_codes:
        print(stock_code)
        stock_url = stock_url_temp.format(stock_code[0])
        req = httpx.get(stock_url)
        json_res = req.json()
        if "primary_share" in json_res:
            json_res = json_res["primary_share"]
            if "last_price" in json_res:
                old_price = get_current_price(stock_code[0])

                with psycopg.connect("postgresql://postgres:CmXKfwocyDjBI7VIM2ub@datastore-asx.cygdlm2jaqpj"
                                     ".us-east-1.rds.amazonaws.com:5432/postgres") as conn:
                    conditions = conn.execute("SELECT username,compare,trigger from asx_cond where stock_code=%s",stock_code).fetchall()
                main_table = dynamodb.Table("stock_updates")

                main_table.update_item(
                    Key={"stock_code": stock_code[0]},
                    UpdateExpression="SET update_time = :u, price=:p",
                    ExpressionAttributeValues={
                        ':u': datetime.now().isoformat(),
                        ':p':str(json_res["last_price"])
                    },
                )
                if old_price is not None:
                    print(old_price)
                    check_conditions(conditions,float(json_res["last_price"]),old_price,stock_code[0])



def check_conditions(conditions,current_price,previous_price,stock):
    send_message_url = "https://d0uzbtefg3.execute-api.us-east-1.amazonaws.com/default/ASXSendMessage"
    for item in conditions:
        print(type(item))

    for item in conditions:
        username, cond, price = item
        login_table = dynamodb.Table("login")
        res=login_table.query(KeyConditionExpression=Key("username").eq(username))["Items"][0]
        if "chatid" not in res:
            continue
        current_time = datetime.now()
        headers = {"stock": stock, "time": current_time.strftime("%H:%M"), "chat_id":res["chatid"]}

        #retieve chat id,skip and display
        if cond == "greater":
            if current_price>price and previous_price<=price:
                httpx.post(send_message_url,headers=headers)
                pass
        elif cond == "less":
            if current_price<price and previous_price>=price:
                httpx.post(send_message_url, headers=headers)
                pass
def get_current_price(stock_code):
    main_table = dynamodb.Table("stock_updates")
    res = main_table.query(KeyConditionExpression=Key("stock_code").eq(stock_code))
    if res["Count"]==0:
        return None
    return res["Items"][0]["price"]

main()