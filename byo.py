# byo.py
from keep_alive import keep_alive
keep_alive()  # 啟動 Flask Ping 服務

import discord
import os
import asyncio
import aiohttp
import json
from deep_translator import GoogleTranslator

TOKEN = os.getenv("TOKEN")

# 各語言對應 Webhook
language_webhooks = {
    "main": "https://discord.com/api/webhooks/XXXX/main",
    "en": "https://discord.com/api/webhooks/XXXX/en",
    "ko": "https://discord.com/api/webhooks/XXXX/ko",
    "id": "https://discord.com/api/webhooks/XXXX/id",
    "th": "https://discord.com/api/webhooks/XXXX/th",
    "pt": "https://discord.com/api/webhooks/XXXX/pt"
}

# 對應每個 webhook 的頻道 ID
webhook_channel_map = {
    "main": 123456789012345678,
    "en": 123456789012345679,
    "ko": 123456789012345680,
    "pt": 123456789012345681,
    "th": 123456789012345682,
    "id": 123456789012345683
}

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

    # 偵測語言（deep-translator 不支援直接 detect，改用 try/except）
    detected_lang = "auto"
    if original_text:
        try:
            detected_lang = GoogleTranslator(source='auto', target='en').detect(original_text)
        except:
            detected_lang = "auto"

    async with aiohttp.ClientSession() as session:
        tasks = []
        for lang, webhook_url in language_webhooks.items():
            target_channel_id = webhook_channel_map[lang]

            # 避免回傳自己訊息
            if source_channel_id == target_channel_id:
                continue

            translated_text = original_text

            try:
                if target_channel_id == webhook_channel_map["main"]:
                    # 主頻道翻譯成繁體中文
                    if detected_lang.startswith("zh"):
                        translated_text = original_text
                    else:
                        translated_text = GoogleTranslator(source='auto', target='zh-TW').translate(original_text)
                else:
                    # 其他語言頻道
                    if detected_lang.startswith(lang):
                        translated_text = original_text
                    else:
                        translated_text = GoogleTranslator(source='auto', target=lang).translate(original_text)
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
            translated_messages.add(message.id)
            print(f"翻譯完成: {original_text} → 發送到 {len(tasks)} 個頻道")

if __name__ == "__main__":
    print("🚀 正在啟動機器人...")
    client.run(TOKEN)
