# Telegram GPT Bot (Render-ready, webhook auto-setup)

- FastAPI + uvicorn
- OpenAI Chat + Whisper (voice)
- Webhook auto-setup using RENDER_EXTERNAL_URL (on Render)
- Keys embedded directly in code (as requested) — DO NOT make this repo public.

## Deploy on Render
1) Upload these files to a **private** GitHub repo.
2) On Render: New → Blueprint, pick the repo, Deploy.
3) After Live, check Logs: you should see "Webhook set to: ...".
4) Open Telegram and send /start to your bot.

## Health
- `GET /healthz` returns `{"status":"ok"}`
- `GET /diag` returns minimal info
