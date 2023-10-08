import os
import sqlite3
import threading

import pandas as pd
import telebot
from telebot import types
from dotenv import load_dotenv


load_dotenv()

# Устанавливаем токен бота из переменной окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Создаем блокировку для защиты доступа к базе данных SQLite
db_lock = threading.Lock()

# Инициализируем бота
bot = telebot.TeleBot(BOT_TOKEN)

# Создаем подключение к базе данных SQLite
with db_lock:
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()

    # Создаем таблицу, если она не существует
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            title TEXT,
            url TEXT,
            xpath TEXT
        )
    ''')
    conn.commit()

# Создаем блокировку для защиты доступа к базе данных SQLite

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    keyboard = types.InlineKeyboardMarkup()
    btn_upload_excel = types.InlineKeyboardButton(text="Загрузить Excel файл", callback_data="upload_excel")
    keyboard.add(btn_upload_excel)
    bot.send_message(message.chat.id, "Нажмите кнопку, чтобы загрузить Excel файл:", reply_markup=keyboard)


# Обработчик нажатия на кнопку для загрузки файла
@bot.callback_query_handler(func=lambda call: call.data == "upload_excel")
def upload_excel_callback(call):
    bot.send_message(call.message.chat.id, "Пожалуйста, загрузите Excel-файл выбрав файл на своем устройстве.")



# Обработчик загрузки файла от пользователя
@bot.message_handler(content_types=['document'])
def handle_document(message):
    # Проверяем, что файл имеет расширение .xlsx
    if message.document.file_name.endswith('.xlsx'):
        file_info = bot.get_file(message.document.file_id)
        file_path = file_info.file_path

        # Скачиваем файл с сервера Telegram
        downloaded_file = bot.download_file(file_path)

        # Сохраняем файл локально
        file_name = 'downloaded_excel.xlsx'
        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_file)

        # Открываем файл с помощью Pandas
        df = pd.read_excel(file_name)

        # Отправляем содержимое файла пользователю
        bot.send_message(message.chat.id, "Содержимое Excel файла:")
        bot.send_message(message.chat.id, df.to_string())

        # Здесь вы можете добавить данные в локальную базу данных SQLite
        for index, row in df.iterrows():
            title = row['title']
            url = row['url']
            xpath = row['xpath']
            with db_lock:
                with sqlite3.connect('data.db') as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        'INSERT INTO products (title, url, xpath) VALUES (?, ?, ?)',
                        (title, url, xpath)
                    )
                    conn.commit()
        # Закрываем соединение с базой данных

    else:
        bot.send_message(message.chat.id, "Пожалуйста, загрузите файл с расширением .xlsx.")


# Запускаем бота
bot.polling(none_stop=True, interval=0)
