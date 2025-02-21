import os
import json
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_STRING = os.getenv("SESSION_STRING")
TARGET_CHANNEL_ID = os.getenv("TELEGRAM_CHAT_ID")

# Проверяем, есть ли сессия
if not SESSION_STRING:
    raise ValueError("❌ SESSION_STRING не найден! Запусти auth.py и добавь его в Railway.")

# Файл хранения данных
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

# Инициализация бота и Telethon
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Привет! Я фильтрую новости по чёрному списку слов.")

@dp.message(Command("add_channel"))
async def add_channel(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Используйте команду так: /add_channel @channel")
        return
    channel = parts[1]
    if channel not in data["channels"]:
        data["channels"].append(channel)
        save_data(data)
        await message.answer(f"Канал {channel} добавлен.")
    else:
        await message.answer("Этот канал уже есть в списке.")

@dp.message(Command("remove_channel"))
async def remove_channel(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Используйте команду так: /remove_channel @channel")
        return
    channel = parts[1]
    if channel in data["channels"]:
        data["channels"].remove(channel)
        save_data(data)
        await message.answer(f"Канал {channel} удалён.")
    else:
        await message.answer("Этого канала нет в списке.")

@dp.message(Command("add_word"))
async def add_word(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Используйте команду так: /add_word слово")
        return
    word = parts[1].lower()
    if word not in data["blacklist"]:
        data["blacklist"].append(word)
        save_data(data)
        await message.answer(f"Слово '{word}' добавлено в черный список.")
    else:
        await message.answer("Это слово уже в черном списке.")

@dp.message(Command("remove_word"))
async def remove_word(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Используйте команду так: /remove_word слово")
        return
    word = parts[1].lower()
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
            if any(word in event.raw_text.lower() for word in data["blacklist"]):
                return  # Пропускаем сообщение, если оно содержит запрещенные слова
            
            # Отправка текста + медиафайлы (если есть)
            caption = f"{event.raw_text}\n\n🔗 Источник: @{event.chat.username}"
            if event.photo:
                photo = await event.download_media()
                await bot.send_photo(TARGET_CHANNEL_ID, types.FSInputFile(photo), caption=caption)
            elif event.video:
                video = await event.download_media()
                await bot.send_video(TARGET_CHANNEL_ID, types.FSInputFile(video), caption=caption)
            elif event.document:
                document = await event.download_media()
                await bot.send_document(TARGET_CHANNEL_ID, types.FSInputFile(document), caption=caption)
            else:
                await bot.send_message(TARGET_CHANNEL_ID, caption)

async def main():
    await client.start()  # Запуск Telethon
    logger.info("✅ Telethon успешно авторизован через реальный аккаунт!")
    await dp.start_polling(bot)
    await client.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
