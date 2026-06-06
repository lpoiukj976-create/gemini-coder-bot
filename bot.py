"""
🤖 Advanced Senior-Level AI Code Architect Telegram Bot
Developed for Academic Proposal & Flawless Code Generation/Debugging.
Powered by Google Gemini 2.5 & pyTelegramBotAPI via Webhook Architecture.
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
# ۱. سیستم مانیتورینگ و لاگین سخت‌گیرانه
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ==========================================
# ۲. تایید اصالت توکن‌ها و متغیرهای محیطی
# ==========================================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not BOT_TOKEN or not GEMINI_API_KEY:
    logger.critical("CRITICAL ERROR: Environment variables 'BOT_TOKEN' or 'GEMINI_API_KEY' are missing!")
    sys.exit("Missing essential environment variables. Deployment halted.")

# مقداردهی به کلاینت‌های اصلی
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)
ai_client = genai.Client(api_key=GEMINI_API_KEY)
app = Flask(__name__)

# حافظه پایدار چت برای حفظ کامل Context و سوابق پیام‌ها
user_chat_sessions = {}

# ==========================================
# ۳. مهندسی پرامپت سیستمی (System Instruction)
# ==========================================
SYSTEM_INSTRUCTION = """
You are an elite, world-class Senior Full-Stack Software Engineer, Devops Expert, and Code Architect. 
Your core design principle is to deliver FLAWLESS, production-ready, highly optimized, and robust code.

