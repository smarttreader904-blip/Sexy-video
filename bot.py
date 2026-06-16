import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = "8859975301:AAEqR6ut9U_Vh77slUhAj5RdbwQmt2OoTXk"
ADMIN_ID = 8559227368
PASSWORD = "1234"

# ---------------- DATABASE ----------------
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
        ["📂 Show Link", "📂 Show Photo"]
    ],
    resize_keyboard=True
)


# ---------------- AUTH ----------------
def is_admin(user_id):
    return user_id == ADMIN_ID


def logged(context):
    return context.user_data.get("auth") == True


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized")
        return

    context.user_data["auth"] = False
    await update.message.reply_text("🔐 Enter password:")


# ---------------- MAIN HANDLER ----------------
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    text = update.message.text

    # -------- PASSWORD --------
    if not logged(context):
        if text == PASSWORD:
            context.user_data["auth"] = True
            await update.message.reply_text("✅ Login successful!", reply_markup=menu)
        else:
            await update.message.reply_text("❌ Wrong password")
        return

    # -------- SAVE MODE --------
    if text == "📁 Save Gallery":
        context.user_data["save_mode"] = True
        await update.message.reply_text(
            "📥 Send video, photo or link.\nVoice system is OFF."
        )
        return

    # -------- SHOW MEMORY (ORDERED) --------
    if text == "📂 Show Memory":

        # VIDEOS FIRST
        cursor.execute("SELECT file_id,text FROM storage WHERE type='video' ORDER BY id DESC")
        videos = cursor.fetchall()

        # PHOTOS SECOND
        cursor.execute("SELECT file_id,text FROM storage WHERE type='photo' ORDER BY id DESC")
        photos = cursor.fetchall()

        # LINKS LAST
        cursor.execute("SELECT text FROM storage WHERE type='link' ORDER BY id DESC")
        links = cursor.fetchall()

        if not videos and not photos and not links:
            await update.message.reply_text("📭 Empty storage")
            return

        await update.message.reply_text("🎬 VIDEOS:")
        for f, t in videos:
            await update.message.reply_video(f, caption=t or "")

        await update.message.reply_text("🖼 PHOTOS:")
        for f, t in photos:
            await update.message.reply_photo(f, caption=t or "")

        await update.message.reply_text("🔗 LINKS:")
        for (t,) in links:
            await update.message.reply_text(t)

        return

    # -------- SHOW LINKS ONLY --------
    if text == "📂 Show Link":
        cursor.execute("SELECT text FROM storage WHERE type='link' ORDER BY id DESC")
        rows = cursor.fetchall()

        if not rows:
            await update.message.reply_text("No links found")
            return

        for (t,) in rows:
            await update.message.reply_text(t)

        return

    # -------- SHOW PHOTOS ONLY --------
    if text == "📂 Show Photo":
        cursor.execute("SELECT file_id,text FROM storage WHERE type='photo' ORDER BY id DESC")
        rows = cursor.fetchall()

        if not rows:
            await update.message.reply_text("No photos found")
            return

        for f, t in rows:
            await update.message.reply_photo(f, caption=t or "")

        return


# ---------------- SAVE HANDLER ----------------
async def save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not logged(context):
        return

    if not context.user_data.get("save_mode"):
        return

    msg = update.message

    # VIDEO
    if msg.video:
        cursor.execute("INSERT INTO storage(type,file_id,text) VALUES (?,?,?)",
                       ("video", msg.video.file_id, "Video"))
        conn.commit()
        await msg.reply_text("💾 Video saved")
        return

    # PHOTO
    if msg.photo:
        cursor.execute("INSERT INTO storage(type,file_id,text) VALUES (?,?,?)",
                       ("photo", msg.photo[-1].file_id, "Photo"))
        conn.commit()
        await msg.reply_text("💾 Photo saved")
        return

    # LINK (TEXT)
    if msg.text and "http" in msg.text:
        cursor.execute("INSERT INTO storage(type,file_id,text) VALUES (?,?,?)",
                       ("link", "", msg.text))
        conn.commit()
        await msg.reply_text("💾 Link saved")
        return


# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handler))
    app.add_handler(MessageHandler(filters.ALL, save))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
