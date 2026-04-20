from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def main_menu_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📥 تحميل مقطع", callback_data="how_to_download"),
        ],
        [
            InlineKeyboardButton(text="🎵 تيك توك", callback_data="platform_tiktok"),
            InlineKeyboardButton(text="📸 انستا", callback_data="platform_instagram"),
        ],
        [
            InlineKeyboardButton(text="🐦 إكس/تويتر", callback_data="platform_twitter"),
            InlineKeyboardButton(text="👻 سناب", callback_data="platform_snapchat"),
        ],
        [
            InlineKeyboardButton(text="🟣 جاكو", callback_data="platform_jaco"),
        ],
        [
            InlineKeyboardButton(text="📞 تواصل مع المطور", url="https://t.me/JustAA2"),
        ],
    ])
    return keyboard

def admin_panel_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton(text="📢 إرسال إذاعة", callback_data="admin_broadcast"),
            InlineKeyboardButton(text="👥 عدد الأعضاء", callback_data="admin_members"),
        ],
        [
            InlineKeyboardButton(text="🔔 إضافة اشتراك إجباري", callback_data="admin_add_fsub"),
            InlineKeyboardButton(text="🗑 حذف اشتراك إجباري", callback_data="admin_remove_fsub"),
        ],
        [
            InlineKeyboardButton(text="📈 إحصائيات الاشتراك الإجباري", callback_data="admin_fsub_stats"),
        ],
        [
            InlineKeyboardButton(text="🚫 حظر مستخدم", callback_data="admin_ban"),
            InlineKeyboardButton(text="✅ رفع الحظر", callback_data="admin_unban"),
        ],
        [
            InlineKeyboardButton(text="🔙 رجوع", callback_data="back_main"),
        ],
    ])
    return keyboard

def back_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 رجوع للقائمة", callback_data="back_main")]
    ])
    return keyboard

def broadcast_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📌 إرسال وتثبيت", callback_data="broadcast_pin"),
            InlineKeyboardButton(text="📨 إرسال فقط", callback_data="broadcast_send"),
        ],
        [InlineKeyboardButton(text="❌ إلغاء", callback_data="admin_panel")]
    ])
    return keyboard

def confirm_keyboard(action: str):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ تأكيد", callback_data=f"confirm_{action}"),
            InlineKeyboardButton(text="❌ إلغاء", callback_data="admin_panel"),
        ]
    ])
    return keyboard

def force_sub_channels_keyboard(channels: list):
    buttons = []
    for ch_id, ch_username, ch_title in channels:
        buttons.append([
            InlineKeyboardButton(
                text=f"✅ {ch_title}",
                url=f"https://t.me/{ch_username.lstrip('@')}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="🔄 تحقق من الاشتراك", callback_data="check_sub")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
