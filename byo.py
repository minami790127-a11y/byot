from keep_alive import keep_alive

keep_alive()  # 啟動 Flask Ping 服務

import discord
import os
from googletrans import Translator

TOKEN = os.getenv("TOKEN")

# 各語言對應 Webhook
language_webhooks = {
    "main": "https://discord.com/api/webhooks/1412374568907051118/pJd9ZBD28snF4XEJmibzb3XP003huybu1FmkbV-rCeKes32Opi4koS7TPoGZGd98ghaP",
    "en": "https://discord.com/api/webhooks/1412375789172953224/ZvwUT1Xh4CpCEKMC_NmV-IVAxSHf0wQiCqq2Qv_IuAosB2QChYd8XAaDDi1t19Y7a_vY",
    "ko": "https://discord.com/api/webhooks/1409370266290884770/t-ZdUoiXHgTGqDG5moLR_SKeILr8dFHXF6aEQ_eUzKdtt04UkVvztAwfznSG75iIXY0t",
    "id": "https://discord.com/api/webhooks/1412376593698914445/WZU35tWn8NnJ1V8gRZCDA_Nhll9MYWiZVcKR93rHTxsioaMohS9zekbemHP4ZS87eUOK",
    "th": "https://discord.com/api/webhooks/1412375635279745024/1N5uQi0Atoml7zCESec9jYEHu1lr9V9HoBkTwAsqsJh5orynd2Je8dArTlJ6WvlZjjpv",
    "pt": "https://discord.com/api/webhooks/1412379870985584650/HhwxrV7gSWbHinXHpjDV5RGIGuS69SUL3PDKBSIyshkdcjpjkUEkJbRzC27_tcu-EKHq"
}

# 對應每個 webhook 的頻道 ID
webhook_channel_map = {
    "main": 1365443913502167161,
    "en": 1409363341230604440,
    "ko": 1409364707193782302,
    "pt": 1409491789102055444,
    "th": 1409599149862686732,
    "id": 1412376571158855751
}

translator = Translator()
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# 防重複翻譯集合
translated_messages = set()

async def send_webhook(session, webhook_url, username, avatar_url, content, attachments=None):
    payload = {"username": username, "avatar_url": avatar_url, "content": content}
    if attachments:
        form = aiohttp.FormData()
        form.add_field("payload_json", json.dumps(payload))
        for filename, file_bytes in attachments:
            form.add_field("file", file_bytes, filename=filename)
        await session.post(webhook_url, data=form)
    else:
        await session.post(webhook_url, json=payload)

@client.event
async def on_ready():
    print(f"✅ Bot 已登入：{client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.id in translated_messages:
        return  # 防重複

    source_channel_id = message.channel.id
    original_text = message.content

    # 讀取附件/GIF
    attachments = []
    for att in message.attachments:
        file_bytes = await att.read()
        attachments.append((att.filename, file_bytes))

    # 偵測語言
    detected_lang = "zh-cn"
    if original_text:
        try:
            detected_lang = translator.detect(original_text).lang.lower()
        except:
            detected_lang = "zh-cn"

    async with aiohttp.ClientSession() as session:
        tasks = []
        for lang, webhook_url in language_webhooks.items():
            target_channel_id = webhook_channel_map[lang]

            # 避免回傳自己訊息
            if source_channel_id == target_channel_id:
                continue

            translated_text = original_text

            try:
                # 主頻道翻譯成繁體中文
                if target_channel_id == webhook_channel_map["main"]:
                    if detected_lang.startswith("zh"):  # 已經是中文就不翻譯
                        translated_text = original_text
                    else:
                        translated_text = translator.translate(original_text, dest="zh-tw").text
                else:
                    # 其他語言頻道翻譯成目標語言
                    # 如果來源語言就是目標語言，就不翻譯
                    if detected_lang.startswith(lang):
                        translated_text = original_text
                    else:
                        translated_text = translator.translate(original_text, dest=lang).text
            except:
                translated_text = original_text

            tasks.append(send_webhook(
                session,
                webhook_url,
                message.author.display_name,
                str(message.author.display_avatar.url),
                translated_text,
                attachments if attachments else None
            ))

        if tasks:
            await asyncio.gather(*tasks)
            translated_messages.add(message.id)  # 標記已翻譯
            print(f"翻譯完成: {original_text} → 發送到 {len(tasks)} 個頻道")

if __name__ == "__main__":
    print("🚀 正在啟動機器人...")
    keep_alive()
    client.run(TOKEN)