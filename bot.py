#!/usr/bin/env python3
"""
DXA Number Bot - Telegram OTP & Number Management Bot
"""

import re
import asyncio
import random
import json
import os
import logging
from datetime import datetime
from telethon import TelegramClient, events, Button
from telethon.errors import SessionPasswordNeededError

# --- লগিং কনফিগারেশন ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- কনফিগারেশন (Environment Variables থেকে নিন) ---
API_ID = int(os.environ.get('API_ID', 30911495))
API_HASH = os.environ.get('API_HASH', 'f19231d13578b1742f80a1a1d54fada0')
PHONE = os.environ.get('PHONE', '+60122079529')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 8197284774))
FORWARD_BOT_TOKEN = os.environ.get('FORWARD_BOT_TOKEN', '8594100418:AAHXI6Br7_7Z_C5ORxvYRh0rVpXuBkD3QHM')
NUMBER_BOT_TOKEN = os.environ.get('NUMBER_BOT_TOKEN', '8332473503:AAEjdM9IEXMuuwGfOGUgBp5zpP54EoiIsVg')

SOURCE_GROUP = int(os.environ.get('SOURCE_GROUP', -1002601589640))
TARGET_GROUP = int(os.environ.get('TARGET_GROUP', -1003578388211))

# --- ফাইল পাথ ---
DB_FILE = 'data/numbers_db.json'
USERS_FILE = 'data/users.txt'
SESSION_DIR = 'sessions'

# --- ডিরেক্টরি তৈরি ---
os.makedirs('data', exist_ok=True)
os.makedirs(SESSION_DIR, exist_ok=True)

# --- ক্লায়েন্ট ইনিশিয়ালাইজেশন ---
user_client = TelegramClient(f'{SESSION_DIR}/user', API_ID, API_HASH)
bot_client = TelegramClient(f'{SESSION_DIR}/forward_bot', API_ID, API_HASH)
new_bot_client = TelegramClient(f'{SESSION_DIR}/number_bot', API_ID, API_HASH)

# ========== ডাটাবেস ফাংশন ==========
def load_db():
    """JSON ডাটাবেস লোড করে"""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"DB load error: {e}")
            return {}
    return {}

def save_db(data):
    """JSON ডাটাবেস সেভ করে"""
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"DB save error: {e}")

def log_user(user_id):
    """ইউজার আইডি লগ করে"""
    try:
        users = set()
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                users = set(f.read().splitlines())
        if str(user_id) not in users:
            with open(USERS_FILE, 'a') as f:
                f.write(f"{user_id}\n")
    except Exception as e:
        logger.error(f"User log error: {e}")

# ========== OTP এক্সট্রাকশন ==========
def extract_otp(text):
    """সকল প্রকার OTP ফরম্যাট এক্সট্রাক্ট করে"""
    if not text:
        return None
    
    patterns = [
        # OTP: 123456
        r'(?:OTP|otp|Code|code|PIN|pin|Verification|verification)[:\s]*([0-9\-\s]{4,8})',
        
        # Your code is 123456
        r'(?:code|is|are)[:\s]*([0-9]{4,8})',
        
        # 123456 (শুধু সংখ্যা)
        r'\b([0-9]{4,8})\b',
        
        # 123-456 or 123 456
        r'([0-9]{3}[-,\s][0-9]{3})',
        
        # G-123456
        r'[Gg]-?([0-9]{4,8})',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]
            # সব ড্যাশ ও স্পেস রিমুভ
            otp = re.sub(r'[\-\s]', '', str(match))
            if otp.isdigit() and 4 <= len(otp) <= 8:
                logger.info(f"OTP found: {otp} (from: {match})")
                return otp
    return None

