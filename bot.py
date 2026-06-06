import os
import sys
import logging
import time
from flask import Flask, request, abort
import telebot
import google.generativeai as genai

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_KEY_1 = os.environ.get("GEMINI_API_KEY_1")
GEMINI_KEY_2 = os.environ.get("GEMINI_API_KEY_2")
GEMINI_KEY_3 = os.environ.get("GEMINI_API_KEY_3")

if not BOT_TOKEN or not GEMINI_KEY_1:
    logger.critical("CRITICAL ERROR: 'BOT_TOKEN' or 'GEMINI_API_KEY_1' is missing!")
    sys.exit("Missing essential environment variables.")

AVAILABLE_KEYS = [k for k in [GEMINI_KEY_1, GEMINI_KEY_2, GEMINI_KEY_3] if k]
current_key_index = 0

def configure_next_gemini_key():
    global current_key_index
    selected_key = AVAILABLE_KEYS[current_key_index]
    genai.configure(api_key=selected_key)
    current_key_index = (current_key_index + 1) % len(AVAILABLE_KEYS)
    logger.info(f"Switched to Gemini API Key Index: {current_key_index}")

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)
user_chat_sessions = {}

SYSTEM_INSTRUCTION = """
You are an elite, world-class Senior Full-Stack Software Engineer and Code Architect. 
Your core design principle is to deliver FLAWLESS, production-ready, highly optimized, and bug-free code.
Strict Execution Rules:
1. Syntax & Logic Integrity: Double-check logic and indentation.
2. Code Formatting: Always use proper markdown wrappers (e.g., ```python ... ```). 
3. Documentation: Embed line-by-line precise comments in English.
4. Language: Explain in Persian (Farsi) but keep code and comments in English.
"""

def get_or_create_chat(user_id: int):
    configure_next_gemini_key()
    if user_id not in user_chat_sessions:
        user_chat_sessions[user_id] = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_INSTRUCTION,
            generation_config={"temperature": 0.2}
        ).start_chat(history=[])
    return user_chat_sessions[user_id]

@bot.message_handler(commands=['start', 'help'])
def send_welcome_message(message):
    welcome_text = (
        "🤖 **دستیار ارشد و تخصصی کدنویسی (نسخه لود بالانسر پایدار) خوش آمدید**\n\n"
        "من آماده‌ام تا کدهای بدون ایراد و تخصصی برای پروپوزال شما تولید کنم.\n"
        "✍️ سوال برنامه‌نویسی خود را بپرسید یا عکس بفرستید:"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['reset'])
def reset_memory(message):
    user_id = message.chat.id
    if user_id in user_chat_sessions:
        del user_chat_sessions[user_id]
    bot.reply_to(message, "🔄 حافظه هوش مصنوعی پاکسازی شد.")

@bot.message_handler(content_types=['photo'])
def handle_incoming_vision_request(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_bin = bot.download_file(file_info.file_path)
        
        configure_next_gemini_key()
        model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=SYSTEM_INSTRUCTION)
        
        contents = [
            {"mime_type": "image/jpeg", "data": downloaded_bin},
            message.caption if message.caption else "Analyze this code image flawlessly."
        ]
        
        raw_response = model.generate_content(contents)
        bot.reply_to(message, raw_response.text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Vision Error: {str(e)}")
        bot.reply_to(message, "❌ خطا در پردازش تصویر.")

@bot.message_handler(func=lambda message: True)
def handle_incoming_text_request(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        active_chat = get_or_create_chat(message.chat.id)
        ai_response = active_chat.send_message(message.text)
        bot.reply_to(message, ai_response.text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Text Error: {str(e)}")
        bot.reply_to(message, "❌ خطایی در پردازش رخ داد. مجدداً ارسال کنید.")

@app.route('/' + BOT_TOKEN, methods=['POST'])
def receive_telegram_updates():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    else:
        abort(403)

@app.route("/")
def index_health_check():
    bot.remove_webhook()
    time.sleep(0.1)
    secure_webhook_url = f"https://{request.host}/{BOT_TOKEN}"
    status = bot.set_webhook(url=secure_webhook_url)
    return f"Status: {'ONLINE' if status else 'ERROR'}", 200

if __name__ == "__main__":
    deployment_port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=deployment_port)
    
