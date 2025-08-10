
import os
import io
import logging
import requests
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import openai

# === HARD-CODED KEYS (you asked for it) ===
TELEGRAM_TOKEN = "8377982156:AAFPAx2X5tbeXxtsZ4oxS7Y8uE9o6-e6G9g"
OPENAI_API_KEY = "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"
WEBHOOK_SECRET = "supersecret-path-123"
# ==========================================

openai.api_key = OPENAI_API_KEY
logging.basicConfig(level=logging.INFO)

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
TELEGRAM_FILE_API = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}"

SYSTEM_PROMPT = (
    "You are a warm, concise CBT/ACT-based mental well-being assistant. "
    "Never diagnose; avoid promises to 'cure'. Always suggest one 5-minute actionable step. "
    "If user mentions self-harm or suicidal intent, stop and show a safety protocol."
)

app = FastAPI()

def set_webhook():
    base_url = os.getenv("RENDER_EXTERNAL_URL")
    if not base_url:
        logging.warning("RENDER_EXTERNAL_URL not found; webhook won't be set automatically.")
        return
    webhook_url = f"{base_url}/webhook/{WEBHOOK_SECRET}"
    resp = requests.post(f"{TELEGRAM_API}/setWebhook", json={"url": webhook_url})
    logging.info("Webhook set to: %s | Telegram response: %s", webhook_url, resp.text)

@app.on_event("startup")
def on_startup():
    set_webhook()

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/diag")
def diag():
    # Do NOT leak full keys
    return {
        "has_token": bool(TELEGRAM_TOKEN),
        "has_openai": bool(OPENAI_API_KEY),
        "webhook_secret": WEBHOOK_SECRET[:6] + "***",
    }

def send_message(chat_id: int, text: str):
    try:
        requests.post(f"{TELEGRAM_API}/sendMessage", json={"chat_id": chat_id, "text": text})
    except Exception as e:
        logging.exception("send_message failed: %s", e)

def openai_chat_reply(user_text: str) -> str:
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
            temperature=0.6,
        )
        return resp.choices[0].message["content"].strip()
    except Exception as e:
        return f"Ошибка GPT: {e}"

def get_file_url(file_id: str) -> str:
    info = requests.get(f"{TELEGRAM_API}/getFile", params={"file_id": file_id}).json()
    if not info.get("ok"):
        raise RuntimeError(f"getFile failed: {info}")
    file_path = info["result"]["file_path"]
    return f"{TELEGRAM_FILE_API}/{file_path}"

def transcribe_voice_from_url(url: str) -> str:
    # Download voice OGG
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    ogg_bytes = io.BytesIO(r.content)
    ogg_bytes.name = "voice.ogg"
    try:
        tr = openai.Audio.transcriptions.create(
            model="whisper-1",
            file=ogg_bytes
        )
        # openai==0.28 may return dict or object
        if isinstance(tr, dict):
            return tr.get("text", "").strip()
        return getattr(tr, "text", "").strip()
    except Exception as e:
        return f"Ошибка распознавания: {e}"

@app.post("/webhook/supersecret-path-123")
async def telegram_webhook(WEBHOOK_SECRET: str, request: Request):
    if WEBHOOK_SECRET != "supersecret-path-123":
        return JSONResponse(status_code=403, content={"error": "Forbidden"})

    data = await request.json()
    logging.info("UPDATE: %s", str(data)[:800])

    msg = data.get("message", {})
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    if not chat_id:
        return {"ok": True}

    if "text" in msg:
        user_text = msg["text"]
        if user_text.strip() == "/start":
            send_message(chat_id, "Привет! Напиши текст или пришли голосовое — я отвечу и распознаю 🎧")
            return {"ok": True}
        answer = openai_chat_reply(user_text)
        send_message(chat_id, answer)
        return {"ok": True}

    if "voice" in msg:
        try:
            file_id = msg["voice"]["file_id"]
            url = get_file_url(file_id)
            text = transcribe_voice_from_url(url)
            if not text:
                send_message(chat_id, "Не смог распознать голос, попробуй короче (до ~30 сек).")
                return {"ok": True}
            answer = openai_chat_reply(text)
            send_message(chat_id, f"🗣️ Распознал: «{text}»\n\n{answer}")
        except Exception as e:
            logging.exception("Voice handling failed: %s", e)
            send_message(chat_id, "Ошибка обработки голосового. Попробуй ещё раз.")
        return {"ok": True}

    # default noop
    return {"ok": True}

# Entry for uvicorn in Docker
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
