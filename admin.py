import logging
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_ID
from database import (
    get_user_count, get_today_users, get_all_users,
    add_force_sub, remove_force_sub, get_force_subs,
    get_force_sub_stats, block_user, unblock_user
)
from keyboards import admin_panel_keyboard, back_keyboard, broadcast_keyboard

router = Router()
logger = logging.getLogger(__name__)

class AdminStates(StatesGroup):
    waiting_broadcast = State()
    waiting_pin_choice = State()
    waiting_add_fsub = State()
    waiting_remove_fsub = State()
    waiting_ban_id = State()
    waiting_unban_id = State()

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# ===== لوحة الأدمن =====
@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ ليس لديك صلاحية الوصول.")
        return
    count = await get_user_count()
    await message.answer(
        f"🛠 *لوحة تحكم الأدمن*\n\n"
        f"👥 إجمالي الأعضاء: *{count}*\n\n"
        "اختر ما تريد:",
        reply_markup=admin_panel_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ ليس لديك صلاحية.", show_alert=True)
        return
    await state.clear()
    count = await get_user_count()
    await callback.message.edit_text(
        f"🛠 *لوحة تحكم الأدمن*\n\n"
        f"👥 إجمالي الأعضاء: *{count}*\n\n"
        "اختر ما تريد:",
        reply_markup=admin_panel_keyboard(),
        parse_mode="Markdown"
    )

# ===== الإحصائيات =====
@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    total = await get_user_count()
    today = await get_today_users()
    fsub_stats = await get_force_sub_stats()
    
    stats_text = (
        f"📊 *إحصائيات البوت*\n\n"
        f"👥 إجمالي الأعضاء: *{total}*\n"
        f"🆕 أعضاء اليوم: *{today}*\n"
    )
    
    if fsub_stats:
        stats_text += "\n📢 *إحصائيات الاشتراك الإجباري:*\n"
        for ch_title, count in fsub_stats:
            stats_text += f"• {ch_title}: *{count}* مشترك\n"
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=back_keyboard(),
        parse_mode="Markdown"
    )

# ===== عدد الأعضاء =====
@router.callback_query(F.data == "admin_members")
async def admin_members(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    count = await get_user_count()
    today = await get_today_users()
    await callback.message.edit_text(
        f"👥 *عدد الأعضاء*\n\n"
        f"📌 الإجمالي: *{count}* عضو\n"
        f"🆕 انضموا اليوم: *{today}* عضو",
        reply_markup=back_keyboard(),
        parse_mode="Markdown"
    )

# ===== الإذاعة =====
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_broadcast)
    await callback.message.edit_text(
        "📢 *إرسال إذاعة*\n\n"
        "أرسل الرسالة التي تريد إذاعتها لجميع المستخدمين:\n"
        "_(يدعم: نص، صورة، فيديو، ستيكر)_",
        reply_markup=back_keyboard(),
        parse_mode="Markdown"
    )