Strict Execution Rules:
1. Syntax & Logic Integrity: Before rendering any code, perform a mental compilation to eliminate syntax errors, indentation faults (especially in Python), unclosed brackets, or logical bugs.
2. Code Formatting: Always isolate your code blocks using proper markdown wrappers with specified languages (e.g., ```python ... ```, ```javascript ... ```). 
3. Code Cleanliness & Security: Write clean, self-documenting code. Implement secure practices (e.g., input validation, preventing SQL injection/XSS where applicable).
4. Documentation: Embed line-by-line precise comments explaining complex operations or algorithmic decisions.
5. Verification Guide: At the absolute end of your response, always provide a concise 'How to Test/Execute' snippet or example output.
6. Language: If the user communicates in Persian (Farsi), reply with Persian explanations but keep the code, structural terms, and comments in English for professional standard maintenance.
"""

# ==========================================
# ۴. توابع مدیریت هوش مصنوعی (Gemini Engine)
# ==========================================
def get_or_create_session(user_id: int):
    """مدیریت و بازیابی نشست‌های فعال چت برای شبیه‌سازی سیستم حافظه"""
    if user_id not in user_chat_sessions:
        logger.info(f"Creating new expert AI chat session for User ID: {user_id}")
        user_chat_sessions[user_id] = ai_client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2,       # دمای پایین جهت تمرکز روی منطق ریاضی/فنی کاملاً دقیق و مهار پاسخ‌های فانتزی
                max_output_tokens=2048 # سقف توکن کافی برای کدهای طولانی و عمیق
            )
        )
    return user_chat_sessions[user_id]

# ==========================================
# ۵. هندلرهای تلگرام (Telegram Handlers)
# ==========================================

@bot.message_handler(commands=['start', 'help'])
def send_welcome_message(message):
    """مدیریت دستور استارت و معرفی ساختار فنی ربات"""
    welcome_text = (
        "🤖 **دستیار ارشد و تخصصی کدنویسی (AI Code Architect) خوش آمدید**\n\n"
        "این ربات به هسته پردازشی لبه‌ی تکنولوژی Google Gemini مجهز شده و برای تسک‌های زیر بهینه‌سازی شده است:\n"
        "◼️ **تولید کدهای بدون باگ:** (پایتون، جاوااسکریپت، سی‌پلاس‌پلاس، اسکویل و...)\n"
        "◼️ **دیباگ و عیب‌یابی:** کدهای اروردار خود را بفرستید تا خط‌به‌خط مهندسی معکوس شوند.\n"
        "◼️ **تحلیل بینایی ماشین (Vision):** از کدهای مانیتور، ارورهای سیستم یا نمودارها عکس بگیرید.\n"
        "◼️ **حفظ حافظه ساختاری:** ربات سوابق پیام‌های قبلی شما را در چت جاری کاملاً درک می‌کند.\n\n"
        "✍️ پروژه یا سوال خود را مطرح کنید:"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['reset'])
def reset_memory(message):
    """امکان ریست کردن حافظه چت توسط کاربر برای شروع پروژه جدید"""
    user_id = message.chat.id
    if user_id in user_chat_sessions:
        del user_chat_sessions[user_id]
    bot.reply_to(message, "🔄 حافظه هوش مصنوعی کاملاً پاکسازی شد. آمادگی برای پروژه جدید.")

@bot.message_handler(content_types=['photo'])
def handle_incoming_vision_request(message):
    """پردازش پیشرفته تصاویر حاوی قطعه کد، نمودار یا ساختار دیتابیس"""
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        logger.info(f"Processing photo from User ID: {message.chat.id}")
        
        # استخراج بالاترین کیفیت عکس ارسالی
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_bin = bot.download_file(file_info.file_path)
        
        # کپسوله‌سازی عکس در فرمت استاندارد API گوگل
        image_payload = types.Part.from_bytes(
            data=downloaded_bin,
            mime_type="image/jpeg"
        )
        
        user_prompt = message.caption if message.caption else "Analyze this code image/diagram, perform optical character recognition (OCR), detect any bugs, and rewrite it flawlessly."
        full_contents = [user_prompt, image_payload]
        
        # فراخوانی امن و بدون واسطه با ساختار Vision جمینای
        raw_response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_contents,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION)
        )
        
        bot.reply_to(message, raw_response.text, parse_mode="Markdown")
        
    except APIError as api_err:
        logger.error(f"Gemini Vision API Error: {api_err}")
        bot.reply_to(message, "❌ خطای موقت در سرور پردازش هوش مصنوعی گوگل رخ داده است. لطفاً مجدداً تلاش کنید.")
    except Exception as e:
        logger.error(f"General Photo Handler Exception: {str(e)}")
        bot.reply_to(message, "❌ پردازش تصویر با خطا مواجه شد. اطمینان حاصل کنید که فایل ارسالی خوانا باشد.")

@bot.message_handler(func=lambda message: True)
def handle_incoming_text_request(message):
    """پردازش پیام‌های متنی، برنامه‌نویسی و دیباگ با تکیه بر مکانیزم چتِ حافظه‌دار"""
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # فراخوانی نشست چت اختصاصی کاربر
        active_chat = get_or_create_session(message.chat.id)
        
        # ارسال پیام به جریان چت و دریافت پاسخ هوشمند
        ai_response = active_chat.send_message(message.text)
        
        # ارسال خروجی با فرمت مارک‌داون
        bot.reply_to(message, ai_response.text, parse_mode="Markdown")
        
    except APIError as api_err:
        logger.error(f"Gemini Text API Error: {api_err}")
        bot.reply_to(message, "❌ ارتباط با سرور هوش مصنوعی به دلیل ترافیک بالا قطع شد. لطفاً پیام خود را دوباره ارسال کنید.")
    except Exception as e:
        logger.error(f"General Text Handler Exception: {str(e)}")
        # ارسال مجدد در صورت مواجهه با خطاهای پیش‌بینی نشده تلگرام جهت پایداری بالا
        try:
            bot.reply_to(message, "⚠️ لایه امنیتی متون فعال شد. لطفاً درخواست خود را با ساختار ساده‌تری بنویسید.")
        except Exception:
            pass

# ==========================================
# ۶. راه‌اندازی وب‌هووک و لایه سرور Flask
# ==========================================
@app.route('/' + BOT_TOKEN, methods=['POST'])
def receive_telegram_updates():
    """هسته دریافت سیگنال‌های وب‌هووک از تلگرام و هدایت به بات پایتون"""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    else:
        abort(403)

@app.route("/")
def index_health_check():
    """تنظیم اتوماتیک وب‌هووک به محض پینگ شدن صفحه اصلی توسط رندر"""
    bot.remove_webhook()
    time.sleep(0.1) # وقفه کوتاه جهت پاکسازی کانال ارتباطی قدیمی
    
    # استخراج هوشمند دامین اختصاصی سرور رندر شما
    assigned_host = request.host
    secure_webhook_url = f"https://{assigned_host}/{BOT_TOKEN}"
    
    status = bot.set_webhook(url=secure_webhook_url)
    if status:
        return f"System Status: ONLINE. Webhook successfully routed to: {secure_webhook_url}", 200
    else:
        return "System Status: ERROR. Failed to lock Telegram Webhook.", 500

if __name__ == "__main__":
    # رندر متغیر PORT را تزریق می‌کند، در غیر این صورت به پورت پیش‌فرض ۵۰۰۰ سوییچ می‌شود.
    deployment_port = int(os.environ.get("PORT", 5000))
    logger.info(f"Production server is booting up on port: {deployment_port}")
    app.run(host="0.0.0.0", port=deployment_port)
  
