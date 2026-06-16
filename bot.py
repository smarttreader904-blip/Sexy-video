import asyncio
import aiosqlite

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from config import BOT_TOKEN, ADMINS
from database import *

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

SERVICES = ["WhatsApp", "Telegram", "TikTok", "Facebook"]

COUNTRIES = ["Bangladesh", "India", "Pakistan", "USA", "UK", "Other"]


# ================= MENU =================
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Add Method", callback_data="add_method")],
        [InlineKeyboardButton(text="👑 Admin Panel", callback_data="admin_panel")],
        [InlineKeyboardButton(text="🆘 Support", callback_data="support")],
    ])


# ================= START =================
@dp.message(CommandStart())
async def start_cmd(message: Message):
    await add_user(message.from_user.id)

    await message.answer(
        f"""
👋 Welcome {message.from_user.first_name}

📌 Please choose from menu below
""",
        reply_markup=main_menu()
    )


# ================= SERVICE =================
@dp.callback_query(F.data == "add_method")
async def add_method_menu(call: CallbackQuery):

    keyboard = [
        [InlineKeyboardButton(text=s, callback_data=f"service_{s}")]
        for s in SERVICES
    ]

    await call.message.edit_text(
        "📲 Select Service",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


# ================= SERVICE SELECT =================
@dp.callback_query(F.data.startswith("service_"))
async def service_select(call: CallbackQuery, state: FSMContext):

    service = call.data.split("_")[1]
    await state.update_data(service=service)

    keyboard = [
        [InlineKeyboardButton(text=c, callback_data=f"country_{c}")]
        for c in COUNTRIES
    ]

    await call.message.edit_text(
        "🌍 Select Country",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


# ================= COUNTRY SELECT =================
@dp.callback_query(F.data.startswith("country_"))
async def country_select(call: CallbackQuery, state: FSMContext):

    country = call.data.split("_")[1]

    if country == "Other":
        await state.set_state(AddState.country)
        await call.message.answer("🌍 Send Country Name:")
        return

    await state.update_data(country=country)
    await state.set_state(AddState.method)

    await call.message.answer("📝 Send Method Text:")


# ================= STATES =================
class AddState(StatesGroup):
    country = State()
    method = State()


# ================= CUSTOM COUNTRY =================
@dp.message(AddState.country)
async def custom_country(message: Message, state: FSMContext):

    await state.update_data(country=message.text)
    await state.set_state(AddState.method)

    await message.answer("📝 Now send method:")


# ================= METHOD SAVE =================
@dp.message(AddState.method)
async def save_method(message: Message, state: FSMContext):

    data = await state.get_data()

    service = data["service"]
    country = data["country"]
    method = message.text

    # pending system
    await add_pending(message.from_user.id, service, country, method)

    await state.clear()

    await message.answer("⏳ Sent to admin for approval")

    # notify admins
    for admin in ADMINS:
        try:
            await bot.send_message(
                admin,
                f"""
🚨 NEW METHOD REQUEST

📲 Service: {service}
🌍 Country: {country}

📝 Method:
{method}

✔ Approve / Reject from admin panel
"""
            )
        except:
            pass


# ================= ADMIN PANEL =================
@dp.callback_query(F.data == "admin_panel")
async def admin_panel(call: CallbackQuery):

    if call.from_user.id not in ADMINS:
        return await call.answer("Not Admin", show_alert=True)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Pending", callback_data="pending")],
        [InlineKeyboardButton(text="📊 Stats", callback_data="stats")],
        [InlineKeyboardButton(text="🏠 Menu", callback_data="main_menu")]
    ])

    await call.message.edit_text("👑 Admin Panel", reply_markup=keyboard)


# ================= PENDING =================
@dp.callback_query(F.data == "pending")
async def pending(call: CallbackQuery):

    rows = await get_pending()

    if not rows:
        return await call.message.edit_text("No pending requests")

    for r in rows:
        pid, uid, service, country, method = r

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Accept", callback_data=f"approve_{pid}"),
                InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_{pid}")
            ]
        ])

        await call.message.answer(
            f"""
📌 Pending Request

📲 {service}
🌍 {country}

📝 {method}
""",
            reply_markup=keyboard
        )


# ================= APPROVE =================
@dp.callback_query(F.data.startswith("approve_"))
async def approve(call: CallbackQuery):

    pid = int(call.data.split("_")[1])

    rows = await get_pending()

    for r in rows:
        if r[0] == pid:

            await add_method(r[2], r[3], r[4])
            await delete_pending(pid)

            # notify all users
            users = await aiosqlite.connect("users.db")
            cur = await users.execute("SELECT user_id FROM users")
            all_users = await cur.fetchall()

            for u in all_users:
                try:
                    await bot.send_message(
                        u[0],
                        f"""
🎉 NEW METHOD ADDED

📲 {r[2]}
🌍 {r[3]}

📝 Use /start to view
"""
                    )
                except:
                    pass

    await call.message.edit_text("✅ Approved")


# ================= REJECT =================
@dp.callback_query(F.data.startswith("reject_"))
async def reject(call: CallbackQuery):

    pid = int(call.data.split("_")[1])

    await delete_pending(pid)

    await call.message.edit_text("❌ Rejected")


# ================= STATS =================
@dp.callback_query(F.data == "stats")
async def stats(call: CallbackQuery):

    users = await total_users()

    await call.message.edit_text(f"👥 Users: {users}")


# ================= SUPPORT =================
@dp.callback_query(F.data == "support")
async def support(call: CallbackQuery):

    await call.message.answer("🆘 Send your problem here:")


# ================= SUPPORT MESSAGE =================
@dp.message()
async def support_msg(message: Message):

    if message.text and message.text.startswith("/"):
        return

    for admin in ADMINS:
        try:
            await bot.send_message(admin, f"📩 Support:\n{message.text}")
        except:
            pass

    await message.answer("✅ Sent to admin")


# ================= MAIN =================
async def main():
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
