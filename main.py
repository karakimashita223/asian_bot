from telebot import TeleBot
import os
import random
import schedule
import time
import threading
from datetime import datetime, timedelta

TOKEN = '7243199722:AAEPVoQrwEPaQgbqKUaFwicJbN_xhBXPHOU'

bot = TeleBot(TOKEN)

IMAGES_FOLDER = "images"
TEXT_FILE = "phrases.txt"

sent_images = set()
phrases = []

MY_CHAT_ID = 1355121335
scheduled_chat_id = None

# Загрузка фраз из текстового файла
def load_phrases():
    global phrases
    if os.path.exists(TEXT_FILE):
        with open(TEXT_FILE, 'r', encoding='utf-8') as file:
            phrases = [line.strip() for line in file.readlines()]
    else:
        phrases = ["Фразы не найдены. Пожалуйста, добавьте фразы в файл phrases.txt."]

def send_random_image():
    global scheduled_chat_id
    try:
        if scheduled_chat_id is not None:
            # Получаем список всех файлов в папке
            images = os.listdir(IMAGES_FOLDER)
            
            # Фильтруем список, оставляя только файлы с нужными расширениями и которые еще не отправлялись
            images = [img for img in images if img.endswith(('jpg', 'jpeg', 'png', 'gif')) and img not in sent_images]
            
            if images:
                # Выбираем случайный файл из списка
                random_image = random.choice(images)
                
                # Полный путь к файлу
                image_path = os.path.join(IMAGES_FOLDER, random_image)
                
                # Отправляем изображение
                with open(image_path, 'rb') as image_file:
                    bot.send_photo(scheduled_chat_id, image_file)
                
                # Добавляем отправленный файл в множество
                sent_images.add(random_image)
                
                # Отправляем случайную фразу
                if phrases:
                    random_phrase = random.choice(phrases)
                    bot.send_message(scheduled_chat_id, random_phrase)
                
                # Запланировать следующую отправку
                schedule_next_image()
            else:
                bot.send_message(scheduled_chat_id, "Все доступные изображения уже были отправлены.")
        else:
            print("scheduled_chat_id is None, no message will be sent.")
    except Exception as e:
        print(f"Ошибка при отправке изображения: {e}")

def schedule_next_image():
    schedule.clear('daily-task')  # Очищаем предыдущую задачу

    # Генерируем случайное время для следующего дня
    random_hour = random.randint(12, 20)
    random_minute = random.randint(0, 59)

    now = datetime.now()
    next_time = now.replace(hour=random_hour, minute=random_minute, second=0, microsecond=0)
    
    # Если случайное время уже прошло сегодня, назначаем на завтра
    if next_time <= now:
        next_time += timedelta(days=1)

    # Планируем задачу
    schedule_time_str = next_time.strftime("%H:%M")
    schedule.every().day.at(schedule_time_str).do(send_random_image).tag('daily-task')

    # Информируем пользователя о следующем времени отправки
    bot.send_message(scheduled_chat_id, f"Следующая картинка будет отправлена в {schedule_time_str}.")

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    global scheduled_chat_id
    scheduled_chat_id = message.chat.id
    bot.reply_to(message, "Бот запущен и будет отправлять случайные картинки с фразами раз в сутки в случайное время.")
    schedule_next_image()

# Функция для постоянного выполнения запланированных задач
def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Запуск планировщика задач в отдельном потоке
schedule_thread = threading.Thread(target=run_schedule)
schedule_thread.start()

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if message.chat.id == MY_CHAT_ID:
        photo = message.photo[-1]

        file_info = bot.get_file(photo.file_id)
        
        downloaded_file = bot.download_file(file_info.file_path)
                
        file_name = f"{photo.file_id}.jpg"
        file_path = os.path.join(IMAGES_FOLDER, file_name)
        
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        bot.reply_to(message, f"Картинка сохранена как {file_name}")
    else:
        bot.reply_to(message, "Извините, я могу сохранять картинки только от определенного пользователя.")

# Загрузка фраз перед запуском бота
load_phrases()

bot.polling(non_stop=True, interval=0)
