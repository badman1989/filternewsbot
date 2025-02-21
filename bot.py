import os
import asyncio
import logging
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
POST_CHANNEL_ID = int(os.getenv("TELEGRAM_CHAT_ID"))  # ID канала для публикаций

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Инициализация Telethon-клиента
client = TelegramClient("news_session", API_ID, API_HASH)

# Хранилище каналов и чёрного списка слов
subscribed_channels = set()
blacklist_words = {"политика", "скандал", "война"}  # Можно изменить

# ============================
#  ОБРАБОТКА КОМАНД
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

@dp.message(Command("add_channel"))
async def add_channel(message: Message):
    """ Добавляет канал в список мониторинга """
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажи юзернейм канала. Например: `/add_channel @news_channel`")
        return
    
    channel_username = args[1]
    subscribed_channels.add(channel_username)
    await message.answer(f"✅ Канал {channel_username} добавлен в список мониторинга!")

@dp.message(Command("list_channels"))
async def list_channels(message: Message):
    """ Показывает список мониторимых каналов """
    if not subscribed_channels:
        await message.answer("📭 Список каналов пуст.")
    else:
        channels = "\n".join(subscribed_channels)
        await message.answer(f"📢 Мониторю эти каналы:\n{channels}")

@dp.message(Command("remove_channel"))
async def remove_channel(message: Message):
    """ Удаляет канал из списка """
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажи юзернейм канала для удаления. Например: `/remove_channel @news_channel`")
        return
    
    channel_username = args[1]
    if channel_username in subscribed_channels:
        subscribed_channels.remove(channel_username)
        await message.answer(f"🗑️ Канал {channel_username} удалён из списка.")
    else:
        await message.answer(f"❌ Канал {channel_username} не найден в списке.")

# ============================
#  ЧЁРНЫЙ СПИСОК СЛОВ
# ============================

@dp.message(Command("add_word"))
async def add_word(message: Message):
    """ Добавляет слово в чёрный список """
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажи слово для добавления. Например: `/add_word скандал`")
        return
    
    word = args[1].lower()
    blacklist_words.add(word)
    await message.answer(f"✅ Слово `{word}` добавлено в чёрный список!")

@dp.message(Command("remove_word"))
async def remove_word(message: Message):
    """ Удаляет слово из чёрного списка """
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажи слово для удаления. Например: `/remove_word скандал`")
        return
    
    word = args[1].lower()
    if word in blacklist_words:
        blacklist_words.remove(word)
        await message.answer(f"🗑️ Слово `{word}` удалено из чёрного списка.")
    else:
        await message.answer(f"❌ Слова `{word}` нет в чёрном списке.")

@dp.message(Command("list_words"))
async def list_words(message: Message):
    """ Показывает список запрещённых слов """
    if not blacklist_words:
        await message.answer("📭 Чёрный список пуст.")
    else:
        words = "\n".join(blacklist_words)
        await message.answer(f"🚫 Запрещённые слова:\n{words}")

# ============================
#  ОБРАБОТКА НОВОСТЕЙ (TELETHON)
# ============================

@client.on(events.NewMessage)
async def news_handler(event):
    """ Фильтрует и пересылает новости в канал """
    if event.chat and event.chat.username and f"@{event.chat.username}" in subscribed_channels:
        message_text = event.raw_text.lower()

        # Фильтрация по чёрному списку слов
        if any(word in message_text for word in blacklist_words):
            logging.info(f"❌ Пост из {event.chat.username} заблокирован (фильтр)")
            return

        # Отправляем в канал
        await bot.send_message(POST_CHANNEL_ID, f"📢 Новость из {event.chat.username}:\n\n{event.raw_text}")

# ============================
#  ЗАПУСК БОТА
# ============================

async def main():
    async with client:
        await client.start()
        logging.info("✅ Telethon успешно авторизован!")

        # Запускаем Aiogram и Telethon одновременно
        await asyncio.gather(
            dp.start_polling(bot),
            client.run_until_disconnected()
        )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
