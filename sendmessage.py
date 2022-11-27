import httpx
import os


def lambda_handler(event, context):
    headers = event["headers"]
    api_key = os.environ['api_key']
    url = "https://api.telegram.org/bot%s/sendMessage" % api_key
    message = "Stock alert from stock %s at time %s" % (headers["stock"], headers["time"])
    payload = {
        "chat_id": headers["chat_id"],
        "text": message
    }
    httpx.post(url, data=payload)
    response = {"statusCode": 200}
    return response
