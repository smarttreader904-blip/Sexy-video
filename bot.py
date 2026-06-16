import os
import uuid
import sqlite3
from yt_dlp import YoutubeDL
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = "8859975301:AAEqR6ut9U_Vh77slUhAj5RdbwQmt2OoTXk"

MAX_DURATION = 180  # optional limit (3 min)

# ---------------- DATABASE ----------------
conn = sqlite3.connect("tiktok_videos.db", check_same_thread=False)
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
    [["📥 Send TikTok Link", "📁 Saved Videos"]],
    resize_keyboard=True
)


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 TikTok Video Bot Ready!\nSend TikTok link.",
        reply_markup=menu
    )


# ---------------- GET INFO ----------------
def get_info(url):
    with YoutubeDL({"quiet": True}) as ydl:
        return ydl.extract_info(url, download=False)


# ---------------- HANDLE MESSAGE ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📁 Saved Videos":
        await show_saved(update, context)
        return

    if "tiktok.com" not in text:
        return

    msg = await update.message.reply_text("Checking video...")

    try:
        info = get_info(text)
        duration = info.get("duration", 0)

        if duration and duration > MAX_DURATION:
            await msg.edit_text("❌ Video too long (only short videos allowed).")
            return

        file_name = f"{uuid.uuid4()}.mp4"

        ydl_opts = {
            "format": "mp4/best",
            "outtmpl": file_name,
            "quiet": True,
        }

        await msg.edit_text("⬇️ Downloading TikTok video...")

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([text])

        await msg.edit_text("📤 Uploading...")

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💾 Save Video", callback_data=file_name)]
        ])

        with open(file_name, "rb") as video:
            sent = await update.message.reply_video(
                video=video,
                caption="🎬 TikTok Video Ready",
                reply_markup=keyboard
            )

        context.bot_data[file_name] = {
            "file_id": sent.video.file_id,
            "title": info.get("title", "TikTok Video")
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

    await query.edit_message_caption("💾 Saved Successfully!")


# ---------------- SHOW SAVED ----------------
async def show_saved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT file_id, title FROM videos ORDER BY id DESC")
    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("No saved videos yet.")
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

    print("TikTok Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
