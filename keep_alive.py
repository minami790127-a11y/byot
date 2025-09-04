from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    try:
        app.run(host='0.0.0.0', port=8080)
    except OSError:
        print("Port 8080 已被佔用，Flask 無法啟動")

def keep_alive():
    t = Thread(target=run)
    t.start()

