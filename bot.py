import os
import asyncio
import logging
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from telethon import TelegramClient, events
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
POST_CHANNEL_ID = int(os.getenv("TELEGRAM_CHAT_ID"))  # Канал, куда публикуются новости

# Файл для хранения данных
DATA_FILE = "data.json"

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Инициализация Telethon-клиента (используем bot_token)
client = TelegramClient("bot_session", API_ID, API_HASH).start(bot_token=API_TOKEN)

# ============================
#  ЗАГРУЗКА ДАННЫХ
# ============================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"channels": [], "blacklist": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

data = load_data()

# ============================
#  ФУНКЦИИ БОТА
# ============================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Привет! Я фильтрую новости по чёрному списку слов.\n\n"
        "📢 Команды:\n"
        "➕ `/add_channel @username` – добавить канал\n"
        "📜 `/list_channels` – список каналов\n"
        "❌ `/remove_channel @username` – удалить канал\n"
        "🛑 `/add_word слово` – добавить слово в ЧС\n"
        "✅ `/remove_word слово` – удалить слово из ЧС\n"
        "📜 `/list_words` – список запрещённых слов"
    )

# ➕ Добавление канала
@dp.message(Command("add_channel"))
async def add_channel(message: Message):
    if len(message.text.split()) < 2:
        return await message.answer("⚠️ Укажите username канала, например: `/add_channel @news`")
    
    channel = message.text.split()[1]
    if channel in data["channels"]:
        return await message.answer("🔹 Этот канал уже добавлен.")

    data["channels"].append(channel)
    save_data(data)
    await message.answer(f"✅ Канал {channel} добавлен!")

# ❌ Удаление канала
@dp.message(Command("remove_channel"))
async def remove_channel(message: Message):
    if len(message.text.split()) < 2:
        return await message.answer("⚠️ Укажите username канала, например: `/remove_channel @news`")
    
    channel = message.text.split()[1]
    if channel not in data["channels"]:
        return await message.answer("⚠️ Такого канала нет в списке.")

    data["channels"].remove(channel)
    save_data(data)
    await message.answer(f"❌ Канал {channel} удалён!")

# 📜 Список каналов
@dp.message(Command("list_channels"))
async def list_channels(message: Message):
    if not data["channels"]:
        return await message.answer("⚠️ Список каналов пуст.")
    
    channels = "\n".join(data["channels"])
    await message.answer(f"📜 Список каналов:\n{channels}")

# 🛑 Добавление слова в ЧС
@dp.message(Command("add_word"))
async def add_word(message: Message):
    if len(message.text.split()) < 2:
        return await message.answer("⚠️ Укажите слово для добавления в ЧС, например: `/add_word война`")
    
    word = message.text.split()[1].lower()
    if word in data["blacklist"]:
        return await message.answer("🔹 Это слово уже в ЧС.")

    data["blacklist"].append(word)
    save_data(data)
    await message.answer(f"🛑 Слово '{word}' добавлено в ЧС!")

# ✅ Удаление слова из ЧС
@dp.message(Command("remove_word"))
async def remove_word(message: Message):
    if len(message.text.split()) < 2:
        return await message.answer("⚠️ Укажите слово для удаления, например: `/remove_word война`")
    
    word = message.text.split()[1].lower()
    if word not in data["blacklist"]:
        return await message.answer("⚠️ Такого слова нет в ЧС.")

    data["blacklist"].remove(word)
    save_data(data)
    await message.answer(f"✅ Слово '{word}' удалено из ЧС!")

# 📜 Список запрещенных слов
@dp.message(Command("list_words"))
async def list_words(message: Message):
    if not data["blacklist"]:
        return await message.answer("⚠️ Чёрный список пуст.")
    
    words = ", ".join(data["blacklist"])
    await message.answer(f"📜 Чёрный список слов:\n{words}")

# ============================
#  ФИЛЬТРАЦИЯ И ПУБЛИКАЦИЯ
# ============================

@client.on(events.NewMessage())
async def handler(event):
    chat = await event.get_chat()
    if f"@{chat.username}" not in data["channels"]:
        return  # Пропускаем, если канал не в списке

    message_text = event.raw_text.lower()

    # Проверка на наличие запрещённых слов
    if any(word in message_text for word in data["blacklist"]):
        logging.info(f"🚫 Фильтруем сообщение из {chat.username}: {event.raw_text[:50]}...")
        return  # Пропускаем сообщение

    # Если сообщение прошло фильтр, публикуем его в канале
    await bot.send_message(POST_CHANNEL_ID, event.raw_text)
    logging.info(f"✅ Опубликовано сообщение из {chat.username}: {event.raw_text[:50]}...")

# ============================
#  ЗАПУСК БОТА
# ============================

async def main():
    logging.info("✅ Telethon успешно авторизован через bot_token!")
    await asyncio.gather(
        dp.start_polling(bot),
        client.run_until_disconnected()
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
