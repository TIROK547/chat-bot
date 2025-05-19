import json
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
import re

BOT_TOKEN = "8042159885:AAHkCyakSH4cug9nSCC2r4DD7-MMK8GVloM"
ADMIN_ID = 461299220 

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

async def send_message_by_type(bot, chat_id, message, reply_to_message_id=None):
    kwargs = {}
    if reply_to_message_id:
        kwargs["reply_to_message_id"] = reply_to_message_id

    if message.text:
        await bot.send_message(chat_id=chat_id, text=message.text, **kwargs)

    elif message.photo:
        await bot.send_photo(chat_id=chat_id, photo=message.photo[-1].file_id, caption=message.caption or "", **kwargs)

    elif message.video:
        await bot.send_video(chat_id=chat_id, video=message.video.file_id, caption=message.caption or "", **kwargs)

    elif message.document:
        await bot.send_document(chat_id=chat_id, document=message.document.file_id, caption=message.caption or "", **kwargs)

    elif message.voice:
        await bot.send_voice(chat_id=chat_id, voice=message.voice.file_id, caption=message.caption or "", **kwargs)

    elif message.sticker:
        await bot.send_sticker(chat_id=chat_id, sticker=message.sticker.file_id, **kwargs)

    elif message.audio:
        await bot.send_audio(chat_id=chat_id, audio=message.audio.file_id, caption=message.caption or "", **kwargs)

    elif message.video_note:
        await bot.send_video_note(chat_id=chat_id, video_note=message.video_note.file_id, **kwargs)

    else:
        return False

    return True


async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    chat_id = str(update.message.chat_id)
    message = update.message

    # If user is blocked, ignore or notify politely
    if users.get(chat_id, {}).get("blocked", False):
        # Optional: send a polite notice to blocked user
        await context.bot.send_message(chat_id=chat_id, text="🚫 You are blocked from sending messages.")
        return

    # Update or create user info with message count
    if chat_id in users:
        users[chat_id]["message_count"] = users[chat_id].get("message_count", 0) + 1
        # Update username and first_name in case they changed
        users[chat_id]["username"] = user.username
        users[chat_id]["first_name"] = user.first_name
    else:
        users[chat_id] = {
            "username": user.username,
            "first_name": user.first_name,
            "message_count": 1,
            "blocked": False
        }

    save_users(users)

    # Save last message ID
    recent_messages[int(chat_id)] = message.message_id

    header = (
        f"📩 Message from: @{user.username or 'NoUsername'}\n"
        f"👤 User ID: {chat_id}\n"
        f"📝 Messages sent: {users[chat_id]['message_count']}"
    )

    await context.bot.send_message(chat_id=ADMIN_ID, text=header, reply_markup=ForceReply(selective=True))

    success = await send_message_by_type(context.bot, ADMIN_ID, message)
    if not success:
        await context.bot.send_message(chat_id=ADMIN_ID, text="📎 Received an unsupported message type.", reply_markup=ForceReply(selective=True))


async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return

    original = update.message.reply_to_message.text or update.message.reply_to_message.caption or ""
    match = re.search(r"User ID:\s*(\d+)", original)
    if not match:
        await update.message.reply_text("❌ Could not extract user ID.")
        return
    
    user_id = int(match.group(1))
    reply_to_id = recent_messages.get(user_id)

    reply = update.message

    try:
        success = await send_message_by_type(context.bot, user_id, reply, reply_to_message_id=reply_to_id)
        if success:
            await update.message.reply_text("✅ Message sent to the user.")
        else:
            await update.message.reply_text("❌ Unsupported message type.")
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to send message: {e}")


async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    message = "👥 Users:\n"
    for uid, info in users.items():
        count = info.get("message_count", 0)
        blocked = "🚫 BLOCKED" if info.get("blocked", False) else ""
        message += f"{info.get('first_name', '')} (@{info.get('username', 'N/A')}) - ID: {uid} - Messages sent: {count} {blocked}\n"
    await update.message.reply_text(message)


async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /block <user_id>")
        return

    user_id = context.args[0]

    if user_id not in users:
        await update.message.reply_text("User ID not found.")
        return

    users[user_id]["blocked"] = True
    save_users(users)

    await update.message.reply_text(f"User {user_id} has been blocked.")


async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /unblock <user_id>")
        return

    user_id = context.args[0]

    if user_id not in users:
        await update.message.reply_text("User ID not found.")
        return

    users[user_id]["blocked"] = False
    save_users(users)

    await update.message.reply_text(f"User {user_id} has been unblocked.")


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & filters.REPLY & filters.User(ADMIN_ID), handle_admin_reply))
app.add_handler(MessageHandler(~filters.COMMAND, handle_user_message))
app.add_handler(CommandHandler("users", list_users))
app.add_handler(CommandHandler("block", block_user))
app.add_handler(CommandHandler("unblock", unblock_user))

app.run_polling()
