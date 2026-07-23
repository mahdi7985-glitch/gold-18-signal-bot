import requests

# ===== توکن ربات خودت رو اینجا بذار =====
TOKEN = "255529172:JpFJkI3w2wUEM_PaF3fiACoekz6oh8alaiM"

# ===== آدرس API بله =====
url = f"https://tapi.bale.ai/bot{TOKEN}/setMyCommands"

# ===== لیست دستورات =====
commands = {
    "commands": [
        {"command": "start", "description": "خوش آمدگویی و شروع کار"},
        {"command": "help", "description": "راهنمای دستورات"},
        {"command": "price", "description": "دریافت قیمت لحظه‌ای طلا"},
        {"command": "signal", "description": "دریافت تحلیل کامل با سیگنال خرید و فروش"},
        {"command": "status", "description": "وضعیت ربات"}
    ]
}

# ===== ارسال درخواست =====
response = requests.post(url, json=commands)

# ===== نمایش نتیجه =====
print("وضعیت:", response.status_code)
print("پاسخ:", response.json())
