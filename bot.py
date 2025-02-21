import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
from telethon import TelegramClient, events

# === BOT CONFIG ===
import os

API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# === TELETHON CLIENT ===
client = TelegramClient("news_bot", API_ID, API_HASH)

# === DATABASE SETUP ===
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
db.commit()

# === BLACKLIST FUNCTION ===
def is_blacklisted(text):
    cursor.execute("SELECT word FROM blacklist")
    blacklist_words = [row[0] for row in cursor.fetchall()]
    return any(word.lower() in text.lower() for word in blacklist_words)

# === TELETHON EVENT HANDLER ===
@client.on(events.NewMessage)
async def news_handler(event):
    if event.is_channel:
        text = event.message.text or ""
        if is_blacklisted(text):
            return  # Ignore blacklisted content

        cursor.execute("SELECT * FROM news WHERE text = ?", (text,))
        if cursor.fetchone():
            return  # Ignore duplicates

        cursor.execute("INSERT INTO news (source, message_id, text) VALUES (?, ?, ?)",
                       (event.chat.title, event.message.id, text))
        db.commit()

        await bot.send_message(CHAT_ID, f"📰 **{event.chat.title}**\n{text}")

# === BOT COMMANDS ===
@dp.message_handler(commands=['start'])
async def start_command(message: Message):
    await message.reply("Привет! Я бот для фильтрации новостей. Добавьте каналы и стоп-слова.")

@dp.message_handler(commands=['add_blacklist'])
async def add_blacklist(message: Message):
    word = message.get_args().strip()
    if not word:
        await message.reply("Введите слово для чёрного списка после команды.")
        return

    cursor.execute("INSERT OR IGNORE INTO blacklist (word) VALUES (?)", (word,))
    db.commit()
    await message.reply(f"Слово '{word}' добавлено в чёрный список!")

@dp.message_handler(commands=['remove_blacklist'])
async def remove_blacklist(message: Message):
    word = message.get_args().strip()
    cursor.execute("DELETE FROM blacklist WHERE word = ?", (word,))
    db.commit()
    await message.reply(f"Слово '{word}' удалено из чёрного списка!")

@dp.message_handler(commands=['show_blacklist'])
async def show_blacklist(message: Message):
    cursor.execute("SELECT word FROM blacklist")
    words = [row[0] for row in cursor.fetchall()]
    if words:
        await message.reply("Чёрный список: " + ", ".join(words))
    else:
        await message.reply("Чёрный список пуст.")

# === MAIN ===
async def main():
    await client.start()
    executor.start_polling(dp, skip_updates=True)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
