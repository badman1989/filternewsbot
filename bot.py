import os
import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.enums import ParseMode
from telethon import TelegramClient, events
from dotenv import load_dotenv

# === ЗАГРУЖАЕМ .env ===
load_dotenv()

# === ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ===
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not API_TOKEN:
    raise ValueError("❌ Ошибка: TELEGRAM_BOT_TOKEN не загружен!")

print(f"✅ Длина токена: {len(API_TOKEN)} символов")
print(f"✅ Токен (первые 10 символов): {API_TOKEN[:10]}...")

# === ИНИЦИАЛИЗИРУЕМ БОТА ===
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# === TELETHON CLIENT ===
client = TelegramClient("news_bot", API_ID, API_HASH)

# === БАЗА ДАННЫХ ===
db = sqlite3.connect("news.db")
cursor = db.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT,
        message_id INTEGER,
        text TEXT UNIQUE
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS blacklist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT UNIQUE
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY
    )
""")
db.commit()

# === ФУНКЦИЯ ПРОВЕРКИ ЧЕРНОГО СПИСКА ===
def is_blacklisted(text):
    cursor.execute("SELECT word FROM blacklist")
    blacklist_words = [row[0] for row in cursor.fetchall()]
    return any(word.lower() in text.lower() for word in blacklist_words)

# === КОМАНДЫ ДЛЯ УПРАВЛЕНИЯ КАНАЛАМИ ===
@dp.message(commands=['add_channel'])
async def add_channel(message: Message):
    chat_id = message.text.split(maxsplit=1)[-1].strip()
    if not chat_id.startswith('-100'):
        await message.answer("Введите ID канала (начинается с -100).")
        return

    cursor.execute("INSERT OR IGNORE INTO channels (id) VALUES (?)", (int(chat_id),))
    db.commit()
    await message.answer(f"✅ Канал {chat_id} добавлен в список.")

@dp.message(commands=['remove_channel'])
async def remove_channel(message: Message):
    chat_id = message.text.split(maxsplit=1)[-1].strip()
    cursor.execute("DELETE FROM channels WHERE id = ?", (int(chat_id),))
    db.commit()
    await message.answer(f"✅ Канал {chat_id} удалён из списка.")

@dp.message(commands=['list_channels'])
async def list_channels(message: Message):
    cursor.execute("SELECT id FROM channels")
    channels = [row[0] for row in cursor.fetchall()]
    if channels:
        await message.answer("📢 Мониторинг каналов:\n" + "\n".join(map(str, channels)))
    else:
        await message.answer("❌ Список каналов пуст.")

# === ОБРАБОТЧИК СООБЩЕНИЙ ИЗ КАНАЛОВ ===
cursor.execute("SELECT id FROM channels")
CHANNELS = [row[0] for row in cursor.fetchall()]

@client.on(events.NewMessage(chats=CHANNELS))
async def news_handler(event):
    if event.is_channel:
        text = event.message.text or ""
        if is_blacklisted(text):
            return  # Игнорируем запрещённые слова
        
        cursor.execute("SELECT * FROM news WHERE text = ?", (text,))
        if cursor.fetchone():
            return  # Игнорируем дубликаты
        
        cursor.execute("INSERT INTO news (source, message_id, text) VALUES (?, ?, ?)",
                       (event.chat.title, event.message.id, text))
        db.commit()
        
        await bot.send_message(CHAT_ID, f"📰 <b>{event.chat.title}</b>\n{text}")

# === КОМАНДЫ ДЛЯ УПРАВЛЕНИЯ ЧЕРНЫМ СПИСКОМ ===
@dp.message(commands=['add_blacklist'])
async def add_blacklist(message: Message):
    word = message.text.split(maxsplit=1)[-1].strip()
    if not word:
        await message.answer("Введите слово для чёрного списка после команды.")
        return
    
    cursor.execute("INSERT OR IGNORE INTO blacklist (word) VALUES (?)", (word,))
    db.commit()
    await message.answer(f"✅ Слово '{word}' добавлено в чёрный список!")

@dp.message(commands=['remove_blacklist'])
async def remove_blacklist(message: Message):
    word = message.text.split(maxsplit=1)[-1].strip()
    cursor.execute("DELETE FROM blacklist WHERE word = ?", (word,))
    db.commit()
    await message.answer(f"✅ Слово '{word}' удалено из чёрного списка!")

@dp.message(commands=['show_blacklist'])
async def show_blacklist(message: Message):
    cursor.execute("SELECT word FROM blacklist")
    words = [row[0] for row in cursor.fetchall()]
    if words:
        await message.answer("🚫 Чёрный список: " + ", ".join(words))
    else:
        await message.answer("❌ Чёрный список пуст.")

# === СТАРТ БОТА ===
async def main():
    print("🚀 Бот запущен!")
    await client.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
