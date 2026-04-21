import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ConversationHandler, ContextTypes
)
from config import BOT_TOKEN
import admin
import database as db
from account_manager import login_account, extract_groups
from broadcaster import start_broadcast, stop_broadcast

# حالات المحادثة لإضافة حساب
PHONE, CODE, PASSWORD = range(3)
temp_data = {}

# ------------------- الأزرار الرئيسية -------------------
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id=None):
    """إرسال القائمة الرئيسية بالأزرار"""
    if user_id is None:
        user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("➕ إضافة حساب", callback_data="add_account")],
        [InlineKeyboardButton("📋 حساباتي", callback_data="my_accounts")],
        [InlineKeyboardButton("📡 استخراج المجموعات", callback_data="extract_groups")],
        [InlineKeyboardButton("📤 بدء النشر", callback_data="start_broadcast")],
        [InlineKeyboardButton("⏹️ إيقاف النشر", callback_data="stop_broadcast")],
        [InlineKeyboardButton("❓ المساعدة", callback_data="help")]
    ]
    # إذا كان المستخدم أدمن، نضيف زر التفعيل
    if admin.is_admin(user_id):
        keyboard.append([InlineKeyboardButton("👑 تفعيل مستخدم", callback_data="admin_activate")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🎯 *القائمة الرئيسية*\nاختر الإجراء المطلوب:"
    if isinstance(update, Update) and update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# ------------------- بدء البوت -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not admin.check_user_access(user_id):
        await update.message.reply_text("❌ غير مصرح. تواصل مع الأدمن.")
        return
    await main_menu(update, context)

# ------------------- معالج الأزرار العامة -------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    data = query.data

    if not admin.check_user_access(user_id):
        await query.edit_message_text("❌ غير مصرح. تواصل مع الأدمن.")
        return

    # قائمة الإجراءات
    if data == "add_account":
        await query.edit_message_text("📞 أرسل رقم الهاتف مع رمز البلد (مثال: +966512345678)")
        return PHONE  # بدء المحادثة

    elif data == "my_accounts":
        accounts = db.get_accounts_by_user(user_id)
        if not accounts:
            await query.edit_message_text("⚠️ لا توجد حسابات مسجلة.\nاستخدم زر ➕ إضافة حساب")
        else:
            text = "📱 *حساباتك:*\n\n"
            for acc in accounts:
                text += f"🆔 {acc['id']} — {acc['phone']}\n"
            text += "\nيمكنك حذف حساب بالضغط على معرفه (قريباً)"
            keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    elif data == "extract_groups":
        accounts = db.get_accounts_by_user(user_id)
        if not accounts:
            await query.edit_message_text("⚠️ لا توجد حسابات. أضف حساباً أولاً.")
            return
        keyboard = []
        for acc in accounts:
            keyboard.append([InlineKeyboardButton(f"📌 {acc['phone']}", callback_data=f"extract_{acc['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")])
        await query.edit_message_text("اختر الحساب لاستخراج مجموعاته:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data.startswith("extract_"):
        account_id = int(data.split("_")[1])
        await query.edit_message_text("⏳ جاري استخراج المجموعات... قد يستغرق دقيقة.")
        success, msg = await extract_groups(account_id, user_id)
        await query.edit_message_text(msg + "\n\n🔙 اضغط /start للعودة")
        return

    elif data == "start_broadcast":
        context.user_data['broadcast_step'] = 'waiting_text'
        await query.edit_message_text("📝 أرسل نص الإعلان المراد نشره:")
        return

    elif data == "stop_broadcast":
        success, msg = stop_broadcast(user_id)
        await query.edit_message_text(msg + "\n\n🔙 اضغط /start")
        return

    elif data == "help":
        text = """
📌 *الأزرار الرئيسية:*
➕ إضافة حساب → تسجيل حساب تلجرام جديد
📋 حساباتي → عرض الأرقام المسجلة
📡 استخراج المجموعات → جلب قروبات الحساب
📤 بدء النشر → إرسال إعلان لجميع المجموعات
⏹️ إيقاف النشر → إلغاء النشر الجاري

👑 *للأدمن فقط:* تفعيل مستخدمين جدد

📢 *ملاحظات:*
- كل حساب له مجموعاته المستقلة.
- يمكنك إضافة عدد غير محدود من الحسابات.
- النشر يتم من جميع الحسابات بنفس الوقت.
"""
        keyboard = [[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_to_main")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    elif data == "admin_activate":
        if not admin.is_admin(user_id):
            await query.edit_message_text("غير مصرح.")
            return
        await query.edit_message_text("👑 أرسل معرف المستخدم (user_id) ثم عدد الأيام بالصيغة:\n`123456789 30`")
        context.user_data['admin_activate'] = True
        return

    elif data == "back_to_main":
        await main_menu(update, context, user_id)
        return

# ------------------- محادثة إضافة حساب -------------------
async def add_account_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    phone = update.message.text.strip()
    temp_data[user_id] = {'phone': phone}
    await update.message.reply_text("📲 تم استلام الرقم. سيتم إرسال رمز التحقق إلى تطبيق تلجرام.\nأرسل الرمز هنا:")
    return CODE

async def add_account_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    code = update.message.text.strip()
    phone = temp_data[user_id]['phone']
    
    async def code_callback():
        return code
    
    success, client, msg = await login_account(user_id, phone, code_callback)
    if success:
        await update.message.reply_text(f"✅ {msg}\n\n🔙 اضغط /start للعودة للقائمة")
        if client:
            await client.disconnect()
    else:
        await update.message.reply_text(f"❌ {msg}\nحاول مرة أخرى باستخدام /start")
    return ConversationHandler.END

# ------------------- محادثة النشر (انتظار النص والتأخير) -------------------
async def broadcast_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if context.user_data.get('broadcast_step') == 'waiting_text':
        context.user_data['broadcast_text'] = update.message.text
        context.user_data['broadcast_step'] = 'waiting_delay'
        await update.message.reply_text("⏱️ أرسل عدد الثواني بين كل رسالة (مثال: 500):")
    elif context.user_data.get('broadcast_step') == 'waiting_delay':
        try:
            delay = int(update.message.text)
        except:
            await update.message.reply_text("❌ أرسل رقماً صحيحاً فقط.")
            return
        text = context.user_data.pop('broadcast_text')
        context.user_data.pop('broadcast_step')
        # بدء النشر في الخلفية
        asyncio.create_task(run_broadcast_and_notify(user_id, text, delay, update))
        await update.message.reply_text(f"✅ بدأ النشر بتأخير {delay} ثانية بين كل رسالة.\nاستخدم /start ثم اضغط ⏹️ إيقاف النشر إذا أردت الإلغاء.")

async def run_broadcast_and_notify(user_id, text, delay, update_obj):
    success, msg = await start_broadcast(user_id, text, delay)
    await update_obj.message.reply_text(msg + "\n\n🔙 اضغط /start للعودة")

# ------------------- محادثة تفعيل الأدمن -------------------
async def admin_activate_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('admin_activate'):
        try:
            parts = update.message.text.split()
            target_id = int(parts[0])
            days = int(parts[1])
        except:
            await update.message.reply_text("❌ صيغة خاطئة. استخدم: `123456789 30`")
            return
        admin_id = update.effective_user.id
        if not admin.is_admin(admin_id):
            await update.message.reply_text("غير مصرح.")
            return
        success, msg = admin.activate_user(admin_id, target_id, days)
        await update.message.reply_text(msg + "\n\n🔙 اضغط /start")
        context.user_data['admin_activate'] = False

# ------------------- إلغاء المحادثات -------------------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم الإلغاء. استخدم /start للقائمة الرئيسية.")
    return ConversationHandler.END

# ------------------- الرئيسي -------------------
def main():
    print("✅ تشغيل البوت بالأزرار...")
    db.init_db()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # محادثة إضافة حساب (ثلاث مراحل)
    conv_add = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^add_account$")],
        states={
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_account_phone)],
            CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_account_code)],
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    # معالج الأزرار العام (لجميع الـ callbacks)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(conv_add)
    
    # معالج استقبال النص للنشر وتفعيل الأدمن
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_text))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_activate_text))
    
    # أوامر أساسية
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    
    print("🚀 البوت يعمل الآن... اضغط Ctrl+C للإيقاف")
    app.run_polling()

if __name__ == '__main__':
    main()
