import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = "8859975301:AAEqR6ut9U_Vh77slUhAj5RdbwQmt2OoTXk"

# ---------------- DATABASE ----------------
conn = sqlite3.connect("data.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS saved (
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
        ["📁 Saved Videos", "📁 Saved Videos 2"]
    ],
    resize_keyboard=True
)


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome!", reply_markup=menu)


# ---------------- HANDLE TEXT / MEDIA ----------------
async def handle_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # ---------- SAVED LIST ----------
    if text == "📁 Saved Videos":
        cursor.execute("SELECT type, file_id, text FROM saved ORDER BY id DESC")
        rows = cursor.fetchall()

        if not rows:
            await update.message.reply_text("No saved items.")
            return

        for t, file_id, txt in rows:
            if t == "video":
                await update.message.reply_video(file_id, caption=txt or "")
            elif t == "photo":
                await update.message.reply_photo(file_id, caption=txt or "")
            else:
                await update.message.reply_text(txt or "")

        return

    # ---------- SAVE MODE MESSAGE ----------
    if context.user_data.get("save_mode"):
        if update.message.video:
            file_id = update.message.video.file_id
            cursor.execute("INSERT INTO saved (type,file_id,text) VALUES (?,?,?)",
                           ("video", file_id, "Saved Video"))
            conn.commit()
            await update.message.reply_text("💾 Video saved!")
            return

        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            cursor.execute("INSERT INTO saved (type,file_id,text) VALUES (?,?,?)",
                           ("photo", file_id, "Saved Photo"))
            conn.commit()
            await update.message.reply_text("💾 Photo saved!")
            return

        if text:
            cursor.execute("INSERT INTO saved (type,file_id,text) VALUES (?,?,?)",
                           ("text", "", text))
            conn.commit()
            await update.message.reply_text("💾 Text saved!")
            return

    # ---------- DEFAULT LINK HANDLING ----------
    await update.message.reply_text("Send something or use menu.")


# ---------------- SAVE MODE BUTTON ----------------
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📁 Saved Videos 2":
        context.user_data["save_mode"] = True
        await update.message.reply_text(
            "📥 Send your video, photo or link.\nIt will be saved automatically."
        )


# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, menu_handler))
    app.add_handler(MessageHandler(filters.ALL, handle_all))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
