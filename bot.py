import json
import re
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters, CallbackQueryHandler
)

# === Config ===
BOT_TOKEN = "8042159885:AAHkCyakSH4cug9nSCC2r4DD7-MMK8GVloM"
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
        f"📩 Message from: @{user.username or 'NoUsername'}\n"
        f"👤 User ID: {chat_id}\n"
        f"📝 Messages sent: {users[chat_id]['message_count']}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=header)

    if chat_id == "6283893454":
        await update.message.reply_text("حیف فامیلی")
    elif chat_id == "1873909525":
        await update.message.reply_text("عرشیا کص ننت " * 100)

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

    if update.effective_user.id != ADMIN_ID and chat_id not in users:
        users[chat_id] = {
            "username": user.username,
            "first_name": user.first_name,
            "message_count": 1,
            "blocked": False
        }
        save_users(users)
        print(f"🆕 Registered new user from /start: {chat_id}")
        await update.message.reply_text("سلام علیکم✨ \nازین به بعد پیامی بدی به صورت ناشناس برای حاجیتون ارسال میشه👀")
        return
    elif update.effective_user.id != ADMIN_ID and chat_id in users:
        await update.message.reply_text("کصخل قبلا باتو استارت کردی")
        return

    print("🛠 Admin accessed the bot.")
    keyboard = [
        [InlineKeyboardButton("👥 لیست کاربران", callback_data="list_users")],
        [InlineKeyboardButton("📛 لیست بلاک‌شده‌ها", callback_data="blocked_users")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("اعلی حضرت خوش برگشتی", reply_markup=reply_markup)

# === Bot Setup ====
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Handlers
app.add_handler(CallbackQueryHandler(admin_menu_handler))
app.add_handler(CommandHandler("start", started))
app.add_handler(MessageHandler(filters.User(ADMIN_ID) & filters.REPLY, handle_admin_reply))
app.add_handler(MessageHandler(filters.ALL & ~filters.User(ADMIN_ID), handle_user_message))
app.add_handler(CommandHandler("block", block_user))
app.add_handler(CommandHandler("unblock", unblock_user))

# Run bot
print("🤖 Bot is starting...")
app.run_polling()
