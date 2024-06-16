from telebot import TeleBot
import os
import random
import schedule
import time
import threading
from datetime import datetime, timedelta



TOKEN = '7243199722:AAGe25Bmfy325_uECrZEVejBrbC7pFHTeSU'
BOT_USERNAME = 'asian_everyday_bot'

bot = TeleBot(TOKEN)

IMAGES_FOLDER = "images"
TEXT_FILE = "phrases.txt"

sent_images = set()
phrases = []

MY_CHAT_ID = 1355121335
scheduled_chat_id = None


def load_phrases():
    global phrases
    with open(TEXT_FILE, 'r', encoding='utf-8') as file:
        phrases = [line.strip() for line in file.readlines()]

def send_random_image():
    global scheduled_chat_id
    try:
        if scheduled_chat_id is not None:
            images = os.listdir(IMAGES_FOLDER)

            images = [img for img in images if img.endswith(('jpg', 'jpeg', 'png', 'gif')) and img not in sent_images]

            if images:
                random_image = random.choice(images)

                image_path = os.path.join(IMAGES_FOLDER, random_image)

                with open(image_path, 'rb') as image_file:
                    bot.send_photo(scheduled_chat_id, image_file)

                sent_images.add(random_image)

                random_phrase = random.choice(phrases)
                bot.send_message(scheduled_chat_id, random_phrase)

                schedule_next_image()
            else:
                bot.send_message(scheduled_chat_id, "Нажаль всі дівки закінчились😭")
        else:
            print("scheduled_chat_id is None, no message will be sent.")
    except Exception as e:
        print(f"Помилка: {e}")

def schedule_next_image():
    schedule.clear('daily-task')

    random_hour = random.randint(6, 6)
    random_minute = random.randint(0, 59)

    now = datetime.now()
    next_time = now.replace(hour=random_hour, minute=random_minute, second=0, microsecond=0)

    if next_time <= now:
        next_time += timedelta(days=1)

    schedule_time_str = next_time.strftime("%H:%M")
    schedule.every().day.at(schedule_time_str).do(send_random_image).tag('daily-task')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.from_user.id == MY_CHAT_ID:
        if f"@{BOT_USERNAME}" in message.text:
            global scheduled_chat_id
            scheduled_chat_id = message.chat.id
            bot.reply_to(message, "Починаю постити дівок❤️")
            schedule_next_image()
        else:
            bot.reply_to(message, "ідінахуй @username.")
    else:
        bot.reply_to(message, "Вибачте, але я слухаю команди лише від своего хазяїна😇")


def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)


schedule_thread = threading.Thread(target=run_schedule)
schedule_thread.start()

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if message.from_user.id == MY_CHAT_ID and message.chat.type == 'private':
        photo = message.photo[-1]

        file_info = bot.get_file(photo.file_id)

        downloaded_file = bot.download_file(file_info.file_path)

        file_name = f"{photo.file_id}.jpg"
        file_path = os.path.join(IMAGES_FOLDER, file_name)

        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        bot.reply_to(message, f"Збереженно як {file_name}")


load_phrases()

bot.polling(non_stop=True, interval=0)