# ========== সিস্টেম ১: মেসেজ ফরওয়ার্ডার ==========
@user_client.on(events.NewMessage(chats=SOURCE_GROUP))
async def forwarder_handler(event):
    """সোর্স গ্রুপ থেকে OTP ফরওয়ার্ড করে"""
    msg_text = event.raw_text
    if not msg_text:
        return
    
    # OTP খুঁজি
    otp = extract_otp(msg_text)
    
    if otp:
        logger.info(f"OTP detected: {otp}")
        
        # বিভিন্ন ফিল্ড এক্সট্রাক্ট করি
        time_match = re.search(r"Time:?\s*(.+)", msg_text, re.IGNORECASE)
        number_match = re.search(r"Number:?\s*(.+)", msg_text, re.IGNORECASE)
        country_match = re.search(r"Country:?\s*(.+)", msg_text, re.IGNORECASE)
        service_match = re.search(r"Service:?\s*(.+)", msg_text, re.IGNORECASE)

        # টাইম
        time = time_match.group(1).strip() if time_match else datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        
        # নাম্বার ফরম্যাটিং
        raw_num = number_match.group(1) if number_match else ""
        clean_num = ''.join(filter(str.isdigit, raw_num))
        
        if len(clean_num) > 7:
            formatted_num = f"{clean_num[:7]} DXA {clean_num[-3:]}"
        elif clean_num:
            formatted_num = clean_num
        else:
            formatted_num = "N/A"
        
        # কান্ট্রি ও সার্ভিস
        country = country_match.group(1).strip() if country_match else "Unknown"
        service = service_match.group(1).strip().upper() if service_match else "TELEGRAM"

        # ফরম্যাটেড মেসেজ
        formatted_message = (
            f"🔥 <b>{service} OTP RECEIVED</b> ✨\n\n"
            f"┌ <b>⏰ Time:</b> <code>{time}</code>\n"
            f"├ <b>🌍 Country:</b> <code>{country}</code>\n"
            f"├ <b>⚙️ Service:</b> <code>{service}</code>\n"
            f"├ <b>☎️ Number:</b> <code>{formatted_num}</code>\n"
            f"└ <b>🔑 OTP:</b> <code>{otp}</code>\n\n"
            f"<i>Powered by @developer_x_asik</i>"
        )
        
        # বাটন
        buttons = [
            [Button.url("📢 Main Channel", "https://t.me/developer_x_asik")],
            [Button.url("👥 Support Group", "https://t.me/developer_x_asik_number")],
        ]
        
        try:
            await bot_client.send_message(
                TARGET_GROUP, 
                formatted_message, 
                buttons=buttons, 
                parse_mode='html'
            )
            logger.info(f"✅ Forwarded: {otp} | {formatted_num}")
        except Exception as e:
            logger.error(f"❌ Forward error: {e}")

# ========== সিস্টেম ২: নাম্বার বট ==========
@new_bot_client.on(events.NewMessage(pattern='/start|🔙 Back'))
async def start_handler(event):
    """স্টার্ট মেসেজ হ্যান্ডলার"""
    user = await event.get_sender()
    log_user(user.id)
    
    # কিবোর্ড তৈরি
    keyboard = [
        [Button.text("📱 Get Number", resize=True)],
        [Button.text("ℹ️ About", resize=True)]
    ]
    
    # অ্যাডমিন হলে অতিরিক্ত বাটন
    if user.id == ADMIN_ID:
        keyboard.append([Button.text("🛠 Admin Panel", resize=True)])
    
    welcome_msg = (
        f"👋 **Welcome {user.first_name}!**\n\n"
        f"📱 **DXA Number Bot**\n"
        f"আপনি এখানে ফ্রি ভার্চুয়াল নাম্বার পেতে পারেন।\n\n"
        f"**কমান্ড:**\n"
        f"• 📱 Get Number - নতুন নাম্বার নিন\n"
        f"• ℹ️ About - আমাদের সম্পর্কে জানুন\n\n"
        f"**চ্যানেল:** @developer_x_asik"
    )
    
    await event.respond(welcome_msg, buttons=keyboard)

@new_bot_client.on(events.NewMessage(pattern='ℹ️ About'))
async def about_handler(event):
    """About সেকশন"""
    msg = (
        "ℹ️ **DXA Number Bot**\n\n"
        "**Version:** 1.0.0\n"
        "**Developer:** @developer_x_asik\n"
        "**Language:** Python 3\n"
        "**Library:** Telethon\n\n"
        "**Features:**\n"
        "• OTP নাম্বার জেনারেশন\n"
        "• ইউজার ট্র্যাকিং\n"
        "• অ্যাডমিন প্যানেল\n"
        "• ব্রডকাস্ট সিস্টেম\n\n"
        "**চ্যানেল:** @developer_x_asik\n"
        "**গ্রুপ:** @developer_x_asik_number"
    )
    await event.respond(msg)

@new_bot_client.on(events.NewMessage(pattern='📱 Get Number'))
async def get_number_handler(event):
    """নাম্বার নেওয়ার হ্যান্ডলার"""
    db = load_db()
    if not db:
        return await event.respond("❌ কোনো সার্ভিস উপলব্ধ নেই।")
    
    buttons = []
    for service in db.keys():
        buttons.append([Button.inline(service, f"srv_{service}".encode())])
    
    await event.respond("📱 **সার্ভিস সিলেক্ট করুন:**", buttons=buttons)

