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

# 🚀 Получаем переменные окружения
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

# 📡 Подключение Telethon (без запроса телефона)
client = TelegramClient("session_name", API_ID, API_HASH)

async def start_telethon():
    """Запуск Telethon-клиента без запроса номера телефона."""
    await client.start(bot_token=API_TOKEN)
    if not await client.is_user_authorized():
        raise ValueError("❌ Ошибка: Не удалось авторизовать Telethon!")
    print("✅ Telethon успешно авторизован!")

# 📥 Хендлер команды /start
@router.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Привет! Я фильтрую новости по чёрному списку слов.")

# 📥 Хендлер команды /add_channel
@router.message(Command("add_channel"))
async def add_channel(message: Message):
    await message.answer("Добавление нового канала в список...")

# 🚀 Основная функция
async def main():
    await start_telethon()
    print("🚀 Бот успешно запущен!")
    await dp.start_polling(bot)

# 🔄 Запуск бота в event loop
if __name__ == "__main__":
    asyncio.run(main())
