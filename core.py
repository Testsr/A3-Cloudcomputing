import boto3
import httpx
import psycopg
import asyncio
import decimal
import os
from boto3.dynamodb.conditions import Key, Attr
from dotenv import load_dotenv
from datetime import datetime
import time
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
load_dotenv()
boto3.setup_default_session(region_name='us-east-1')
dynamodb = boto3.resource('dynamodb')
stock_url_temp = os.environ["stock_url"]
update_table = dynamodb.Table("stock_updates")


# cond = ["greater",price]
def get_price(stock_code):
    res = update_table.query(KeyConditionExpression=Key("stock_code").eq(stock_code))
    if res["Count"]==0:
        return None
    if  res["Items"][0]["price"] is not None:
        return decimal.Decimal(res["Items"][0]["price"])
    return None
async def get_updated_price(http_client,stock_code):
    stock_url = stock_url_temp.format(stock_code)
    res = await http_client.get(stock_url)

    json_res = res.json()
    if "primary_share" in json_res:
        primary_share_json = json_res["primary_share"]
        if "last_price" in primary_share_json:
            current_price = decimal.Decimal(str(primary_share_json["last_price"]))
            return current_price
    return None


async def main():
    # reieteve the data
    async with await psycopg.AsyncConnection.connect("postgresql://postgres:CmXKfwocyDjBI7VIM2ub@datastore-asx.cygdlm2jaqpj"
                         ".us-east-1.rds.amazonaws.com:5432/postgres") as aconn:

        async with aconn.cursor() as cur:
            await cur.execute("SELECT stock_code from asx_stocks")
            stock_codes = await cur.fetchall()
            i = 1
            async with httpx.AsyncClient() as client:
                for stock_code in stock_codes:
                    current_price = get_price(stock_code[0])
                    updated_price = await get_updated_price(client,stock_code[0])
                    await cur.execute("SELECT username,compare,trigger from asx_cond where stock_code=%s",
                                (stock_code[0],))
                    if updated_price != current_price:
                        print("Updated")
                        conditions = await cur.fetchall()
                        await check_conditions(client, conditions, updated_price, current_price, stock_code[0])
                        update_table.update_item(
                            Key={"stock_code": stock_code[0]},
                            UpdateExpression="SET update_time = :u, price=:p",
                            ExpressionAttributeValues={
                                ':u': datetime.now().isoformat(),
                                ':p': current_price
                            }
                        )


async def check_conditions(httpclient,conditions,updated_price,current_price,stock):
    send_message_url = "https://d0uzbtefg3.execute-api.us-east-1.amazonaws.com/default/ASXSendMessage"
    for item in conditions:
        username, cond, trigger = item
        print(item)
        login_table = dynamodb.Table("login")
        res=login_table.query(KeyConditionExpression=Key("username").eq(username))["Items"][0]
        if "chatid" not in res:
            continue
        current_time = datetime.now()
        headers = {"stock": stock, "time": current_time.strftime("%H:%M"), "chat_id":res["chatid"]}
        #retieve chat id,skip and display
        if cond == "greater":
            if updated_price>trigger and current_price<=trigger:
                print("Ready")
                await httpclient.post(send_message_url,headers=headers)
        elif cond == "less":
            if updated_price<trigger and current_price>=trigger:
                print("Ready")
                await httpclient.post(send_message_url,headers=headers)

start = time.time()
asyncio.run(main())
end=time.time()
print(end-start)