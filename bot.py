import json
import re
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from telegram.ext import (
    ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters, CallbackQueryHandler
)
from telegram.constants import ParseMode
import requests
import jdatetime
from hijri_converter import convert
from datetime import datetime
from prices import get_all_prices_text

# === Config ===
BOT_TOKEN = "7871738259:AAFV1SdnSQ0sezHeVlUWDEKz6p-Z2Oyfbp8"
ADMIN_ID = 461299220

# === Load / Save Users ===
def load_users():
    try:
        with open("users.json", "r") as f:
            users_data = json.load(f)
            print(f"{len(users_data)} users loaded from file.")
            return users_data
    except FileNotFoundError:
        print("No users file found. Starting with empty user list.")
        return {}

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f, indent=2)
    print("✅ Users saved to file.")

users = load_users()
recent_messages = {}

# === Utility: Send Various Message Types ===
async def send_message_by_type(bot, chat_id, message, reply_to_message_id=None):
    kwargs = {"reply_to_message_id": reply_to_message_id} if reply_to_message_id else {}

    if message.text:
        return await bot.send_message(chat_id, text=message.text, **kwargs)
    elif message.photo:
        return await bot.send_photo(chat_id, photo=message.photo[-1].file_id, caption=message.caption or "", **kwargs)
    elif message.video:
        return await bot.send_video(chat_id, video=message.video.file_id, caption=message.caption or "", **kwargs)
    elif message.document:
        return await bot.send_document(chat_id, document=message.document.file_id, caption=message.caption or "", **kwargs)
    elif message.voice:
        return await bot.send_voice(chat_id, voice=message.voice.file_id, caption=message.caption or "", **kwargs)
    elif message.sticker:
        return await bot.send_sticker(chat_id, sticker=message.sticker.file_id, **kwargs)
    elif message.audio:
        return await bot.send_audio(chat_id, audio=message.audio.file_id, caption=message.caption or "", **kwargs)
    elif message.video_note:
        return await bot.send_video_note(chat_id, video_note=message.video_note.file_id, **kwargs)

    return None  # Unsupported type

