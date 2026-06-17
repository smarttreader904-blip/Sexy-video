import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import BOT_TOKEN, ADMINS
from database import add_user, create_db

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# =========================
# FSM STATES
# =========================

class AddMethodState(StatesGroup):
    platform = State()
    country = State()
    custom_country = State()
    method = State()


# =========================
# START MESSAGE
# =========================

@dp.message(CommandStart())
async def start_cmd(message: Message):
    await add_user(
        message.from_user.id,
        message.from_user.full_name,
        message.from_user.username
    )

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "➕ Add Method", "callback_data": "add_method"},
                {"text": "👑 Admin Panel", "callback_data": "admin_panel"}
            ]
        ]
    }

    await message.answer(
        "👋 Welcome to Method Bot",
        reply_markup=keyboard
    )


# =========================
# ADD METHOD BUTTON
# =========================

@dp.callback_query(F.data == "add_method")
async def add_method(call: CallbackQuery, state: FSMContext):

    await state.set_state(AddMethodState.platform)

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "Telegram", "callback_data": "platform_Telegram"},
                {"text": "WhatsApp", "callback_data": "platform_WhatsApp"}
            ],
            [
                {"text": "Facebook", "callback_data": "platform_Facebook"},
                {"text": "TikTok", "callback_data": "platform_TikTok"}
            ]
        ]
    }

    await call.message.edit_text(
        "📱 Select Platform",
        reply_markup=keyboard
    )


# =========================
# ADMIN PANEL BUTTON
# =========================

@dp.callback_query(F.data == "admin_panel")
async def admin_panel(call: CallbackQuery):

    if call.from_user.id not in ADMINS:
        return await call.answer("Access Denied", show_alert=True)

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "📊 Statistics", "callback_data": "statistics"}
            ],
            [
                {"text": "📥 Pending Requests", "callback_data": "pending"}
            ],
            [
                {"text": "📢 Broadcast", "callback_data": "broadcast"}
            ]
        ]
    }

    await call.message.edit_text(
        "👑 Admin Panel",
        reply_markup=keyboard
    )


# =========================
# PLACEHOLDER (NEXT PART)
# =========================

@dp.callback_query(F.data == "statistics")
async def stats(call: CallbackQuery):
    await call.answer("Coming in next part", show_alert=True)


@dp.callback_query(F.data == "pending")
async def pending(call: CallbackQuery):
    await call.answer("Coming in next part", show_alert=True)


@dp.callback_query(F.data == "broadcast")
async def broadcast(call: CallbackQuery):
    await call.answer("Coming in next part", show_alert=True)


# =========================
# START BOT
# =========================

async def main():
    await create_db()
    print("Bot Started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
    from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import DEFAULT_COUNTRIES
from database import add_method, add_pending_request


# =========================
# PLATFORM SELECT
# =========================

@dp.callback_query(F.data.startswith("platform_"))
async def select_platform(call: CallbackQuery, state: FSMContext):

    platform = call.data.split("_")[1]

    await state.update_data(platform=platform)
    await state.set_state(AddMethodState.country)

    keyboard = {
        "inline_keyboard": [
            [{"text": c, "callback_data": f"country_{c}"}]
            for c in DEFAULT_COUNTRIES
        ]
    }

    await call.message.edit_text(
        "🌍 Select Country",
        reply_markup=keyboard
    )


# =========================
# COUNTRY SELECT
# =========================

@dp.callback_query(F.data.startswith("country_"))
async def select_country(call: CallbackQuery, state: FSMContext):

    country = call.data.split("_")[1]

    # Others case
    if country == "Others":
        await state.set_state(AddMethodState.custom_country)
        await call.message.edit_text("✏️ Send country name:")
        return

    await state.update_data(country=country)
    await state.set_state(AddMethodState.method)

    await call.message.edit_text("📝 Send your method:")


# =========================
# CUSTOM COUNTRY INPUT
# =========================

@dp.message(AddMethodState.custom_country)
async def custom_country(message: Message, state: FSMContext):

    await state.update_data(country=message.text)
    await state.set_state(AddMethodState.method)

    await message.answer("📝 Send your method:")


# =========================
# METHOD INPUT (USER SEND)
# =========================

@dp.message(AddMethodState.method)
async def receive_method(message: Message, state: FSMContext):

    data = await state.get_data()

    platform = data["platform"]
    country = data["country"]
    method = message.text
    user_id = message.from_user.id

    # =====================
    # ADMIN DIRECT ADD
    # =====================

    if user_id in ADMINS:

        await add_method(platform, country, method, user_id)

        await message.answer("✅ Method added successfully (Admin)")

        await state.clear()
        return

    # =====================
    # USER → PENDING REQUEST
    # =====================

    await add_pending_request(
        user_id,
        platform,
        country,
        method
    )

    await message.answer("⏳ Sent for admin approval")

    await state.clear()
    from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import (
    get_pending_requests,
    get_pending_request,
    approve_request,
    reject_request,
    add_method
)


# =========================
# VIEW PENDING REQUESTS
# =========================

@dp.callback_query(F.data == "pending")
async def show_pending(call: CallbackQuery):

    if call.from_user.id not in ADMINS:
        return await call.answer("Access Denied", show_alert=True)

    requests = await get_pending_requests()

    if not requests:
        return await call.message.edit_text("📭 No pending requests")

    for r in requests:
        req_id = r[0]
        user_id = r[1]
        platform = r[2]
        country = r[3]
        method = r[4]

        text = (
            f"🆕 Request ID: {req_id}\n\n"
            f"📱 Platform: {platform}\n"
            f"🌍 Country: {country}\n\n"
            f"📄 Method:\n{method}\n\n"
            f"👤 User ID: {user_id}"
        )

        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Accept", "callback_data": f"accept_{req_id}"},
                    {"text": "❌ Reject", "callback_data": f"reject_{req_id}"}
                ]
            ]
        }

        await call.message.answer(text, reply_markup=keyboard)


