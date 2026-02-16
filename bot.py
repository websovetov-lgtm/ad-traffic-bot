import logging
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEB_APP_URL = os.getenv("WEB_APP_URL")
PORT = int(os.getenv("PORT", 10000))

users_db = {}

def get_user(user_id):
    if user_id not in users_db:
        users_db[user_id] = {
            'balance': 0.0,
            'total_earned': 0.0,
            'ads_watched': 0,
            'clicks': 0,
            'referrer_id': None,
            'referrals': [],
            'created_at': datetime.now()
        }
    return users_db[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = get_user(user.id)
    
    if context.args and len(context.args) > 0:
        try:
            referrer_id = int(context.args[0])
            if referrer_id != user.id and referrer_id in users_db:
                user_data['referrer_id'] = referrer_id
                users_db[referrer_id]['referrals'].append(user.id)
        except:
            pass
    
    keyboard = [
        [InlineKeyboardButton("🎮 Грати і заробляти", web_app=WebAppInfo(url=WEB_APP_URL))],
        [
            InlineKeyboardButton("💰 Баланс", callback_data="balance"),
            InlineKeyboardButton("📊 Статистика", callback_data="stats")
        ],
        [
            InlineKeyboardButton("👥 Реферали", callback_data="referral"),
            InlineKeyboardButton("ℹ️ Інфо", callback_data="info")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
👋 Привіт, {user.first_name}!

🎮 **Ad Traffic Bot** - заробляй переглядаючи рекламу!

💎 За кожен клік: 0.001₴
📺 За рекламу: 0.01₴
👥 Реферальна програма: 20%

Натисни "Грати" щоб почати! 👇
"""
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_data = get_user(user_id)
    
    if query.data == "balance":
        text = f"""
💰 **Твій баланс**

💎 Доступно: **{user_data['balance']:.3f}₴**
📊 Всього заробив: **{user_data['total_earned']:.3f}₴**
📺 Реклам переглянуто: **{user_data['ads_watched']}**
🖱 Кліків зроблено: **{user_data['clicks']}**
"""
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif query.data == "stats":
        top_users = sorted(users_db.items(), key=lambda x: x[1]['total_earned'], reverse=True)[:5]
        
        stats_text = "📊 **Топ-5 користувачів**\n\n"
        for i, (uid, data) in enumerate(top_users, 1):
            try:
                user_info = await context.bot.get_chat(uid)
                name = user_info.first_name
            except:
                name = "User"
            
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            stats_text += f"{emoji} {name} - {data['total_earned']:.3f}₴\n"
        
        stats_text += f"\n👥 Всього користувачів: **{len(users_db)}**"
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif query.data == "referral":
        ref_count = len(user_data['referrals'])
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        
        text = f"""
👥 **Реферальна програма**

🎁 Запрошуй друзів і отримуй **20%** від їх заробітку!

📊 Твоя статистика:
• Рефералів: **{ref_count}**

🔗 Твоє посилання:
`{ref_link}`

Надішли це посилання друзям! 👆
"""
        keyboard = [
            [InlineKeyboardButton("📤 Поділитись", url=f"https://t.me/share/url?url={ref_link}&text=Заробляй переглядаючи рекламу!")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif query.data == "info":
        text = """
ℹ️ **Як це працює?**

1️⃣ Натисни "🎮 Грати і заробляти"
2️⃣ Грай в гру і клікай по монеті
3️⃣ Дивись рекламу за винагороду
4️⃣ Запрошуй друзів і отримуй бонуси

💰 **Заробіток:**
• Клік по монеті: 0.001₴
• Перегляд реклами: 0.01₴
• 20% від заробітку рефералів
"""
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif query.data == "back":
        keyboard = [
            [InlineKeyboardButton("🎮 Грати і заробляти", web_app=WebAppInfo(url=WEB_APP_URL))],
            [
                InlineKeyboardButton("💰 Баланс", callback_data="balance"),
                InlineKeyboardButton("📊 Статистика", callback_data="stats")
            ],
            [
                InlineKeyboardButton("👥 Реферали", callback_data="referral"),
                InlineKeyboardButton("ℹ️ Інфо", callback_data="info")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Головне меню 👇", reply_markup=reply_markup)

async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = update.effective_message.web_app_data.data
        user_id = update.effective_user.id
        logger.info(f"WebApp data from {user_id}: {data}")
        await update.message.reply_text("✅ Дані отримано!")
    except Exception as e:
        logger.error(f"Error: {e}")

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')
    
    def log_message(self, format, *args):
        pass

def start_http_server():
    server = HTTPServer(('0.0.0.0', PORT), HealthCheckHandler)
    logger.info(f"HTTP server started on port {PORT}")
    server.serve_forever()

if __name__ == '__main__':
    logger.info("Starting bot...")
    
    http_thread = Thread(target=start_http_server, daemon=True)
    http_thread.start()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    
    logger.info("Bot started successfully!")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
