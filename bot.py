import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from aiogram.types import Message
from telethon import TelegramClient
from dotenv import load_dotenv

# 🔍 Загружаем переменные окружения
load_dotenv()

# 🛠 Настройки логирования
logging.basicConfig(level=logging.INFO)

# 🚀 Получаем переменные из Railway (или .env)
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_ID = int(os.getenv("TELEGRAM_API_ID"))
API_HASH = os.getenv("TELEGRAM_API_HASH")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ✅ Проверка токена
if not API_TOKEN or len(API_TOKEN) < 40:
    raise ValueError("❌ Ошибка: Неверный TELEGRAM_BOT_TOKEN!")

print(f"✅ Длина токена: {len(API_TOKEN)} символов")
print(f"✅ Токен (первые 10 символов): {API_TOKEN[:10]}...")

# 🏗️ Инициализация aiogram
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# 📡 Подключение Telethon
client = TelegramClient("session_name", API_ID, API_HASH)

# 📌 Фильтр слов (чёрный список)
BLACKLIST = {"запрещенное_слово", "другое_слово"}

# 📥 Хендлер команды /start
@router.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Привет! Я фильтрую новости по чёрному списку слов.")

# 📥 Хендлер команды /add_channel
@router.message(Command("add_channel"))
async def add_channel_handler(message: Message):
    text = message.text.split(maxsplit=1)
    if len(text) < 2:
        await message.answer("Используйте: /add_channel @channel_username")
        return
    channel = text[1]
    await message.answer(f"Канал {channel} добавлен в список.")

# 🔍 Фильтрация и отправка сообщений
async def fetch_and_filter_news():
    async with client:
        async for message in client.iter_messages(CHAT_ID, limit=20):
            if not any(word in message.text.lower() for word in BLACKLIST):
                await bot.send_message(CHAT_ID, message.text)

# 🚀 Основная функция
async def main():
    async with client:
        print("🚀 Бот успешно запущен!")
        await dp.start_polling(bot)

# 🔄 Запуск бота в event loop
if __name__ == "__main__":
    asyncio.run(main())
