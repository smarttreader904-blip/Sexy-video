import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = "8859975301:AAEqR6ut9U_Vh77slUhAj5RdbwQmt2OoTXk"

ADMIN_ID = 8559227368

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
        ["📁 Save Gallery", "📂 Show Memory"]
    ],
    resize_keyboard=True
)


# ---------------- ADMIN CHECK ----------------
def is_admin(user_id):
    return user_id == ADMIN_ID


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return

    msg = """
━━━━━━━━━━━━━━━
👋 Welcome to Admin Vault Bot
━━━━━━━━━━━━━━━

📌 This is your private storage system.

Use the buttons below:
"""
    await update.message.reply_text(msg, reply_markup=menu)


# ---------------- MENU HANDLER ----------------
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    text = update.message.text

    # -------- SAVE MODE --------
    if text == "📁 Save Gallery":
        context.user_data["save_mode"] = True

        await update.message.reply_text(
            "📥 Send anything:\n\n"
            "✔ Video\n✔ Photo\n✔ Voice\n✔ Text\n\n"
            "It will be saved automatically."
        )
        return

    # -------- SHOW MEMORY --------
    if text == "📂 Show Memory":
        cursor.execute("SELECT type, file_id, text FROM storage ORDER BY id DESC")
        rows = cursor.fetchall()

        if not rows:
            await update.message.reply_text("📭 No saved memory found.")
            return

        for t, file_id, txt in rows:
            if t == "video":
                await update.message.reply_video(file_id, caption=txt or "")
            elif t == "photo":
                await update.message.reply_photo(file_id, caption=txt or "")
            elif t == "voice":
                await update.message.reply_voice(file_id, caption=txt or "")
            else:
                await update.message.reply_text(txt or "")

        return


# ---------------- SAVE HANDLER ----------------
async def save_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not context.user_data.get("save_mode"):
        return

    msg = update.message

    # VIDEO
    if msg.video:
        file_id = msg.video.file_id
        cursor.execute("INSERT INTO storage (type,file_id,text) VALUES (?,?,?)",
                       ("video", file_id, "Saved Video"))
        conn.commit()
        await msg.reply_text("💾 Video saved!")
        return

    # PHOTO
    if msg.photo:
        file_id = msg.photo[-1].file_id
        cursor.execute("INSERT INTO storage (type,file_id,text) VALUES (?,?,?)",
                       ("photo", file_id, "Saved Photo"))
        conn.commit()
        await msg.reply_text("💾 Photo saved!")
        return

    # VOICE
    if msg.voice:
        file_id = msg.voice.file_id
        cursor.execute("INSERT INTO storage (type,file_id,text) VALUES (?,?,?)",
                       ("voice", file_id, "Saved Voice"))
        conn.commit()
        await msg.reply_text("💾 Voice saved!")
        return

    # TEXT
    if msg.text:
        cursor.execute("INSERT INTO storage (type,file_id,text) VALUES (?,?,?)",
                       ("text", "", msg.text))
        conn.commit()
        await msg.reply_text("💾 Text saved!")
        return


# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    app.add_handler(MessageHandler(filters.ALL, save_handler))

    print("Admin Vault Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()
