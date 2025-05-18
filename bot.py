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
        json.dump(users, f)

users = load_users()

recent_messages = {}
async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    chat_id = update.message.chat_id
    message = update.message

    # Save user info
    users[str(chat_id)] = {
        "username": user.username,
        "first_name": user.first_name,
    }
    save_users(users)

    # Save last message ID
    recent_messages[chat_id] = message.message_id

    # Header message with user info
    header = f"📩 Message from: @{user.username or 'NoUsername'}\n👤 User ID: {chat_id}"

    await context.bot.send_message(chat_id=ADMIN_ID, text=header, reply_markup=ForceReply(selective=True))

    # Forward the actual content
    if message.text:
        await context.bot.send_message(chat_id=ADMIN_ID, text=message.text, reply_markup=ForceReply(selective=True))
    elif message.photo:
        await context.bot.send_photo(chat_id=ADMIN_ID, photo=message.photo[-1].file_id, caption=message.caption or "", reply_markup=ForceReply(selective=True))
    elif message.voice:
        await context.bot.send_voice(chat_id=ADMIN_ID, voice=message.voice.file_id, caption=message.caption or "", reply_markup=ForceReply(selective=True))
    elif message.document:
        await context.bot.send_document(chat_id=ADMIN_ID, document=message.document.file_id, caption=message.caption or "", reply_markup=ForceReply(selective=True))
    elif message.video:
        await context.bot.send_video(chat_id=ADMIN_ID, video=message.video.file_id, caption=message.caption or "", reply_markup=ForceReply(selective=True))
    else:
        await context.bot.send_message(chat_id=ADMIN_ID, text="📎 Received an unsupported message type.", reply_markup=ForceReply(selective=True))

            
async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return

    original = update.message.reply_to_message.text
    match = re.search(r"User ID:\s*(\d+)", original)
    if match:
        user_id = int(match.group(1))
        reply_to_id = recent_messages.get(user_id)
        if reply_to_id:
            await context.bot.send_message(
                chat_id=user_id,
                text=update.message.text,
                reply_to_message_id=reply_to_id
            )
        else:
            await context.bot.send_message(chat_id=user_id, text=update.message.text)

        await update.message.reply_text("✅ Message sent to the user.")
    else:
        await update.message.reply_text("❌ Could not extract user ID.")

# Command to list users
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    message = "👥 Users:\n"
    for uid, info in users.items():
        message += f"{info.get('first_name', '')} (@{info.get('username', 'N/A')}) - ID: {uid}\n"
    await update.message.reply_text(message)

# Start the bot
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.TEXT & filters.REPLY & filters.User(ADMIN_ID), handle_admin_reply))
app.add_handler(MessageHandler(~filters.COMMAND, handle_user_message))
app.add_handler(CommandHandler("users", list_users))

app.run_polling()
