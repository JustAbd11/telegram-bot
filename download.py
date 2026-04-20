import re
import logging
import asyncio
import yt_dlp
import os
import tempfile
from aiogram import Router, Bot, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from keyboards import back_keyboard, force_sub_channels_keyboard
from handlers.user import check_force_sub

router = Router()
logger = logging.getLogger(__name__)

URL_PATTERNS = {
    "tiktok": r"(tiktok\.com|vm\.tiktok\.com)",
    "instagram": r"(instagram\.com|instagr\.am)",
    "twitter": r"(twitter\.com|x\.com|t\.co)",
    "snapchat": r"(snapchat\.com|snap\.com)",
    "jaco": r"(jaco\.app|jaco\.com)",
}

PLATFORM_NAMES = {
    "tiktok": "🎵 تيك توك",
    "instagram": "📸 انستا",
    "twitter": "🐦 إكس/تويتر",
    "snapchat": "👻 سناب",
    "jaco": "🟣 جاكو",
}

def detect_platform(url: str):
    for platform, pattern in URL_PATTERNS.items():
        if re.search(pattern, url, re.IGNORECASE):
            return platform
    return None

def is_url(text: str) -> bool:
    return bool(re.search(r"https?://", text))

async def download_video(url: str) -> str | None:
    """تحميل الفيديو وإرجاع مسار الملف"""
    tmp_dir = tempfile.mkdtemp()
    output_template = os.path.join(tmp_dir, "%(id)s.%(ext)s")
    
    ydl_opts = {
        "outtmpl": output_template,
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "max_filesize": 50 * 1024 * 1024,  # 50MB حد تيليجرام
    }
    
    try:
        loop = asyncio.get_event_loop()
        
        def _download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                # تأكد من وجود الملف بامتداد mp4
                if not os.path.exists(filename):
                    filename = filename.rsplit(".", 1)[0] + ".mp4"
                return filename
        
        filename = await loop.run_in_executor(None, _download)
        return filename
    except Exception as e:
        logger.error(f"خطأ في التحميل: {e}")
        return None

@router.message(F.text & F.text.regexp(r"https?://"))
async def handle_url(message: Message, bot: Bot):
    url = message.text.strip()
    user = message.from_user
    
    # تحقق من الاشتراك الإجباري
    not_subbed = await check_force_sub(bot, user.id)
    if not_subbed:
        await message.answer(
            "⚠️ *يجب عليك الاشتراك في القنوات التالية أولاً:*",
            reply_markup=force_sub_channels_keyboard(not_subbed),
            parse_mode="Markdown"
        )
        return

    platform = detect_platform(url)
    if not platform:
        await message.answer(
            "❌ *الرابط غير مدعوم!*\n\n"
            "المنصات المدعومة:\n"
            "🎵 تيك توك | 📸 انستا | 🐦 إكس | 👻 سناب | 🟣 جاكو",
            reply_markup=back_keyboard(),
            parse_mode="Markdown"
        )
        return

    platform_name = PLATFORM_NAMES[platform]
    loading_msg = await message.answer(
        f"⏳ *جاري تحميل مقطعك من {platform_name}...*\n\n"
        "الرجاء الانتظار لحظات ✨",
        parse_mode="Markdown"
    )

    try:
        file_path = await download_video(url)
        
        if not file_path or not os.path.exists(file_path):
            await loading_msg.edit_text(
                "❌ *تعذر تحميل المقطع!*\n\n"
                "تأكد من:\n"
                "• أن الرابط صحيح ✅\n"
                "• أن المقطع عام وليس خاصاً 🔓\n"
                "• أن الرابط لم تنته صلاحيته 🔗\n\n"
                "للمساعدة تواصل مع: @JustAA2",
                reply_markup=back_keyboard(),
                parse_mode="Markdown"
            )
            return

        file_size = os.path.getsize(file_path)
        if file_size > 50 * 1024 * 1024:
            await loading_msg.edit_text(
                "❌ *حجم الملف كبير جداً!*\n\n"
                "الحد المسموح به 50MB\n"
                "للمساعدة تواصل مع: @JustAA2",
                reply_markup=back_keyboard(),
                parse_mode="Markdown"
            )
            os.remove(file_path)
            return

        await loading_msg.edit_text(
            f"✅ *تم التحميل! جاري الإرسال...*\n{platform_name}",
            parse_mode="Markdown"
        )

        video_file = FSInputFile(file_path)
        await message.answer_video(
            video=video_file,
            caption=(
                f"✅ *تم التحميل بنجاح!*\n"
                f"📲 المصدر: {platform_name}\n\n"
                f"🤖 @YourBotUsername"
            ),
            parse_mode="Markdown"
        )
        await loading_msg.delete()
        
        # تنظيف الملف
        try:
            os.remove(file_path)
            os.rmdir(os.path.dirname(file_path))
        except Exception:
            pass

    except Exception as e:
        logger.error(f"خطأ غير متوقع: {e}")
        await loading_msg.edit_text(
            "⚠️ *حدث خطأ غير متوقع!*\n\n"
            "يرجى المحاولة لاحقاً أو التواصل مع: @JustAA2",
            reply_markup=back_keyboard(),
            parse_mode="Markdown"
        )