# === Handler: User Message ===
async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user = message.from_user
    chat_id = str(message.chat_id)

    print(f"📨 Message received from {chat_id} (@{user.username})")

    # Blocked users
    if users.get(chat_id, {}).get("blocked"):
        await context.bot.send_message(chat_id=chat_id, text="🚫 You are blocked from sending messages.")
        print(f"🚫 Blocked user {chat_id} tried to send a message.")
        return

    # Register/update user info
    if chat_id not in users:
        users[chat_id] = {
            "username": user.username,
            "first_name": user.first_name,
            "message_count": 1,
            "blocked": False
        }
        print(f"🆕 New user registered: {chat_id} - {user.first_name} (@{user.username})")
    else:
        users[chat_id]["message_count"] = users[chat_id].get("message_count", 0) + 1
        users[chat_id]["username"] = user.username
        users[chat_id]["first_name"] = user.first_name
        print(f"📈 Message count updated for {chat_id}: {users[chat_id]['message_count']}")

    save_users(users)
    recent_messages[int(chat_id)] = message.message_id

    header = (
        f"👀 User name: {user.first_name or 'Null'} {user.last_name or ''}"
        f"📩 Message from: @{user.username or 'NoUsername'}\n"
        f"👤 User ID: {chat_id}\n"
        f"📝 Messages sent: {users[chat_id]['message_count']}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=header)

    await update.message.reply_text("✅ پیام رفت برا اقا ایلیا")

    if not await send_message_by_type(context.bot, ADMIN_ID, message):
        await context.bot.send_message(chat_id=ADMIN_ID, text="📎 Unsupported message type.")
        print("⚠️ Unsupported message type from user.")

# === Handler: Admin Menu Callback ===
async def admin_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    print(f"🛠 Admin used menu option: {query.data}")

    if query.data == "list_users":
        msg = "👥 لیست کاربران:\n"
        for uid, info in users.items():
            blocked = "🚫 BLOCKED" if info.get("blocked") else ""
            msg += f"{info.get('first_name', '')} ( @{info.get('username', 'N/A')} ) \n ID: {uid} \n Messages: {info.get('message_count', 0)} {blocked}\n"
        await query.message.reply_text(msg)

    elif query.data == "blocked_users":
        msg = "📛 لیست کاربران بلاک‌شده:\n"
        found = False
        for uid, info in users.items():
            if info.get("blocked"):
                found = True
                msg += f"{info.get('first_name', '')} ( @{info.get('username', 'N/A')} )\nID: {uid}\n\n"
        if not found:
            msg = "هیچ کاربر بلاک‌شده‌ای وجود نداره ✅"
        await query.message.reply_text(msg)
        
    elif query.data == "get_json":
        with open("users.json", "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)

        await query.message.reply_document(InputFile("users.json"), filename="users.json")

        json_str = json.dumps(users, ensure_ascii=False, indent=2)
        if len(json_str) < 4096:
            await query.message.reply_text(f"```json\n{json_str}\n```", parse_mode=ParseMode.MARKDOWN)
        else:
            await query.message.reply_text("⚠️ متن JSON بیشتر از ۴۰۹۶ کاراکتره و فقط فایل فرستاده شد.")
    
    elif query.data == "update_json":
        await query.message.reply_text(
            "To update the user data:\n"
            "1. Send a JSON file\n"
            "or\n"
            "2. Send a text formatted like the user list.\n"
            "The bot will automatically process and update the data after receiving it."
        )
        context.user_data["awaiting_user_data_update"] = True


#get weather

def get_weather_summary(city="Tehran", api_key="YOUR_API_KEY"):
    url = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?q={city}&appid={api_key}&units=metric&lang=fa"
    )
    response = requests.get(url)
    weather_data = response.json()

    if "list" not in weather_data:
        print("❌ Failed to get forecast:", weather_data)
        return None, None
    
    print("accessed weather api successfully👌")
    
    try:
        now_weather = weather_data['list'][0]
        today_temp = now_weather['main']['temp']
        today_desc = now_weather['weather'][0]['description']
        today_summary = f"{today_temp}°C | {today_desc}"

        tomorrow_weather = weather_data['list'][8]
        tomorrow_temp = tomorrow_weather['main']['temp']
        tomorrow_desc = tomorrow_weather['weather'][0]['description']
        tomorrow_summary = f"{tomorrow_temp}°C | {tomorrow_desc}"

        return today_summary, tomorrow_summary

    except (KeyError, IndexError) as e:
        print("⚠️ Parsing weather failed:", e)
        return None, None

# === Handler: Admin Reply ===
async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Please reply to a user message.")
        return

    original_text = update.message.reply_to_message.text or update.message.reply_to_message.caption or ""
    match = re.search(r"User ID:\s*(\d+)", original_text)

    if not match:
        await update.message.reply_text("❌ Could not extract user ID.")
        return

    user_id = int(match.group(1))
    print(f"✉️ Admin is replying to user {user_id}")
    reply_to_id = recent_messages.get(user_id)

    try:
        result = await send_message_by_type(context.bot, user_id, update.message, reply_to_message_id=reply_to_id)
        if result:
            await update.message.reply_text("✅ Message sent to the user.")
        else:
            await update.message.reply_text("❌ Unsupported message type.")
    except Exception as e:
        print(f"❌ Error sending message to user {user_id}: {e}")
        await update.message.reply_text(f"❌ Failed to send message: {e}")

# === Handler: Block User ===
async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("کصخل میخوای سازنده باتو بلاک کنی؟🤣")
        return

    if context.args:
        user_id = context.args[0]
    else:
        original_text = update.message.reply_to_message.text or update.message.reply_to_message.caption or ""
        match = re.search(r"User ID:\s*(\d+)", original_text)
        if not match:
            await update.message.reply_text("❌ Could not extract user ID.")
            return
        user_id = match.group(1)

    if user_id not in users:
        await update.message.reply_text("❌ User ID not found.")
        return

    print(f"⛔️ Admin requested to block user {user_id}")
    if users[user_id]["blocked"]:
        await update.message.reply_text("اینکه بلاک بود کصکش")
        return

    users[user_id]["blocked"] = True
    save_users(users)
    await update.message.reply_text(f"🚫 User {user_id} has been blocked.")

# === Handler: Unblock User ===
async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("کصخل میخوای سازنده باتو بلاک کنی؟🤣")
        return

    if context.args:
        user_id = context.args[0]
    else:
        original_text = update.message.reply_to_message.text or update.message.reply_to_message.caption or ""
        match = re.search(r"User ID:\s*(\d+)", original_text)
        if not match:
            await update.message.reply_text("❌ Could not extract user ID.")
            return
        user_id = match.group(1)

    if user_id not in users:
        await update.message.reply_text("❌ User ID not found.")
        return

    print(f"🔓 Admin requested to unblock user {user_id}")
    if not users[user_id]["blocked"]:
        await update.message.reply_text("اینکه بلاک نبود کصکش")
        return

    users[user_id]["blocked"] = False
    save_users(users)
    await update.message.reply_text(f"✅ User {user_id} has been unblocked.")
    
# === Handler: Start ===
async def started(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user = message.from_user
    chat_id = str(message.chat_id)

    print(f"🚀 /start from {chat_id} (@{user.username})")

    # ==== Non-admin users ====
    if update.effective_user.id != ADMIN_ID:
        if chat_id not in users:
            users[chat_id] = {
                "username": user.username,
                "first_name": user.first_name,
                "message_count": 1,
                "blocked": False
            }

            save_users(users)
            print(f"🆕 Registered new user from /start: {chat_id}")
            await message.reply_text(
                "سلام علیکم ✨\n"
                "از این به بعد پیامی بدی، به صورت ناشناس برای حاجیتون ارسال میشه 👀"
            )
        else:
            await message.reply_text("کصخل قبلاً باتو استارت کردی ")
        return

    # ==== Admin Panel ====
    print("🛠 Admin accessed the bot.")

    # Keyboard buttons
    keyboard = [
        [InlineKeyboardButton("👥 لیست کاربران", callback_data="list_users")],
        [InlineKeyboardButton("🚫 لیست بلاک‌شده‌ها", callback_data="blocked_users")],
        [InlineKeyboardButton("📥 دریافت فایل JSON", callback_data="get_json")],
        [InlineKeyboardButton("💾 آپدیت فایل JSON", callback_data="update_json")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Dates
    now = datetime.now()
    jalali = jdatetime.datetime.now().strftime("%Y/%m/%d")
    hijri = convert.Gregorian(now.year, now.month, now.day).to_hijri()
    hijri_str = f"{hijri.year}/{hijri.month:02}/{hijri.day:02}"

    # Weather
    WEATHER_API_KEY = "bb77d86a66d5363f985cbf48fe5959ef"
    today_weather_str, tomorrow_weather_str = get_weather_summary(
    city="Tehran", api_key="bb77d86a66d5363f985cbf48fe5959ef"
    )


    # Admin Panel Message
    try:
        prices_text = get_all_prices_text()
    except Exception as e:
        prices_text = "❌ دریافت قیمت‌ها ممکن نبود.\n"

    text = (
        "<b>TIROK ADMIN PANEL</b> ✨\n\n"
        "<b>تاریخ‌ها:</b>\n"
        f"🇺🇸 میلادی: {now.strftime('%Y/%m/%d')}\n"
        f"🇮🇷 شمسی: {jalali}\n\n"
        "<b>آب‌وهوا - تهران:</b>\n"
        f"🌤 امروز: {today_weather_str}\n"
        f"🌥 فردا: {tomorrow_weather_str}\n\n"
        f"{prices_text}"
    )

    await message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")

async def update_users_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_user_data_update"):
        return

    if update.message.document:
        file = await update.message.document.get_file()
        file_path = "users.json"
        await file.download_to_drive(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                new_data = json.load(f)
            users.update(new_data)
            save_users(users)
            await update.message.reply_text("✅ successful")
        except Exception as e:
            await update.message.reply_text(f"❌ Error while loading JSON:\n{e}")
            
    elif update.message.text:
        try:
            text = update.message.text.strip()
            lines = text.split("\n")
            new_users = {}
            current = {}

            for i in range(len(lines)):
                line = lines[i].strip()
                if line.startswith("👥") or line == "":
                    continue
                if "( @" in line:
                    name = line.split(" (")[0].strip()
                    username = line.split("@")[1].split(")")[0].strip()
                    current["first_name"] = name
                    current["username"] = None if username == "N/A" else username
                elif line.startswith("ID:"):
                    current["id"] = int(line.replace("ID:", "").strip())
                elif line.startswith("Messages:"):
                    parts = line.replace("Messages:", "").strip().split()
                    current["message_count"] = int(parts[0])
                    current["blocked"] = "BLOCKED" in line
                    new_users[current["id"]] = current
                    current = {}

            users = new_users
            save_users(users)
            await update.message.reply_text("✅ Users updated successfully from formatted text.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error parsing text:\n{e}")
    print("Users json file was changed")
    context.user_data["awaiting_user_data_update"] = False

# === Bot Setup ====
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Handlers
app.add_handler(CallbackQueryHandler(admin_menu_handler))
app.add_handler(CommandHandler("start", started))
app.add_handler(CommandHandler("block", block_user))
app.add_handler(CommandHandler("unblock", unblock_user))
app.add_handler(MessageHandler(filters.User(ADMIN_ID) & filters.REPLY, handle_admin_reply))
app.add_handler(MessageHandler(filters.ALL & ~filters.User(ADMIN_ID), handle_user_message))
app.add_handler(MessageHandler(
    filters.User(ADMIN_ID) & (filters.TEXT | filters.Document.ALL),
    update_users_data_handler
))

# Run bot
print("🤖 Bot is starting...")
app.run_polling()
