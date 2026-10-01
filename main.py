from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "البوت يعمل بنجاح!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    CallbackQueryHandler, MessageHandler, filters
)

TOKEN = "8229290474:AAGX-MRndjwESpxPE_PwqCPJ8OZvOpuVvRw"
ADMIN_ID = 7925936169
# بيانات الشام كاش
SHAM_CASH_NUMBER = "cb9f5afc5c2dfba507737215c32b71a9"  # رقم محفظتك
SHAM_CASH_NAME = " أبو فهد"     # اسمك المعتمد

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- 1. إدارة قاعدة البيانات (Database Setup) ---
def init_db():
    conn = sqlite3.connect("vip_bot.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            balance REAL DEFAULT 0.0
        )
    ''')
    conn.commit()
    conn.close()

def get_or_create_user(user_id, full_name):
    conn = sqlite3.connect("vip_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id, full_name, balance) VALUES (?, ?, ?)", (user_id, full_name, 0.0))
        conn.commit()
        balance = 0.0
    else:
        balance = row[0]
    conn.close()
    return balance

init_db()

# --- 2. إعداد أوامر القائمة الجانبية ---
async def post_init(application):
    commands = [
        BotCommand("start", "🚀 القائمة الرئيسية / الحساب"),
        BotCommand("balance", "💰 عرض رصيد الحساب"),
        BotCommand("cancel", "❌ إلغاء العملية")
    ]
    await application.bot.set_my_commands(commands)

# --- 3. الواجهة الرئيسية ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    balance = get_or_create_user(user.id, user.full_name)

    keyboard = [
        [InlineKeyboardButton("📥 إيداع (شام كاش)", callback_data="deposit"), InlineKeyboardButton("📤 سحب أرباح", callback_data="withdraw")],
        [InlineKeyboardButton("🎮 شحن حساب VIPBET", callback_data="charge_vipbet")],
        [InlineKeyboardButton("👤 حسابي والرصيد", callback_data="check_balance"), InlineKeyboardButton("📊 قائمة الأسعار", callback_data="price_list")],
        [InlineKeyboardButton("📞 الدعم الفني", callback_data="contact_support"), InlineKeyboardButton("ℹ️ عن البوت", callback_data="about_info")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"👋 **أهلاً بك في V.I.P Bot!**\n\n"
        f"🆔 **رقم حسابك:** `{user.id}`\n"
        f"💰 **رصيدك الحالي:** `{balance:,.0f}` ل.س\n\n"
        f"اختر الخدمة المطلوبة من القائمة أدناه:"
    )

    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    balance = get_or_create_user(user.id, user.full_name)
    await update.message.reply_text(f"👤 **رصيد حسابك الحالي:** `{balance:,.0f}` ل.س", parse_mode="Markdown")

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ تم إلغاء العملية الحالية والعودة للقائمة الرئيسية.")

# --- 4. التفاعل مع الأزرار ---
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    # خيار الإيداع
    if query.data == "deposit":
        msg = (
            "📥 **قسم الإيداع عبر شام كاش:**\n\n"
            f"1. حول المبلغ المطلوب إلى المحفظة: `{SHAM_CASH_NUMBER}`\n"
            f"2. اسم الحساب: **{SHAM_CASH_NAME}**\n\n"
            "✍️ **بعد التحويل:** أرسل صورة الإشعار أو رقم العملية هنا في المحادثة مباشرة ليتم إضافتها لرصيدك."
        )
        await query.message.reply_text(msg, parse_mode="Markdown")

    # خيار السحب
    elif query.data == "withdraw":
        msg = (
            "📤 **طلب سحب رصيد:**\n\n"
            "يرجى إرسال رسالة توضح:\n"
            "1. المبلغ المطلوب سحبه (ل.س).\n"
            "2. رقم محفظتك في شام كاش لاستلام المبلغ.\n\n"
            "*(اكتب التفاصيل في رسالة عادية وسيتم تحويلها للإدارة)*"
        )
        await query.message.reply_text(msg, parse_mode="Markdown")

    # خيار التحويل إلى VIPBET
    elif query.data == "charge_vipbet":
        balance = get_or_create_user(user.id, user.full_name)
        msg = (
            "🎮 **شحن حساب موقع VIPBET:**\n\n"
            f"💰 **رصيدك المتاح في البوت:** `{balance:,.0f}` ل.س\n\n"
            "لإتمام الشحن، أرسل رسالة تحتوي على:\n"
            "1. **ID حسابك في موقع VIPBET**\n"
            "2. **المبلغ المراد تحويله**\n\n"
            "مثال: `ID: 554321 - المبلغ: 50000`"
        )
        await query.message.reply_text(msg, parse_mode="Markdown")

    # عرض الرصيد والحساب
    elif query.data == "check_balance":
        balance = get_or_create_user(user.id, user.full_name)
        text = (
            f"👤 **بيانات حسابك في البوت:**\n\n"
            f"🆔 **ID الحساب:** `{user.id}`\n"
            f"👤 **الاسم:** {user.full_name}\n"
            f"💰 **الرصيد الحالي:** `{balance:,.0f}` ل.س"
        )
        await query.message.reply_text(text, parse_mode="Markdown")

    elif query.data == "price_list":
        prices_text = (
            "📊 **قائمة الخدمات والأسعار:**\n\n"
            "🔹 أقل مبلغ للإيداع: 5,000 ل.س\n"
            "🔹 أقل مبلغ للسحب: 10,000 ل.س\n"
            "🔹 تحويل فوري لحسابات VIPBET"
        )
        await query.message.reply_text(prices_text, parse_mode="Markdown")

    elif query.data == "contact_support":
        await query.message.reply_text("📞 للتواصل المباشر مع الدعم الفني: @username")

    elif query.data == "about_info":
        await query.message.reply_text("ℹ️ **V.I.P Bot**\nمنصة خدمات شحن المحافظ والتحويل لموقع VIPBET.")

    # موافقة أو رفض الأدمن
    elif query.data.startswith("approve_"):
        user_id = query.data.split("_")[1]
        await query.edit_message_text(f"✅ تم قبول الطلب ومعالجته للمستخدم `{user_id}`.")
        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text="🎉 تم التأكد من طلبك وتنفيذه بنجاح!"
            )
        except Exception as e:
            print("خطأ الإشعار:", e)

    elif query.data.startswith("reject_"):
        user_id = query.data.split("_")[1]
        await query.edit_message_text(f"❌ تم رفض الطلب للمستخدم `{user_id}`.")
        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text="❌ عذراً، تعذر تنفيذ الطلب. يرجى مراجعة الدعم الفني."
            )
        except Exception as e:
            print("خطأ الإشعار:", e)

# --- 5. استقبال الرسائل والإشعارات وتحويلها للأدمن ---
async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_name = user.full_name
    username = f"@{user.username}" if user.username else "لا يوجد"
    
    balance = get_or_create_user(user_id, user_name)

    admin_keyboard = [
        [
            InlineKeyboardButton("✅ قبول وتأفيذ", callback_data=f"approve_{user_id}"),
            InlineKeyboardButton("❌ رفض الطلب", callback_data=f"reject_{user_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(admin_keyboard)

    admin_text = (
        f"📩 **طلب جديد من مستخدم!**\n\n"
        f"👤 **المستخدم:** {user_name} ({username})\n"
        f"🆔 **ID البوت:** `{user_id}`\n"
        f"💰 **رصيده الحالي:** `{balance:,.0f}` ل.س\n\n"
        f"👇 **تفاصيل الطلب/الإشعار المرفق:**"
    )

    if update.message.photo:
        photo_id = update.message.photo[-1].file_id
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_id,
            caption=admin_text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    elif update.message.text:
        text_content = update.message.text
        full_admin_text = f"{admin_text}\n\n📝 **النص المرسل:**\n`{text_content}`"
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=full_admin_text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

    await update.message.reply_text("✅ تم استلام طلبك وبانتظار مراجعة الإدارة. سيرد عليك البوت فور المعالجة.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, handle_receipt))

    print("البوت يعمل بنجاح مع قاعدة البيانات...")
    app.run_polling()
