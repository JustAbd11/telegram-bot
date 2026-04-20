import logging
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from config import WELCOME_MESSAGE, MAIN_MENU_TEXT, ADMIN_ID
from database import add_user, get_user_count, get_force_subs, record_force_sub_join
from keyboards import main_menu_keyboard, force_sub_channels_keyboard

router = Router()
logger = logging.getLogger(__name__)

async def check_force_sub(bot: Bot, user_id: int) -> list:
    """يرجع قائمة القنوات اللي المستخدم ما اشترك فيها"""
    channels = await get_force_subs()
    not_subbed = []
    for ch_id, ch_username, ch_title in channels:
        try:
            member = await bot.get_chat_member(ch_id, user_id)
            if member.status in ("left", "kicked"):
                not_subbed.append((ch_id, ch_username, ch_title))
            else:
                await record_force_sub_join(user_id, ch_id)
        except Exception as e:
            logger.warning(f"تعذر التحقق من القناة {ch_id}: {e}")
    return not_subbed

@router.message(CommandStart())
async def start_handler(message: Message, bot: Bot):
    user = message.from_user
    await add_user(user.id, user.username or "", user.full_name)

    # إشعار الأدمن
    count = await get_user_count()
    try:
        await bot.send_message(
            ADMIN_ID,
            f"🆕 *مستخدم جديد دخل البوت!*\n\n"
            f"👤 الاسم: {user.full_name}\n"
            f"🆔 الآيدي: `{user.id}`\n"
            f"📛 اليوزر: @{user.username or 'لا يوجد'}\n\n"
            f"📊 إجمالي الأعضاء الآن: *{count}*",
            parse_mode="Markdown"
        )
    except Exception:
        pass

    # تحقق من الاشتراك الإجباري
    not_subbed = await check_force_sub(bot, user.id)
    if not_subbed:
        await message.answer(
            "⚠️ *يجب عليك الاشتراك في القنوات التالية أولاً للاستمرار:*",
            reply_markup=force_sub_channels_keyboard(not_subbed),
            parse_mode="Markdown"
        )
        return

    name = user.first_name
    await message.answer(
        WELCOME_MESSAGE.format(name=name),
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery, bot: Bot):
    not_subbed = await check_force_sub(bot, callback.from_user.id)
    if not_subbed:
        await callback.answer("❌ لم تشترك في جميع القنوات بعد!", show_alert=True)
        await callback.message.edit_reply_markup(
            reply_markup=force_sub_channels_keyboard(not_subbed)
        )
    else:
        name = callback.from_user.first_name
        await callback.message.edit_text(
            WELCOME_MESSAGE.format(name=name),
            reply_markup=main_menu_keyboard(),
            parse_mode="Markdown"
        )

@router.callback_query(F.data == "back_main")
async def back_main_callback(callback: CallbackQuery):
    name = callback.from_user.first_name
    await callback.message.edit_text(
        MAIN_MENU_TEXT,
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "how_to_download")
async def how_to_download(callback: CallbackQuery):
    from keyboards import back_keyboard
    await callback.message.edit_text(
        "📥 *طريقة التحميل:*\n\n"
        "1️⃣ انسخ رابط المقطع من أي تطبيق\n"
        "2️⃣ أرسله مباشرةً هنا في البوت\n"
        "3️⃣ انتظر ثوانٍ وسيصلك المقطع بأعلى جودة! ✅\n\n"
        "✅ *المنصات المدعومة:*\n"
        "🎵 تيك توك | 📸 انستا | 🐦 إكس | 👻 سناب | 🟣 جاكو",
        reply_markup=back_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("platform_"))
async def platform_info(callback: CallbackQuery):
    from keyboards import back_keyboard
    platforms = {
        "platform_tiktok": ("🎵", "تيك توك", "tiktok.com"),
        "platform_instagram": ("📸", "انستا", "instagram.com"),
        "platform_twitter": ("🐦", "إكس / تويتر", "x.com أو twitter.com"),
        "platform_snapchat": ("👻", "سناب شات", "snapchat.com"),
        "platform_jaco": ("🟣", "جاكو", "jaco"),
    }
    data = callback.data
    if data in platforms:
        emoji, name, domain = platforms[data]
        await callback.message.edit_text(
            f"{emoji} *{name}*\n\n"
            f"أرسل رابط المقطع من `{domain}` وسيتم تحميله فوراً! 🚀",
            reply_markup=back_keyboard(),
            parse_mode="Markdown"
        )