@new_bot_client.on(events.NewMessage(pattern='🛠 Admin Panel'))
async def admin_panel_handler(event):
    """অ্যাডমিন প্যানেল"""
    if event.sender_id != ADMIN_ID:
        return
    
    db = load_db()
    
    # ইউজার কাউন্ট
    users_count = 0
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            users_count = len(f.read().splitlines())
    
    # নাম্বার কাউন্ট
    total_nums = 0
    for s in db.values():
        for nums in s.values():
            total_nums += len(nums)
    
    # স্ট্যাটাস
    status = (
        f"🛠 **Admin Control Panel**\n\n"
        f"👥 **Total Users:** `{users_count}`\n"
        f"🔢 **Total Numbers:** `{total_nums}`\n"
        f"📊 **Services:** `{len(db)}`\n"
        f"⏱ **Uptime:** Active\n\n"
        f"**System Info:**\n"
        f"• Python: 3.9+\n"
        f"• Telethon: 1.34+\n"
        f"• Database: JSON"
    )
    
    buttons = [
        [Button.inline("📊 Stock Status", b"adm_status")],
        [Button.inline("📢 Broadcast", b"adm_bc_start")],
        [Button.inline("⚙️ Manage Stock", b"adm_manage")],
        [Button.inline("➕ Add Numbers", b"adm_add")],
        [Button.inline("📈 Statistics", b"adm_stats")]
    ]
    
    await event.respond(status, buttons=buttons)

# ========== কলব্যাক হ্যান্ডলার ==========
@new_bot_client.on(events.CallbackQuery)
async def callback_handler(event):
    """বাটন কলব্যাক হ্যান্ডলার"""
    data = event.data
    user_id = event.sender_id
    db = load_db()
    
    # --- ইউজার কলব্যাক ---
    if data.startswith(b"srv_"):
        service = data.decode().split("_")[1]
        if service not in db:
            return await event.answer("Service not found!")
        
        countries = []
        for country in db[service].keys():
            count = len(db[service][country])
            countries.append([Button.inline(
                f"{country} ({count})", 
                f"cnt_{service}_{country}".encode()
            )])
        
        countries.append([Button.inline("🔙 Back", b"back_services")])
        await event.edit(f"📍 **{service} - Select Country:**", buttons=countries)
    
    elif data.startswith(b"cnt_"):
        parts = data.decode().split("_", 2)
        if len(parts) < 3:
            return
        
        service, country = parts[1], parts[2]
        
        if service not in db or country not in db[service]:
            return await event.answer("Stock empty!")
        
        available = db[service][country]
        if len(available) < 1:
            return await event.answer("No numbers available!")
        
        # ৩টি নাম্বার দিন
        take = min(3, len(available))
        selected = random.sample(available, take)
        
        # নাম্বার রিমুভ
        for n in selected:
            if n in db[service][country]:
                db[service][country].remove(n)
        
        # খালি কান্ট্রি ডিলিট
        if not db[service][country]:
            del db[service][country]
        if not db[service]:
            del db[service]
        
        save_db(db)
        
        # রেসপন্স
        numbers_text = "\n".join([f"📱 `+{n}`" for n in selected])
        msg = (
            f"✅ **Your Numbers:**\n\n"
            f"{numbers_text}\n\n"
            f"**Service:** {service}\n"
            f"**Country:** {country}\n\n"
            f"💡 OTP পেতে নাম্বার কপি করুন"
        )
        
        buttons = [
            [Button.inline("🔄 New Numbers", f"cnt_{service}_{country}".encode())],
            [Button.inline("🔙 Services", b"back_services")]
        ]
        
        await event.edit(msg, buttons=buttons)
    
    elif data == b"back_services":
        # সার্ভিস লিস্ট দেখান
        buttons = []
        for service in db.keys():
            buttons.append([Button.inline(service, f"srv_{service}".encode())])
        await event.edit("📱 **Select Service:**", buttons=buttons)
    
    # --- অ্যাডমিন কলব্যাক ---
    elif user_id == ADMIN_ID:
        if data == b"adm_status":
            status = "📊 **Stock Status**\n\n"
            for s, cnts in db.items():
                status += f"**{s}**\n"
                for c, nums in cnts.items():
                    status += f"  • {c}: {len(nums)}\n"
            await event.edit(status, buttons=[[Button.inline("🔙 Back", b"adm_back")]])
        
        elif data == b"adm_manage":
            buttons = []
            for s in db.keys():
                total = sum(len(n) for n in db[s].values())
                buttons.append([Button.inline(f"⚙️ {s} ({total})", f"mng_{s}".encode())])
            buttons.append([Button.inline("🔙 Back", b"adm_back")])
            await event.edit("**Manage Services:**", buttons=buttons)
        
        elif data.startswith(b"mng_"):
            service = data.decode().split("_")[1]
            if service not in db:
                return
            
            buttons = []
            for c, nums in db[service].items():
                buttons.append([Button.inline(
                    f"❌ {c} ({len(nums)})", 
                    f"del_{service}_{c}".encode()
                )])
            buttons.append([Button.inline("🔙 Back", b"adm_manage")])
            await event.edit(f"**{service} - Select to delete:**", buttons=buttons)
        
        elif data.startswith(b"del_"):
            parts = data.decode().split("_", 2)
            if len(parts) < 3:
                return
            service, country = parts[1], parts[2]
            
            if service in db and country in db[service]:
                del db[service][country]
                if not db[service]:
                    del db[service]
                save_db(db)
                await event.answer(f"✅ {country} deleted!")
            
            await admin_panel_handler(event)
        
        elif data == b"adm_add":
            await event.edit(
                "📤 **Add Numbers**\n\n"
                "Send a `.txt` file with numbers (one per line).\n"
                "Example:\n"
                "```\n"
                "1234567890\n"
                "0987654321\n"
                "```",
                buttons=[[Button.inline("🔙 Back", b"adm_back")]]
            )
        
        elif data == b"adm_stats":
            import psutil
            import platform
            
            info = (
                f"📈 **System Statistics**\n\n"
                f"**System:** {platform.system()}\n"
                f"**Python:** {platform.python_version()}\n"
                f"**CPU:** {psutil.cpu_percent()}%\n"
                f"**RAM:** {psutil.virtual_memory().percent}%\n"
                f"**Uptime:** Active"
            )
            await event.edit(info, buttons=[[Button.inline("🔙 Back", b"adm_back")]])
        
        elif data == b"adm_bc_start":
            async with new_bot_client.conversation(user_id) as conv:
                await conv.send_message("📢 Send broadcast message:")
                response = await conv.get_response()
                
                if os.path.exists(USERS_FILE):
                    with open(USERS_FILE, 'r') as f:
                        users = f.read().splitlines()
                    
                    success = 0
                    for uid in users:
                        try:
                            await new_bot_client.send_message(int(uid), response.text)
                            success += 1
                            await asyncio.sleep(0.05)
                        except:
                            pass
                    
                    await conv.send_message(f"✅ Broadcast sent to {success} users!")
        
        elif data == b"adm_back":
            await admin_panel_handler(event)

