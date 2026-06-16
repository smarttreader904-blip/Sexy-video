import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = "8859975301:AAEqR6ut9U_Vh77slUhAj5RdbwQmt2OoTXk"
ADMIN_ID = 8559227368

PASSWORD = "904"   # 🔐 Change your password here

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


# ---------------- CHECK AUTH ----------------
def is_admin(user_id):
    return user_id == ADMIN_ID


def is_logged_in(context):
    return context.user_data.get("auth") == True


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return

    context.user_data["auth"] = False

    await update.message.reply_text(
        "🔐 Enter your password to access the bot:"
    )


# ---------------- PASSWORD CHECK ----------------
async def password_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if user_id != ADMIN_ID:
        return

    # If not logged in → treat as password
    if not is_logged_in(context):
        if text == PASSWORD:
            context.user_data["auth"] = True
            await update.message.reply_text(
                "✅ Login successful!",
                reply_markup=menu
            )
        else:
            await update.message.reply_text("❌ Wrong password!")
        return


    # ---------------- MENU ----------------
    if text == "📁 Save Gallery":
        context.user_data["save_mode"] = True
        await update.message.reply_text(
            "📥 Send video/photo/voice/text to save."
        )
        return

    if text == "📂 Show Memory":
        cursor.execute("SELECT type,file_id,text FROM storage ORDER BY id DESC")
        rows = cursor.fetchall()

        if not rows:
            await update.message.reply_text("📭 No data found.")
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


# ---------------- SAVE DATA ----------------
async def save_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not is_logged_in(context):
        return

    if not context.user_data.get("save_mode"):
        return

    msg = update.message

    if msg.video:
        cursor.execute("INSERT INTO storage VALUES (NULL,?,?,?)",
                       ("video", msg.video.file_id, "Video"))
        conn.commit()
        await msg.reply_text("💾 Saved Video")
        return

    if msg.photo:
        cursor.execute("INSERT INTO storage VALUES (NULL,?,?,?)",
                       ("photo", msg.photo[-1].file_id, "Photo"))
        conn.commit()
        await msg.reply_text("💾 Saved Photo")
        return

    if msg.voice:
        cursor.execute("INSERT INTO storage VALUES (NULL,?,?,?)",
                       ("voice", msg.voice.file_id, "Voice"))
        conn.commit()
        await msg.reply_text("💾 Saved Voice")
        return

    if msg.text:
        cursor.execute("INSERT INTO storage VALUES (NULL,?,?,?)",
                       ("text", "", msg.text))
        conn.commit()
        await msg.reply_text("💾 Saved Text")


# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # password + menu
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, password_handler))

    # media save
    app.add_handler(MessageHandler(filters.ALL, save_handler))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
