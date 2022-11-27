import boto3
import httpx
import psycopg
import os
dynamodb = boto3.resource('dynamodb')
url = os.environ["url"]
# cond = ["greater",price]
def main():
    # reieteve the data
    with psycopg.connect("postgresql://postgres:CmXKfwocyDjBI7VIM2ub@datastore-asx.cygdlm2jaqpj"
                         ".us-east-1.rds.amazonaws.com:5432/postgres") as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT stock_code from asx_stocks")
            stock_codes = cur.fetchall()
            cur.execute("SELECT * from asx_")

    for stock_code in stock_codes:
        url = url % stock_code[0]
        req = httpx.get(url)
        json_res = req.json()
        if "primary_share" in json_res:
            json_res = json_res["primary_share"]
            if "last_price" in json_res:
                main_table = dynamodb.Table("stocks-updates")
                main_table.put_item({
                    "stock_code": stock_code[0],
                    "price": json_res["last_price"]
                })
    main_table = dynamodb.Table("stocks-updates")
    for row in items:
        stock_code=row[0]
        check_conditions((row[1],row[2],row),get_current_price(stock_code))


def check_conditions(prices_cond,current_price,previous_price,chat_id):
    send_message_url=
    for cond,price,username in prices_cond:
        #retieve chat id,skip and display
        if cond == "greater":
            if current_price>=price and previous_price<price:
                httpx.post(send_message_url)
        elif cond == "less than":
            if current_price<=price and previous_price>price:
                httpx.post(send_message_url)

def get_current_price(stockcode):
    return 0

