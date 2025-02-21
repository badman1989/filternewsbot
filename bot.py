import asyncio
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor
from telethon import TelegramClient, events

# === BOT CONFIG ===
import os

API_TOKEN = os.getenv("7542300451:AAGuMRnNwBgB3wBojfjAtVN5T4gJIFMWEFc")
API_ID = os.getenv("22046638")
API_HASH = os.getenv("c039255309530e542b97d46f3df4cf1f")
CHAT_ID = os.getenv("-1002310511779")

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
cursor.execute("""
    CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY
    )
""")
db.commit()

# === BLACKLIST FUNCTION ===
def is_blacklisted(text):
    cursor.execute("SELECT word FROM blacklist")
    blacklist_words = [row[0] for row in cursor.fetchall()]
    return any(word.lower() in text.lower() for word in blacklist_words)

# === CHANNEL MANAGEMENT ===
@dp.message_handler(commands=['add_channel'])
async def add_channel(message: Message):
    chat_id = message.get_args().strip()
    if not chat_id.startswith('-100'):
        await message.reply("Введите ID канала (начинается с -100).")
        return

    cursor.execute("INSERT OR IGNORE INTO channels (id) VALUES (?)", (int(chat_id),))
    db.commit()
    await message.reply(f"Канал {chat_id} добавлен в список.")

@dp.message_handler(commands=['remove_channel'])
async def remove_channel(message: Message):
    chat_id = message.get_args().strip()
    cursor.execute("DELETE FROM channels WHERE id = ?", (int(chat_id),))
    db.commit()
    await message.reply(f"Канал {chat_id} удалён из списка.")

@dp.message_handler(commands=['list_channels'])
async def list_channels(message: Message):
    cursor.execute("SELECT id FROM channels")
    channels = [row[0] for row in cursor.fetchall()]
    if channels:
        await message.reply("Мониторинг каналов:\n" + "\n".join(map(str, channels)))
    else:
        await message.reply("Список каналов пуст.")

# === TELETHON EVENT HANDLER ===
cursor.execute("SELECT id FROM channels")
CHANNELS = [row[0] for row in cursor.fetchall()]

@client.on(events.NewMessage(chats=CHANNELS))
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
