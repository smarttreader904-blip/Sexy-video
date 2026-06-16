import os
import uuid
import sqlite3
from yt_dlp import YoutubeDL
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN"

MAX_DURATION = 180

# ---------------- DATABASE ----------------
conn = sqlite3.connect("videos.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT,
    title TEXT
)
""")
conn.commit()


# ---------------- MENU ----------------
menu = ReplyKeyboardMarkup(
    [["📥 Send Link", "📁 Saved Videos"]],
    resize_keyboard=True
)


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to Video Bot!\nSend YouTube Shorts link.",
        reply_markup=menu
    )


# ---------------- GET VIDEO INFO ----------------
def get_info(url):
    with YoutubeDL({"quiet": True}) as ydl:
        return ydl.extract_info(url, download=False)


# ---------------- HANDLE LINK ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📁 Saved Videos":
        await show_saved(update, context)
        return

    if "youtube.com" not in text and "youtu.be" not in text:
        return

    msg = await update.message.reply_text("Checking...")

    try:
        info = get_info(text)
        duration = info.get("duration", 0)

        if duration > MAX_DURATION:
            await msg.edit_text("❌ Only Shorts / videos under 3 min allowed.")
            return

        file_name = f"{uuid.uuid4()}.mp4"

        ydl_opts = {
            "format": "mp4/best",
            "outtmpl": file_name,
            "quiet": True
        }

        await msg.edit_text("⬇️ Downloading...")

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([text])

        await msg.edit_text("📤 Uploading...")

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💾 Save Video", callback_data=file_name)]
        ])

        with open(file_name, "rb") as video:
            sent = await update.message.reply_video(
                video=video,
                caption="Your video is ready",
                reply_markup=keyboard
            )

        # store temp mapping
        context.bot_data[file_name] = {
            "file_id": sent.video.file_id,
            "title": info.get("title", "No Title")
        }

        await msg.delete()

        os.remove(file_name)

    except Exception as e:
        await msg.edit_text(f"Error: {str(e)}")


# ---------------- SAVE VIDEO ----------------
async def save_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    key = query.data

    data = context.bot_data.get(key)

    if not data:
        await query.edit_message_text("❌ Video expired.")
        return

    cursor.execute(
        "INSERT INTO videos (file_id, title) VALUES (?, ?)",
        (data["file_id"], data["title"])
    )
    conn.commit()

    await query.edit_message_caption(
        caption="💾 Saved successfully!"
    )


# ---------------- SHOW SAVED ----------------
async def show_saved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT file_id, title FROM videos ORDER BY id DESC")
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("No saved videos found.")
        return

    for file_id, title in rows:
        await update.message.reply_video(
            video=file_id,
            caption=f"📌 {title}"
        )


# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(save_video))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
