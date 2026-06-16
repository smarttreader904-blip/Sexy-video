import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = "8859975301:AAEqR6ut9U_Vh77slUhAj5RdbwQmt2OoTXk"
ADMIN_ID = 8559227368
PASSWORD = "352616"

# ---------------- DB ----------------
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS storage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    file_id TEXT,
    text TEXT
)
""")
conn.commit()


# ---------------- MENU ----------------
menu = ReplyKeyboardMarkup(
    [
        ["📁 Save Gallery", "📂 Show Memory"],
        ["📂 Show Text", "📂 Show Photo"]
    ],
    resize_keyboard=True
)


# ---------------- AUTH ----------------
def is_admin(uid):
    return uid == ADMIN_ID


def logged(context):
    return context.user_data.get("auth") == True


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not allowed")
        return

    context.user_data["auth"] = False
    await update.message.reply_text("🔐 Enter password:")


# ---------------- LOGIN + MENU ----------------
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    text = update.message.text

    # LOGIN
    if not logged(context):
        if text == PASSWORD:
            context.user_data["auth"] = True
            await update.message.reply_text("✅ Logged in", reply_markup=menu)
        else:
            await update.message.reply_text("❌ Wrong password")
        return

    # ---------------- SAVE MODE ----------------
    if text == "📁 Save Gallery":
        context.user_data["save_mode"] = True
        await update.message.reply_text("📥 Send video/photo/text to save")
        return

    # ---------------- SHOW MEMORY (FULL ORDER) ----------------
    if text == "📂 Show Memory":
        # VIDEOS
        cursor.execute("SELECT file_id,text FROM storage WHERE type='video' ORDER BY id DESC")
        videos = cursor.fetchall()

        for file_id, txt in videos:
            await update.message.reply_video(file_id, caption=txt or "")

        # PHOTOS
        cursor.execute("SELECT file_id,text FROM storage WHERE type='photo' ORDER BY id DESC")
        photos = cursor.fetchall()

        for file_id, txt in photos:
            await update.message.reply_photo(file_id, caption=txt or "")

        # LINKS (TEXT containing http)
        cursor.execute("SELECT text FROM storage WHERE type='text' ORDER BY id DESC")
        texts = cursor.fetchall()

        for (t,) in texts:
            if "http" in t:
                await update.message.reply_text(f"🔗 {t}")

        return

    # ---------------- SHOW TEXT ONLY ----------------
    if text == "📂 Show Text":
        cursor.execute("SELECT text FROM storage WHERE type='text' ORDER BY id DESC")
        rows = cursor.fetchall()

        for (t,) in rows:
            await update.message.reply_text(t)

        return

    # ---------------- SHOW PHOTO ONLY ----------------
    if text == "📂 Show Photo":
        cursor.execute("SELECT file_id FROM storage WHERE type='photo' ORDER BY id DESC")
        rows = cursor.fetchall()

        for (file_id,) in rows:
            await update.message.reply_photo(file_id)

        return


# ---------------- SAVE HANDLER ----------------
async def save_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not logged(context):
        return

    if not context.user_data.get("save_mode"):
        return

    msg = update.message

    # VIDEO
    if msg.video:
        cursor.execute("INSERT INTO storage VALUES (NULL,'video',?,?)",
                       (msg.video.file_id, "Video"))
        conn.commit()
        await msg.reply_text("💾 Video saved")
        return

    # PHOTO
    if msg.photo:
        cursor.execute("INSERT INTO storage VALUES (NULL,'photo',?,?)",
                       (msg.photo[-1].file_id, "Photo"))
        conn.commit()
        await msg.reply_text("💾 Photo saved")
        return

    # TEXT / LINK
    if msg.text:
        cursor.execute("INSERT INTO storage VALUES (NULL,'text','',?)",
                       (msg.text,))
        conn.commit()
        await msg.reply_text("💾 Text saved")
        return


# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))
    app.add_handler(MessageHandler(filters.ALL, save_handler))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
