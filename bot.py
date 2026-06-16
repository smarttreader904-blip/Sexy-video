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
from database import (
    init_db,
    add_user,
    add_pending,
    get_methods,
    get_pending,
    delete_pending,
    add_method,
    total_users
)

# ================= INIT =================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

SERVICES = ["WhatsApp", "Telegram", "TikTok", "Facebook"]

COUNTRIES = ["Bangladesh", "India", "Pakistan", "USA", "UK", "Other"]


# ================= KEYBOARD =================
def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Add Method", callback_data="add_method")],
            [InlineKeyboardButton(text="👑 Admin Panel", callback_data="admin_panel")],
            [InlineKeyboardButton(text="🆘 Support", callback_data="support")],
            [InlineKeyboardButton(text="📲 WhatsApp", callback_data="service_WhatsApp")],
            [InlineKeyboardButton(text="✈️ Telegram", callback_data="service_Telegram")],
            [InlineKeyboardButton(text="🎵 TikTok", callback_data="service_TikTok")],
            [InlineKeyboardButton(text="📘 Facebook", callback_data="service_Facebook")]
        ]
    )


# ================= START =================
@dp.message(CommandStart())
async def start_cmd(message: Message):
    await add_user(message.from_user.id)

    await message.answer(
        f"""
🎉 Welcome {message.from_user.first_name}

━━━━━━━━━━━━━━
🔥 Method Bot
🌍 Countries Supported
⚡ Fast System
━━━━━━━━━━━━━━

👇 Select Option
""",
        reply_markup=main_menu()
    )


# ================= SERVICE =================
@dp.callback_query(F.data.startswith("service_"))
async def service(call: CallbackQuery):

    service = call.data.split("_")[1]

    keyboard = [
        [InlineKeyboardButton(text=f"🌍 {c}", callback_data=f"country_{service}_{c}")]
        for c in COUNTRIES
    ]

    keyboard.append([InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")])

    await call.message.edit_text(
        f"📲 Service: {service}\n\n🌍 Select Country",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


# ================= COUNTRY =================
@dp.callback_query(F.data.startswith("country_"))
async def country(call: CallbackQuery):

    _, service, country = call.data.split("_")

    methods = await get_methods(service, country)

    if not methods:
        text = f"❌ No Methods\n\n{service} | {country}"
    else:
        text = f"✅ Methods\n\n{service} | {country}\n\n"
        for i, m in enumerate(methods, 1):
            text += f"{i}. {m[0]}\n"

    await call.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]
            ]
        )
    )


# ================= MAIN =================
@dp.callback_query(F.data == "main_menu")
async def main(call: CallbackQuery):
    await call.message.edit_text("🏠 Main Menu", reply_markup=main_menu())


# ================= SUPPORT =================
@dp.callback_query(F.data == "support")
async def support(call: CallbackQuery):
    await call.message.edit_text(
        "🆘 Support: @YOUR_USERNAME",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🏠 Main Menu", callback_data="main_menu")]]
        )
    )


# ================= ADD METHOD STATES =================
class AddMethod(StatesGroup):
    service = State()
    country = State()
    method = State()


# ================= ADD METHOD =================
@dp.callback_query(F.data == "add_method")
async def add_method_menu(call: CallbackQuery):

    keyboard = [
        [InlineKeyboardButton(text=s, callback_data=f"addservice_{s}")]
        for s in SERVICES
    ]

    await call.message.edit_text(
        "➕ Select Service",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@dp.callback_query(F.data.startswith("addservice_"))
async def add_service(call: CallbackQuery, state: FSMContext):

    service = call.data.split("_")[1]
    await state.update_data(service=service)

    keyboard = [
        [InlineKeyboardButton(text=c, callback_data=f"addcountry_{c}")]
        for c in COUNTRIES
    ]

    await call.message.edit_text(
        "🌍 Select Country",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@dp.callback_query(F.data.startswith("addcountry_"))
async def add_country(call: CallbackQuery, state: FSMContext):

    country = call.data.split("_")[1]

    if country == "Other":
        await state.set_state(AddMethod.country)
        await call.message.answer("🌍 Send Country Name")
        return

    await state.update_data(country=country)
    await state.set_state(AddMethod.method)

    await call.message.answer("📝 Send Method Text")


# ================= OTHER COUNTRY =================
@dp.message(AddMethod.country)
async def other_country(message: Message, state: FSMContext):

    await state.update_data(country=message.text)
    await state.set_state(AddMethod.method)

    await message.answer("📝 Send Method Text")


# ================= SAVE METHOD (IMPORTANT FIX) =================
@dp.message(AddMethod.method)
async def save_method(message: Message, state: FSMContext):

    data = await state.get_data()

    service = data["service"]
    country = data["country"]
    text = message.text

    # ================= ADMIN DIRECT ADD =================
    if message.from_user.id in ADMINS:

        await add_method(service, country, text)

        await message.answer("✅ Admin Method Added Directly")

    else:

        await add_pending(
            message.from_user.id,
            service,
            country,
            text
        )

        await message.answer("⏳ Sent to Admin for Approval")

    await state.clear()


# ================= ADMIN PANEL =================
@dp.callback_query(F.data == "admin_panel")
async def admin(call: CallbackQuery):

    if call.from_user.id not in ADMINS:
        return await call.answer("❌ Not Admin", show_alert=True)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Pending", callback_data="pending")],
            [InlineKeyboardButton(text="📊 Stats", callback_data="stats")],
        ]
    )

    await call.message.edit_text("👑 Admin Panel", reply_markup=keyboard)


# ================= PENDING =================
@dp.callback_query(F.data == "pending")
async def pending(call: CallbackQuery):

    rows = await get_pending()

    if not rows:
        return await call.message.edit_text("No Pending Requests")

    for r in rows:
        pid, uid, service, country, method = r

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Approve", callback_data=f"approve_{pid}"),
                    InlineKeyboardButton(text="❌ Reject", callback_data=f"reject_{pid}")
                ]
            ]
        )

        await call.message.answer(
            f"👤 {uid}\n📲 {service}\n🌍 {country}\n\n{method}",
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


# ================= MAIN =================
async def main():
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
