import json
import re
from telegram import Update, ForceReply
from telegram.ext import (
    ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
)

# === Config ===
BOT_TOKEN = "8042159885:AAHkCyakSH4cug9nSCC2r4DD7-MMK8GVloM"
ADMIN_ID = 461299220

# === Load / Save Users ===
def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f, indent=2)

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
    print(f"Received message from user {update.message.from_user.id}: {update.message.text or update.message.caption}")
    message = update.message
    user = message.from_user
    chat_id = str(message.chat_id)

    # Blocked users
    if users.get(chat_id, {}).get("blocked"):
        await context.bot.send_message(chat_id=chat_id, text="🚫 You are blocked from sending messages.")
        return

    # Register/update user info
    if chat_id not in users:
        users[chat_id] = {
            "username": user.username,
            "first_name": user.first_name,
            "message_count": 1,
            "blocked": False
        }
    else:
        users[chat_id]["message_count"] = users[chat_id].get("message_count", 0) + 1
        users[chat_id]["username"] = user.username
        users[chat_id]["first_name"] = user.first_name


    save_users(users)
    recent_messages[int(chat_id)] = message.message_id

    # Send message header to admin
    header = (
        f"📩 Message from: @{user.username or 'NoUsername'}\n"
        f"👤 User ID: {chat_id}\n"
        f"📝 Messages sent: {users[chat_id]['message_count']}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=header, reply_markup=ForceReply(selective=True))
    await update.message.reply_text("✅ Message sent to the user.")
    
    # Forward message content
    if not await send_message_by_type(context.bot, ADMIN_ID, message):
        await context.bot.send_message(chat_id=ADMIN_ID, text="📎 Unsupported message type.")

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
    reply_to_id = recent_messages.get(user_id)

    try:
        result = await send_message_by_type(context.bot, user_id, update.message, reply_to_message_id=reply_to_id)
        if result:
            await update.message.reply_text("✅ Message sent to the user.")
        else:
            await update.message.reply_text("❌ Unsupported message type.")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to send message: {e}")

# === Handler: List Users ===
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = "👥 Users:\n"
    for uid, info in users.items():
        blocked = "🚫 BLOCKED" if info.get("blocked") else ""
        msg += f"{info.get('first_name', '')} ( @{info.get('username', 'N/A')} ) \n ID: {uid} \n Messages: {info.get('message_count', 0)} {blocked}\n"

    await update.message.reply_text(msg)

# === Handler: Block User ===
async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not context.args:
        await update.message.reply_text("Usage: /block <user_id>")
        return

    user_id = context.args[0]
    if user_id not in users:
        await update.message.reply_text("❌ User ID not found.")
        return

    users[user_id]["blocked"] = True
    save_users(users)
    await update.message.reply_text(f"🚫 User {user_id} has been blocked.")

# === Handler: Unblock User ===
async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not context.args:
        await update.message.reply_text("Usage: /unblock <user_id>")
        return

    user_id = context.args[0]
    if user_id not in users:
        await update.message.reply_text("❌ User ID not found.")
        return

    users[user_id]["blocked"] = False
    save_users(users)
    await update.message.reply_text(f"✅ User {user_id} has been unblocked.")

async def started(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("اعلی حضرت خوش برگشتی")
        return
    await update.message.reply_text("سلام علیکم! \nازین به بعد پیامی بدی به صورت ناشناس برای حاجیتون ارسال میشه")

# === Bot Setup ===
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Handlers
app.add_handler(MessageHandler(filters.User(ADMIN_ID) & filters.REPLY, handle_admin_reply))
app.add_handler(MessageHandler(filters.ALL & ~filters.User(ADMIN_ID), handle_user_message))
app.add_handler(CommandHandler("users", list_users))
app.add_handler(CommandHandler("block", block_user))
app.add_handler(CommandHandler("unblock", unblock_user))
app.add_handler(CommandHandler("start", started))

# Run bot
app.run_polling()
