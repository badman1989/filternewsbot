import asyncio
import logging
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from telethon import TelegramClient, events
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
TARGET_CHANNEL_ID = os.getenv("TELEGRAM_CHAT_ID")

# Файл для хранения данных
DATA_FILE = "channels_and_blacklist.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"channels": [], "blacklist": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

data = load_data()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация aiogram
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Инициализация Telethon
client = TelegramClient("session", API_ID, API_HASH)

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Привет! Я фильтрую новости по чёрному списку слов.")

@dp.message(Command("add_channel"))
async def add_channel(message: Message):
    if not message.text.split():
        await message.answer("Используйте команду так: /add_channel @channel")
        return
    channel = message.text.split()[1]
    if channel not in data["channels"]:
        data["channels"].append(channel)
        save_data(data)
        await message.answer(f"Канал {channel} добавлен.")
    else:
        await message.answer("Этот канал уже есть в списке.")

@dp.message(Command("remove_channel"))
async def remove_channel(message: Message):
    if not message.text.split():
        await message.answer("Используйте команду так: /remove_channel @channel")
        return
    channel = message.text.split()[1]
    if channel in data["channels"]:
        data["channels"].remove(channel)
        save_data(data)
        await message.answer(f"Канал {channel} удалён.")
    else:
        await message.answer("Этого канала нет в списке.")

@dp.message(Command("add_word"))
async def add_word(message: Message):
    word = message.text.split()[1].lower()
    if word not in data["blacklist"]:
        data["blacklist"].append(word)
        save_data(data)
        await message.answer(f"Слово '{word}' добавлено в черный список.")
    else:
        await message.answer("Это слово уже в черном списке.")

@dp.message(Command("remove_word"))
async def remove_word(message: Message):
    word = message.text.split()[1].lower()
    if word in data["blacklist"]:
        data["blacklist"].remove(word)
        save_data(data)
        await message.answer(f"Слово '{word}' удалено из черного списка.")
    else:
        await message.answer("Этого слова нет в черном списке.")

@client.on(events.NewMessage)
async def handler(event):
    for channel in data["channels"]:
        if event.chat and event.chat.username == channel.replace("@", ""):
            if not any(word in event.raw_text.lower() for word in data["blacklist"]):
                await bot.send_message(TARGET_CHANNEL_ID, event.raw_text)

async def main():
    await client.start(bot_token=API_TOKEN)
    logger.info("✅ Telethon успешно авторизован через bot_token!")
    await dp.start_polling(bot)
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
