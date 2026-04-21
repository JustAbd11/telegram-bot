import os
import asyncio
from telethon import TelegramClient, errors
from config import API_ID, API_HASH
import database as db

# مجلد حفظ الجلسات
SESSION_DIR = "sessions"
os.makedirs(SESSION_DIR, exist_ok=True)

async def login_account(user_id, phone, code_callback):
    """
    تسجيل الدخول برقم الهاتف.
    code_callback هي دالة غير متزامنة تستقبل رمز التحقق وتعيد إدخاله.
    """
    session_path = os.path.join(SESSION_DIR, f"user_{user_id}_{phone}.session")
    client = TelegramClient(session_path, API_ID, API_HASH)
    
    try:
        await client.connect()
        if not await client.is_user_authorized():
            # إرسال طلب الرمز
            await client.send_code_request(phone)
            code = await code_callback()
            try:
                await client.sign_in(phone, code)
            except errors.SessionPasswordNeededError:
                password = await code_callback("password")  # طلب كلمة مرور التحقق بخطوتين
                await client.sign_in(password=password)
        
        # حفظ الحساب في قاعدة البيانات
        db.add_account(user_id, phone, session_path)
        return True, client, "تم تسجيل الدخول بنجاح."
    except Exception as e:
        return False, None, f"خطأ: {str(e)}"

async def extract_groups(account_id, user_id):
    """استخراج جميع المجموعات التي فيها الحساب وحفظها"""
    # جلب معلومات الحساب من قاعدة البيانات
    accounts = db.get_accounts_by_user(user_id)
    account = next((a for a in accounts if a['id'] == account_id), None)
    if not account:
        return False, "الحساب غير موجود."
    
    session_path = account['session_name']
    if not os.path.exists(session_path):
        return False, "جلسة الحساب غير موجودة. أعد تسجيل الدخول."
    
    client = TelegramClient(session_path, API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        return False, "الحساب غير مصرح. أعد تسجيل الدخول."
    
    # مسح المجموعات القديمة
    db.clear_groups(account_id)
    
    count = 0
    async for dialog in client.iter_dialogs():
        if dialog.is_group:
            group_id = dialog.id
            title = dialog.name
            db.add_group(account_id, group_id, title)
            count += 1
    
    await client.disconnect()
    return True, f"تم استخراج {count} مجموعة وحفظها."

async def get_all_groups_for_user(user_id):
    """جلب جميع المجموعات لكل حسابات المستخدم"""
    accounts = db.get_accounts_by_user(user_id)
    result = {}
    for acc in accounts:
        groups = db.get_groups_by_account(acc['id'])
        result[acc['id']] = {
            'phone': acc['phone'],
            'groups': groups
        }
    return result