import os
import uuid
from yt_dlp import YoutubeDL
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters

BOT_TOKEN = "8859975301:AAEqR6ut9U_Vh77slUhAj5RdbwQmt2OoTXk"

MAX_DURATION = 180  # 3 minutes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
🎬 Welcome to Shorts Downloader Bot!

━━━━━━━━━━━━━━
📥 Download YouTube Shorts
⚡ Fast Download Speed
🎞 HD Quality Supported
🗑 Auto File Delete
🕒 Only videos up to 3 minutes
━━━━━━━━━━━━━━

🔗 Send your YouTube Shorts link now.
"""
    await update.message.reply_text(text)


def get_video_info(url):
    with YoutubeDL({"quiet": True}) as ydl:
        return ydl.extract_info(url, download=False)


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "youtube.com" not in url and "youtu.be" not in url:
        return

    msg = await update.message.reply_text(
"🔍 Analyzing your video...\n⏳ Please wait."
)

    try:
        info = get_video_info(url)

        duration = info.get("duration", 0)

        if duration > MAX_DURATION:
            await msg.edit_text(
                "❌ Only YouTube Shorts or videos under 3 minutes are allowed."
            )
            return

        unique_name = f"{uuid.uuid4()}.mp4"

        ydl_opts = {
            "format": "mp4/best",
            "outtmpl": unique_name,
            "quiet": True,
        }

        await msg.edit_text(
"⬇️ Downloading your Shorts...\n🚀 Processing video..."
)

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        await msg.edit_text(
"📤 Uploading to Telegram...\n✨ Almost done..."
)

        with open(unique_name, "rb") as video:
            await update.message.reply_video(video=video)

        if os.path.exists(unique_name):
            os.remove(unique_name)

        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"Error: {str(e)}")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link)
    )

    print("Bot Started...")
    app.run_polling()


if __name__ == "__main__":
    main()