# ========== ফাইল আপলোড হ্যান্ডলার ==========
@new_bot_client.on(events.NewMessage(from_users=ADMIN_ID))
async def file_handler(event):
    """অ্যাডমিনের ফাইল আপলোড হ্যান্ডলার"""
    if event.document and event.document.mime_type == 'text/plain':
        async with new_bot_client.conversation(ADMIN_ID) as conv:
            await conv.send_message("📌 Service name (e.g., TELEGRAM):")
            srv = (await conv.get_response()).text.strip().upper()
            
            await conv.send_message("📌 Country name (e.g., USA):")
            cnt = (await conv.get_response()).text.strip().upper()
            
            # ফাইল ডাউনলোড
            path = await event.download_media()
            
            try:
                with open(path, 'r') as f:
                    numbers = [n.strip() for n in f.readlines() if n.strip()]
                
                # ভ্যালিডেশন
                valid_nums = []
                for num in numbers:
                    clean = ''.join(filter(str.isdigit, num))
                    if clean and len(clean) >= 8:
                        valid_nums.append(clean)
                
                if not valid_nums:
                    await conv.send_message("❌ No valid numbers!")
                    return
                
                # ডাটাবেসে যোগ
                db = load_db()
                if srv not in db:
                    db[srv] = {}
                if cnt not in db[srv]:
                    db[srv][cnt] = []
                
                db[srv][cnt].extend(valid_nums)
                save_db(db)
                
                await conv.send_message(
                    f"✅ **Added {len(valid_nums)} numbers**\n"
                    f"• Service: {srv}\n"
                    f"• Country: {cnt}"
                )
            except Exception as e:
                await conv.send_message(f"❌ Error: {str(e)}")
            finally:
                if os.path.exists(path):
                    os.remove(path)

# ========== মেইন ফাংশন ==========
async def main():
    """মেইন ফাংশন"""
    logger.info("Starting DXA Number Bot...")
    
    try:
        # ইউজার ক্লায়েন্ট স্টার্ট
        await user_client.start(phone=PHONE)
        logger.info("✅ User client started")
        
        # বট ক্লায়েন্ট স্টার্ট
        await bot_client.start(bot_token=FORWARD_BOT_TOKEN)
        logger.info("✅ Forward bot started")
        
        await new_bot_client.start(bot_token=NUMBER_BOT_TOKEN)
        logger.info("✅ Number bot started")
        
        logger.info("🚀 All systems online!")
        logger.info(f"Admin ID: {ADMIN_ID}")
        logger.info(f"Source Group: {SOURCE_GROUP}")
        logger.info(f"Target Group: {TARGET_GROUP}")
        
        # একসাথে চালানো
        await asyncio.gather(
            user_client.run_until_disconnected(),
            bot_client.run_until_disconnected(),
            new_bot_client.run_until_disconnected()
        )
    except SessionPasswordNeededError:
        logger.error("2FA enabled! Please enter password")
        await user_client.sign_in(password=input("Password: "))
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        logger.info("Shutting down...")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