@router.message(AdminStates.waiting_broadcast)
async def receive_broadcast(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(broadcast_message_id=message.message_id)
    await state.set_state(AdminStates.waiting_pin_choice)
    
    await message.answer(
        "📌 *هل تريد تثبيت الرسالة عند الإرسال؟*",
        reply_markup=broadcast_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.in_({"broadcast_send", "broadcast_pin"}))
async def execute_broadcast(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not is_admin(callback.from_user.id):
        return
    
    pin = callback.data == "broadcast_pin"
    data = await state.get_data()
    msg_id = data.get("broadcast_message_id")
    await state.clear()
    
    users = await get_all_users()
    total = len(users)
    success = 0
    failed = 0

    progress_msg = await callback.message.edit_text(
        f"⏳ *جاري إرسال الإذاعة...*\n\n0 / {total}",
        parse_mode="Markdown"
    )

    for i, user_id in enumerate(users):
        try:
            sent = await bot.copy_message(
                chat_id=user_id,
                from_chat_id=callback.from_user.id,
                message_id=msg_id
            )
            if pin:
                try:
                    await bot.pin_chat_message(user_id, sent.message_id)
                except Exception:
                    pass
            success += 1
        except Exception:
            failed += 1
        
        # تحديث التقدم كل 50 مستخدم
        if (i + 1) % 50 == 0:
            try:
                await progress_msg.edit_text(
                    f"⏳ *جاري إرسال الإذاعة...*\n\n{i+1} / {total}",
                    parse_mode="Markdown"
                )
            except Exception:
                pass

    await progress_msg.edit_text(
        f"✅ *اكتملت الإذاعة!*\n\n"
        f"📤 إجمالي: *{total}*\n"
        f"✅ نجح: *{success}*\n"
        f"❌ فشل: *{failed}*",
        reply_markup=back_keyboard(),
        parse_mode="Markdown"
    )

# ===== الاشتراك الإجباري =====
@router.callback_query(F.data == "admin_add_fsub")
async def add_fsub_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_add_fsub)
    await callback.message.edit_text(
        "🔔 *إضافة اشتراك إجباري*\n\n"
        "أرسل معرف القناة بهذا الشكل:\n"
        "`@channel_username` أو `-100xxxxxxxxxx`\n\n"
        "_تأكد أن البوت أدمن في القناة أولاً!_",
        reply_markup=back_keyboard(),
        parse_mode="Markdown"
    )

@router.message(AdminStates.waiting_add_fsub)
async def add_fsub_execute(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    channel_input = message.text.strip()
    try:
        chat = await bot.get_chat(channel_input)
        await add_force_sub(
            str(chat.id),
            chat.username or channel_input,
            chat.title
        )
        await state.clear()
        await message.answer(
            f"✅ *تمت إضافة القناة بنجاح!*\n\n"
            f"📢 الاسم: *{chat.title}*\n"
            f"🆔 المعرف: `{chat.id}`",
            reply_markup=back_keyboard(),
            parse_mode="Markdown"
        )
    except Exception as e:
        await message.answer(
            f"❌ *خطأ:* {str(e)}\n\n"
            "تأكد أن البوت أدمن في القناة وأن المعرف صحيح.",
            reply_markup=back_keyboard(),
            parse_mode="Markdown"
        )

@router.callback_query(F.data == "admin_remove_fsub")
async def remove_fsub_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    channels = await get_force_subs()
    if not channels:
        await callback.message.edit_text(
            "📭 *لا يوجد اشتراك إجباري مضاف حالياً.*",
            reply_markup=back_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    text = "🗑 *القنوات المضافة:*\n\n"
    for ch_id, ch_username, ch_title in channels:
        text += f"• {ch_title} — `{ch_id}`\n"
    text += "\nأرسل معرف القناة لحذفها:"
    
    await state.set_state(AdminStates.waiting_remove_fsub)
    await callback.message.edit_text(text, reply_markup=back_keyboard(), parse_mode="Markdown")

@router.message(AdminStates.waiting_remove_fsub)
async def remove_fsub_execute(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    channel_id = message.text.strip()
    await remove_force_sub(channel_id)
    await state.clear()
    await message.answer(
        f"✅ *تم حذف القناة بنجاح!*\n`{channel_id}`",
        reply_markup=back_keyboard(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "admin_fsub_stats")
async def fsub_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    stats = await get_force_sub_stats()
    if not stats:
        await callback.message.edit_text(
            "📭 *لا توجد إحصائيات بعد.*",
            reply_markup=back_keyboard(),
            parse_mode="Markdown"
        )
        return
    
    text = "📈 *إحصائيات الاشتراك الإجباري:*\n\n"
    for ch_title, count in stats:
        text += f"📢 {ch_title}: *{count}* مشترك\n"
    
    await callback.message.edit_text(text, reply_markup=back_keyboard(), parse_mode="Markdown")

# ===== حظر / رفع الحظر =====
@router.callback_query(F.data == "admin_ban")
async def ban_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_ban_id)
    await callback.message.edit_text(
        "🚫 *حظر مستخدم*\n\nأرسل الآيدي الرقمي للمستخدم:",
        reply_markup=back_keyboard(),
        parse_mode="Markdown"
    )

@router.message(AdminStates.waiting_ban_id)
async def ban_execute(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        user_id = int(message.text.strip())
        await block_user(user_id)
        await state.clear()
        await message.answer(
            f"✅ *تم حظر المستخدم:* `{user_id}`",
            reply_markup=back_keyboard(),
            parse_mode="Markdown"
        )
    except ValueError:
        await message.answer("❌ الآيدي يجب أن يكون رقماً!")

@router.callback_query(F.data == "admin_unban")
async def unban_prompt(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminStates.waiting_unban_id)
    await callback.message.edit_text(
        "✅ *رفع الحظر عن مستخدم*\n\nأرسل الآيدي الرقمي للمستخدم:",
        reply_markup=back_keyboard(),
        parse_mode="Markdown"
    )

@router.message(AdminStates.waiting_unban_id)
async def unban_execute(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        user_id = int(message.text.strip())
        await unblock_user(user_id)
        await state.clear()
        await message.answer(
            f"✅ *تم رفع الحظر عن:* `{user_id}`",
            reply_markup=back_keyboard(),
            parse_mode="Markdown"
        )
    except ValueError:
        await message.answer("❌ الآيدي يجب أن يكون رقماً!")
