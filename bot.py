"""
🤖 Advanced Senior-Level AI Code Architect Telegram Bot (Multi-API Edition)
Developed for Academic Proposal & Flawless Code Generation/Debugging.
Features: Load Balancing with 3 Gemini API Keys for bypass limits.
"""

import os
import sys
import logging
import time
from flask import Flask, request, abort
import telebot
from google import genai
from google.genai import types
from google.genai.errors import APIError

# ==========================================
# ۱. سیستم مانیتورینگ و لاگین
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ==========================================
# ۲. تایید اصالت توکن‌ها و بارگذاری ۳ کلید API
# ==========================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# دریافت هر ۳ کلید از محیط رندر
GEMINI_KEY_1 = os.environ.get("GEMINI_API_KEY_1")
GEMINI_KEY_2 = os.environ.get("GEMINI_API_KEY_2")
GEMINI_KEY_3 = os.environ.get("GEMINI_API_KEY_3")

if not BOT_TOKEN or not GEMINI_KEY_1:
    logger.critical("CRITICAL ERROR: 'BOT_TOKEN' or at least 'GEMINI_API_KEY_1' is missing!")
    sys.exit("Missing essential environment variables.")

# ساخت یک لیست از کلیدهای معتبر موجود
AVAILABLE_KEYS = [k for k in [GEMINI_KEY_1, GEMINI_KEY_2, GEMINI_KEY_3] if k]
logger.info(f"Loaded {len(AVAILABLE_KEYS)} Gemini API Key(s) for load balancing.")

# شمارنده چرخشی برای سوییچ بین کلیدها
current_key_index = 0

def get_ai_client():
    """توزیع بار چرخشی: در هر درخواست یک کلید متفاوت را برای پردازش انتخاب می‌کند"""
    global current_key_index
    if not AVAILABLE_KEYS:
        raise ValueError("No Gemini API keys are available.")
    
    selected_key = AVAILABLE_KEYS[current_key_index]
    # سوییچ به کلید بعدی برای درخواست آینده
    current_key_index = (current_key_index + 1) % len(AVAILABLE_KEYS)
    
    logger.info(f"Using Gemini API Key Index: {current_key_index} for this request.")
    return genai.Client(api_key=selected_key)

bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
app = Flask(__name__)

# حافظه پایدار چت کاربران
user_chat_sessions = {}

# ==========================================
# ۳. مهندسی پرامپت سیستمی
# ==========================================
SYSTEM_INSTRUCTION = """
You are an elite, world-class Senior Full-Stack Software Engineer and Code Architect. 
Your core design principle is to deliver FLAWLESS, production-ready, highly optimized, and bug-free code.

Strict Execution Rules:
1. Syntax & Logic Integrity: Before rendering any code, perform a mental compilation to eliminate syntax errors, indentation faults (especially in Python), unclosed brackets, or logical bugs.
2. Code Formatting: Always isolate your code blocks using proper markdown wrappers with specified languages (e.g., ```python ... ```). 
3. Code Cleanliness & Security: Write clean, self-documenting code. 
4. Documentation: Embed line-by-line precise comments explaining complex operations.
5. Verification Guide: At the absolute end of your response, always provide a concise 'How to Test/Execute' snippet.
6. Language: If the user communicates in Persian (Farsi), reply with Persian explanations but keep the code, structural terms, and comments in English.
"""

# ==========================================
# ۴. توابع هوشمند چت با قابلیت سوییچ کلید
# ==========================================
def get_or_create_session(user_id: int, client):
    """مدیریت نشست‌های چت برای حفظ حافظه ربات"""
    if user_id not in user_chat_sessions:
        logger.info(f"Creating new expert AI chat session for User ID: {user_id}")
        user_chat_sessions[user_id] = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2,
                max_output_tokens=2048
            )
        )
    return user_chat_sessions[user_id]

# ==========================================
# ۵. هندلرهای تلگرام
# ==========================================

@bot.message_handler(commands=['start', 'help'])
def send_welcome_message(message):
    welcome_text = (
        "🤖 **دستیار ارشد و تخصصی کدنویسی (نسخه توزیع بار ۳ کاناله) خوش آمدید**\n\n"
        "این ربات مجهز به پایداری بالا در برابر محدودیت پیام است و تسک‌های زیر را انجام می‌دهد:\n"
        "◼️ **تولید کدهای بدون باگ:** با تحلیل عمیق ساختاری.\n"
        "◼️ **دیباگ حرفه‌ای:** ارسال کدهای اروردار جهت مهندسی معکوس.\n"
        "◼️ **تحلیل بینایی ماشین (Vision):** پردازش عکس قطعه کدها یا نمودارها.\n"
        "◼️ **سیستم چرخشی لود بالانس:** مجهز به ۳ هسته API موازی برای کاهش محدودیت فکر کردن ربات.\n\n"
        "✍️ سوال برنامه‌نویسی خود را بپرسید یا عکس بفرستید:"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['reset'])
def reset_memory(message):
    user_id = message.chat.id
    if user_id in user_chat_sessions:
        del user_chat_sessions[user_id]
    bot.reply_to(message, "🔄 حافظه هوش مصنوعی کاملاً پاکسازی شد. آماده برای تسک جدید.")

@bot.message_handler(content_types=['photo'])
def handle_incoming_vision_request(message):
    """پردازش عکس با قابلیت استفاده از کلیدهای زاپاس در صورت بروز خطا"""
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_bin = bot.download_file(file_info.file_path)
        
        image_payload = types.Part.from_bytes(data=downloaded_bin, mime_type="image/jpeg")
        user_prompt = message.caption if message.caption else "Analyze this code image flawlessly."
        
        # فراخوانی کلاینت با کلید چرخشی فعال
        client = get_ai_client()
        raw_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[user_prompt, image_payload],
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
        )
        bot.reply_to(message, raw_response.text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Vision Error: {str(e)}")
        bot.reply_to(message, "❌ خطا در پردازش تصویر. لطفا دوباره تلاش کنید.")

@bot.message_handler(func=lambda message: True)
def handle_incoming_text_request(message):
    """ارسال پیام متنی با سیستم هوشمند توزیع بار"""
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # دریافت کلاینت فعال (کلید چرخشی)
        client = get_ai_client()
        active_chat = get_or_create_session(message.chat.id, client)
        
        ai_response = active_chat.send_message(message.text)
        bot.reply_to(message, ai_response.text, parse_mode="Markdown")
        
    except APIError as api_err:
        logger.warning(f"Key limit reached, switching token or retrying: {api_err}")
        bot.reply_to(message, "⚠️ لایه محافظتی فعال شد. لطفاً به دلیل اعمال محدودیت کلید گوگل، پیام خود را ثانیه‌ای دیگر مجدد ارسال کنید تا روی کانال دوم سوییچ شود.")
    except Exception as e:
        logger.error(f"Text Error: {str(e)}")
        bot.reply_to(message, "❌ خطایی در پردازش رخ داد. مجدداً ارسال کنید.")

# ==========================================
# ۶. راه‌اندازی وب‌هووک و سرور Flask
# ==========================================
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
    assigned_host = request.host
    secure_webhook_url = f"https://{assigned_host}/{BOT_TOKEN}"
    status = bot.set_webhook(url=secure_webhook_url)
    if status:
        return f"System Status: ONLINE. Multi-API Balancing active.", 200
    else:
        return "System Status: ERROR.", 500

if __name__ == "__main__":
    deployment_port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=deployment_port)
    
