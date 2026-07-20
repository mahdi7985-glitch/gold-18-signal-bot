import requests
from config import BOT_TOKEN, CHAT_ID

def send_message(message):
    url = f"https://api.telegram.org/bot{8890210647:AAE_64GUSExXMA7klRvAzQVqtWvlU0L5EXw}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        requests.post(url, data=data, timeout=10)
        print("Message sent.")
    except Exception as e:
        print(e)
