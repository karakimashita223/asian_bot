from flask import Flask, request
from telebot import TeleBot, types
import os
import random
import threading
import time
import schedule
from datetime import datetime, timedelta

TOKEN = os.getenv('TELEGRAM_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
PORT = int(os.getenv('PORT', 5000))

bot = TeleBot(TOKEN)
app = Flask(__name__)

IMAGES_FOLDER = "images"
TEXT_FILE = "phrases.txt"

sent_images = set()
phrases = []

MY_USER_ID = 1355121335
scheduled_chat_id = MY_USER_ID

if not os.path.exists(IMAGES_FOLDER):
    os.makedirs(IMAGES_FOLDER)

def load_phrases():
    global phrases
    if os.path.exists(TEXT_FILE):
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
                
                if phrases:
                    random_phrase = random.choice(phrases)
                    bot.send_message(scheduled_chat_id, random_phrase)
                
                schedule_next_image()
            else:
                bot.send_message(scheduled_chat_id, "Нажадь всі дівки закінчились")
        else:
            print("scheduled_chat_id is None, no message will be sent.")
    except Exception as e:
        print(f"Ошибка при отправке изображения: {e}")

def schedule_next_image():
    schedule.clear('daily-task')

    random_hour = random.randint(0, 23)
    random_minute = random.randint(0, 59)

    now = datetime.now()
    next_time = now.replace(hour=random_hour, minute=random_minute, second=0, microsecond=0)
    
    if next_time <= now:
        next_time += timedelta(days=1)

    schedule_time_str = next_time.strftime("%H:%M")
    schedule.every().day.at(schedule_time_str).do(send_random_image).tag('daily-task')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.from_user.id == MY_USER_ID:
        if f"@{BOT_USERNAME}" in message.text or message.chat.type == 'private':
            global scheduled_chat_id
            scheduled_chat_id = message.chat.id
            bot.reply_to(message, "Починаю постити дівок")
            schedule_next_image()
        else:
            bot.reply_to(message, "ідінахуй")
    else:
        bot.reply_to(message, "Вибачте, але я слухаю команди лише від свого хазяїна")

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

schedule_thread = threading.Thread(target=run_schedule)
schedule_thread.start()

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if message.from_user.id == MY_USER_ID and message.chat.type == 'private':
        photo = message.photo[-1]

        file_info = bot.get_file(photo.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
                
        file_name = f"{photo.file_id}.jpg"
        file_path = os.path.join(IMAGES_FOLDER, file_name)
        
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        bot.reply_to(message, f"Збереженно як {file_name}")
    else:
        bot.reply_to(message, "Вибачте, але я можу зберігати дівок лише від свего хазяїна".")

load_phrases()

@app.route('/' + TOKEN, methods=['POST'])
def get_message():
    json_str = request.get_data().decode('UTF-8')
    update = types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '!', 200

@app.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL + TOKEN)
    return '!', 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=PORT)