# =========================
# ACCEPT REQUEST
# =========================

@dp.callback_query(F.data.startswith("accept_"))
async def accept_request(call: CallbackQuery):

    if call.from_user.id not in ADMINS:
        return await call.answer("Denied", show_alert=True)

    req_id = int(call.data.split("_")[1])

    req = await get_pending_request(req_id)

    if not req:
        return await call.answer("Not found")

    user_id = req[1]
    platform = req[2]
    country = req[3]
    method = req[4]

    # save method
    await add_method(platform, country, method, user_id)

    await approve_request(req_id)

    # notify user
    try:
        await bot.send_message(
            user_id,
            "✅ Your method has been approved!"
        )
    except:
        pass

    await call.message.edit_text("✅ Approved")


# =========================
# REJECT START
# =========================

class RejectState(StatesGroup):
    reason = State()


@dp.callback_query(F.data.startswith("reject_"))
async def reject_start(call: CallbackQuery, state: FSMContext):

    if call.from_user.id not in ADMINS:
        return await call.answer("Denied", show_alert=True)

    req_id = int(call.data.split("_")[1])

    await state.update_data(req_id=req_id)
    await state.set_state(RejectState.reason)

    await call.message.answer("❌ Send reject reason:")


# =========================
# REJECT REASON SAVE
# =========================

@dp.message(RejectState.reason)
async def reject_reason(message: Message, state: FSMContext):

    data = await state.get_data()
    req_id = data["req_id"]

    req = await get_pending_request(req_id)

    if not req:
        await message.answer("Not found")
        return await state.clear()

    user_id = req[1]

    await reject_request(req_id)

    # notify user
    try:
        await bot.send_message(
            user_id,
            f"❌ Rejected\nReason: {message.text}"
        )
    except:
        pass

    await message.answer("❌ Request rejected")

    await state.clear()
    from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import (
    get_all_users,
    get_statistics,
    add_broadcast_history,
    add_support_message
)


# =========================
# STATISTICS
# =========================

@dp.callback_query(F.data == "statistics")
async def statistics(call: CallbackQuery):

    if call.from_user.id not in ADMINS:
        return await call.answer("Denied", show_alert=True)

    stats = await get_statistics()

    text = (
        "📊 Statistics\n\n"
        f"👤 Users: {stats['users']}\n"
        f"🌍 Countries: {stats['countries']}\n"
        f"📄 Methods: {stats['methods']}\n"
        f"⏳ Pending: {stats['pending']}"
    )

    await call.message.edit_text(text)


# =========================
# BROADCAST STATE
# =========================

class BroadcastState(StatesGroup):
    message = State()


# =========================
# BROADCAST START
# =========================

@dp.callback_query(F.data == "broadcast")
async def broadcast_start(call: CallbackQuery, state: FSMContext):

    if call.from_user.id not in ADMINS:
        return await call.answer("Denied", show_alert=True)

    await state.set_state(BroadcastState.message)

    await call.message.answer("📢 Send broadcast message:")


# =========================
# BROADCAST SEND
# =========================

@dp.message(BroadcastState.message)
async def broadcast_send(message: Message, state: FSMContext):

    users = await get_all_users()

    sent = 0
    failed = 0

    for u in users:
        try:
            await bot.send_message(u[0], message.text)
            sent += 1
        except:
            failed += 1

    await add_broadcast_history(message.text)

    await message.answer(
        f"📢 Broadcast Done\n\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}"
    )

    await state.clear()


# =========================
# SUPPORT SYSTEM
# =========================

class SupportState(StatesGroup):
    message = State()


# USER SEND SUPPORT
@dp.callback_query(F.data == "support")
async def support_start(call: CallbackQuery, state: FSMContext):

    await state.set_state(SupportState.message)

    await call.message.answer("🛠 Send your problem:")


@dp.message(SupportState.message)
async def support_send(message: Message, state: FSMContext):

    user_id = message.from_user.id

    await add_support_message(user_id, message.text)

    # send to admin
    for admin in ADMINS:

        try:
            await bot.send_message(
                admin,
                f"🛠 Support Request\n\n"
                f"User: {message.from_user.full_name}\n"
                f"ID: {user_id}\n\n"
                f"{message.text}"
            )
        except:
            pass

    await message.answer("✅ Sent to admin")

    await state.clear()


# =========================
# BOT RUNNER
# =========================

async def main():

    await create_db()

    print("Bot Started Successfully 🚀")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
    
