import asyncio
import os

import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8000/api/v1")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")


def build_headers(update: Update) -> dict[str, str]:
    user = update.effective_user
    if not user:
        return {}
    # Production mode: backend resolves role by telegram_id from users table.
    return {"X-Telegram-Id": str(user.id)}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Bot ready. /aml_check <address> /new_request <address> <amount> <aml_check_id>")


async def aml_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /aml_check <tron_address>")
        return
    address = context.args[0]
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            f"{BACKEND_BASE_URL}/aml/check",
            json={"address": address, "network": "TRON"},
            headers=build_headers(update),
        )
    if response.status_code != 200:
        await update.message.reply_text(f"AML error: {response.text}")
        return
    data = response.json()
    await update.message.reply_text(
        f"AML result\nrisk_level={data['risk_level']}\nrisk_score={data['risk_score']}\ncheck_id={data['check_id']}"
    )


async def new_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /new_request <tron_address> <amount> <aml_check_id>")
        return
    address, amount, aml_check_id = context.args[0], context.args[1], context.args[2]
    payload = {
        "address": address,
        "network": "TRON",
        "asset": "USDT",
        "amount": amount,
        "comment": "Created from Telegram bot",
        "aml_check_id": aml_check_id,
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(f"{BACKEND_BASE_URL}/requests", json=payload, headers=build_headers(update))
    if response.status_code not in (200, 201):
        await update.message.reply_text(f"Create request error: {response.text}")
        return
    data = response.json()
    await update.message.reply_text(f"Created: {data['request_no']} status={data['status']}")


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("Set BOT_TOKEN environment variable")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("aml_check", aml_check))
    app.add_handler(CommandHandler("new_request", new_request))
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
