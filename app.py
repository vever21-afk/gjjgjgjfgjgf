import os
from fastapi import FastAPI, Request
import requests
import openai

# ==== Конфиг ====
TELEGRAM_TOKEN = "8377982156:AAFPAx2X5tbeXxtsZ4oxS7Y8uE9o6-e6G9g"
OPENAI_API_KEY = "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"

openai.api_key = OPENAI_API_KEY

app = FastAPI()

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# ==== Маршрут для вебхука ====
@app.post("/webhook/supersecret-path-123")
async def webhook(request: Request):
    try:
        update = await request.json()
    except Exception as e:
        print("Ошибка парсинга JSON:", e)
        return {"ok": False}

    print("UPDATE:", update)

    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        user_message = update["message"]["text"]

        # Генерация ответа от GPT
        try:
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты — дружелюбный Telegram-бот."},
                    {"role": "user", "content": user_message}
                ]
            )
            reply_text = completion.choices[0].message["content"]
        except Exception as e:
            reply_text = f"Ошибка OpenAI: {e}"

        # Отправка ответа пользователю
        send_message(chat_id, reply_text)

    return {"ok": True}

# ==== Отправка сообщений в Telegram ====
def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    r = requests.post(url, json=payload)
    if r.status_code != 200:
        print(f"Ошибка отправки: {r.text}")

# ==== Healthcheck ====
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


   
   

   
