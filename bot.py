from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import logging
import os
from datetime import datetime

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфігурація
BOT_TOKEN = "8406711319:AAFbS0fNyOyRHdo_Ub3zZXU92E5I-6gqZmU"
WEB_APP_URL = "https://storied-daffodil-9cfeac.netlify.app"

# База даних в пам'яті (для простоти)
users_db = {}

def get_user(user_id):
    """Отримати або створити користувача"""
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
    """Команда /start"""
    user = update.effective_user
    user_data = get_user(user.id)
    
    # Перевірка реферального коду
    if context.args and len(context.args) > 0:
        try:
            referrer_id = int(context.args[0])
            if referrer_id != user.id and referrer_id in users_db:
                user_data['referrer_id'] = referrer_id
                users_db[referrer_id]['referrals'].append(user.id)
                logger.info(f"User {user.id} registered via referral from {referrer_id}")
        except ValueError:
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

Натисни кнопку "Грати" щоб почати! 👇
"""
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробка кнопок"""
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
        # Топ-5 користувачів
        top_users = sorted(users_db.items(), key=lambda x: x[1]['total_earned'], reverse=True)[:5]
        
        stats_text = "📊 **Топ-5 користувачів**\n\n"
        for i, (uid, data) in enumerate(top_users, 1):
            try:
                user_info = await context.bot.get_chat(uid)
                name = user_info.first_name
            except:
                name = "Unknown"
            
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            stats_text += f"{emoji} {name} - {data['total_earned']:.3f}₴\n"
        
        stats_text += f"\n👥 Всього користувачів: **{len(users_db)}**"
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')
    
    elif query.data == "referral":
        ref_count = len(user_data['referrals'])
        ref_earnings = sum(users_db[rid]['total_earned'] * 0.2 for rid in user_data['referrals'] if rid in users_db)
        ref_link = f"https://t.me/{context.bot.username}?start={user_id}"
        
        text = f"""
👥 **Реферальна програма**

🎁 Запрошуй друзів і отримуй **20%** від їх заробітку!

📊 Твоя статистика:
- Рефералів: **{ref_count}**
- Заробив з рефералів: **{ref_earnings:.3f}₴**

🔗 Твоє посилання:
`{ref_link}`

Надішли це посилання друзям! 👆
"""
        
        keyboard = [
            [InlineKeyboardButton("📤 Поділитись", url=f"https://t.me/share/url?url={ref_link}&text=Заробляй на перегляді реклами!")],
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
- Клік по монеті: 0.001₴
- Перегляд реклами: 0.01₴
- 20% від заробітку рефералів

📞 **Підтримка:** @YOUR_USERNAME
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
    """Обробка даних з WebApp"""
    try:
        data = update.effective_message.web_app_data.data
        user_id = update.effective_user.id
        user_data = get_user(user_id)
        
        # Парсимо дані (можна використати JSON)
        logger.info(f"Received WebApp data from {user_id}: {data}")
        
        # Тут можна обробляти дані з гри
        # Наприклад, синхронізувати баланс
        
        await update.message.reply_text("✅ Дані отримано!")
    except Exception as e:
        logger.error(f"Error processing WebApp data: {e}")

def main():
    """Головна функція"""
    # Створюємо додаток
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Додаємо обробники
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    
    # Запускаємо бота
    logger.info("Bot started!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()