import asyncio
import random
from telethon import TelegramClient, errors
from config import API_ID, API_HASH
import database as db

# متغيرات عامة للتحكم بعملية النشر
running_broadcasts = {}  # key: user_id, value: asyncio.Task أو flag

async def start_broadcast(user_id, message_text, delay_seconds):
    """
    بدء عملية النشر لجميع حسابات المستخدم وجميع المجموعات.
    delay_seconds: التأخير بين كل رسالة وأخرى.
    """
    if user_id in running_broadcasts and running_broadcasts[user_id]:
        return False, "يوجد عملية نشر قيد التشغيل حالياً. أوقفها أولاً."
    
    # جلب جميع حسابات المستخدم مع مجموعاتها
    accounts = db.get_accounts_by_user(user_id)
    if not accounts:
        return False, "لا توجد حسابات مسجلة لك."
    
    all_tasks = []
    for acc in accounts:
        groups = db.get_groups_by_account(acc['id'])
        if not groups:
            continue
        session_path = acc['session_name']
        if not os.path.exists(session_path):
            continue
        client = TelegramClient(session_path, API_ID, API_HASH)
        await client.connect()
        if not await client.is_user_authorized():
            await client.disconnect()
            continue
        
        # إرسال الرسائل لكل مجموعة مع تأخير
        for group in groups:
            if not running_broadcasts.get(user_id, False):
                # تم إيقاف النشر
                await client.disconnect()
                return False, "تم إيقاف النشر بواسطة المستخدم."
            
            try:
                await client.send_message(int(group['group_id']), message_text)
                # تأخير عشوائي قليل لتجنب الحظر (زيادة الأمان)
                sleep_time = delay_seconds + random.uniform(0, 5)
                await asyncio.sleep(sleep_time)
            except errors.FloodWaitError as e:
                await asyncio.sleep(e.seconds + 5)
            except Exception as e:
                print(f"خطأ في الإرسال: {e}")
                await asyncio.sleep(delay_seconds)
        
        await client.disconnect()
    
    running_broadcasts[user_id] = False
    return True, "تم الانتهاء من نشر الرسالة في جميع المجموعات."

def stop_broadcast(user_id):
    if user_id in running_broadcasts:
        running_broadcasts[user_id] = False
        return True, "تم إيقاف النشر."
    return False, "لا توجد عملية نشر نشطة."