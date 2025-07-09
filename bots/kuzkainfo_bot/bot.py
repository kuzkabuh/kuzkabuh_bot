import os
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

load_dotenv('/root/kuzkabuh/.env')

BOT_TOKEN = os.getenv('KUZKAINFO_BOT_TOKEN')
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST')
WEBHOOK_PATH = os.getenv('KUZKAINFO_WEBHOOK_PATH')
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
GROUP_ID = os.getenv('ADMIN_GROUP_ID')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

CBR_DAILY = "https://www.cbr-xml-daily.ru/daily_json.js"

async def fetch_currency():
    async with aiohttp.ClientSession() as session:
        async with session.get(CBR_DAILY) as resp:
            data = await resp.json()
    usd = data['Valute']['USD']['Value']
    eur = data['Valute']['EUR']['Value']
    prev_usd = data['Valute']['USD']['Previous']
    prev_eur = data['Valute']['EUR']['Previous']
    msg = (
        f"💵 Доллар: {usd:.2f} ({'+' if usd > prev_usd else ''}{usd-prev_usd:.2f})\n"
        f"💶 Евро: {eur:.2f} ({'+' if eur > prev_eur else ''}{eur-prev_eur:.2f})"
    )
    return msg

async def send_currency():
    msg = await fetch_currency()
    if GROUP_ID:
        await bot.send_message(GROUP_ID, f"Курс валют на сегодня:\n{msg}")

async def send_currency_next_day():
    msg = await fetch_currency()
    if GROUP_ID:
        await bot.send_message(GROUP_ID, f"Курс валют на завтра:\n{msg}")

@dp.message_handler(commands="start")
async def welcome(message: types.Message):
    await message.reply("Привет! Это KUZKAINFO_BOT, я работаю через Webhook.")

@dp.message_handler(content_types=types.ContentType.NEW_CHAT_MEMBERS)
async def new_user(message: types.Message):
    for user in message.new_chat_members:
        await message.reply(f"👋 Добро пожаловать, {user.first_name}! Мы рады вас видеть!")

async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    scheduler.add_job(send_currency, 'cron', hour=9, minute=0)
    scheduler.add_job(send_currency_next_day, 'cron', hour=18, minute=0)
    scheduler.start()

async def on_shutdown(dp):
    await bot.delete_webhook()

if __name__ == "__main__":
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host="0.0.0.0",
        port=8002
    )
