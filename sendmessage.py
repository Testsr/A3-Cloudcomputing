import httpx
import os

def lambda_handler(event,context):
    print(event["stock"])
    print(event["time"])
    print(event["chat_id"])
    api_key = os.environ['api_key']
    url = "https://api.telegram.org/bot%s/sendMessage"%api_key
    message = "Stock alert from stock %s at time %s"%(event["stock"],event["time"])
    payload = {
        "chat_id": event["chat_id"],
        "text":message
    }
    httpx.post(url, data=payload)
