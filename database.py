import aiosqlite

DB_NAME = "users.db"


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS methods(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT,
            country TEXT,
            method TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS pending_methods(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service TEXT,
            country TEXT,
            method TEXT
        )
        """)

        await db.commit()


async def add_user(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users(user_id) VALUES(?)",
            (user_id,)
        )
        await db.commit()


async def add_method(service, country, method):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO methods(service,country,method) VALUES(?,?,?)",
            (service, country, method)
        )
        await db.commit()


async def get_methods(service, country):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT method FROM methods WHERE service=? AND country=?",
            (service, country)
        )
        return await cursor.fetchall()


async def add_pending(user_id, service, country, method):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO pending_methods
            (user_id,service,country,method)
            VALUES(?,?,?,?)
            """,
            (user_id, service, country, method)
        )
        await db.commit()


async def get_pending():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM pending_methods"
        )
        return await cursor.fetchall()


async def delete_pending(pid):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM pending_methods WHERE id=?",
            (pid,)
        )
        await db.commit()


async def total_users():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM users"
        )
        return (await cursor.fetchone())[0]
      from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import *

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


SERVICES = [
    "WhatsApp",
    "Telegram",
    "TikTok",
    "Facebook"
]

COUNTRIES = [
    "Bangladesh",
    "India",
    "Pakistan",
    "USA",
    "UK",
    "Other"
]


def main_menu():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Add Method",
                    callback_data="add_method"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👑 Admin Panel",
                    callback_data="admin_panel"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🆘 Support",
                    callback_data="support"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📲 WhatsApp",
                    callback_data="service_WhatsApp"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✈️ Telegram",
                    callback_data="service_Telegram"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎵 TikTok",
                    callback_data="service_TikTok"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📘 Facebook",
                    callback_data="service_Facebook"
                )
            ]
        ]
    )


@dp.message(CommandStart())
async def start_cmd(message: Message):

    await add_user(message.from_user.id)

    text = f"""
🎉 Welcome {message.from_user.first_name}

━━━━━━━━━━━━━━

🔥 Method Sharing Bot

📚 Find Latest Methods
🌍 Multiple Countries
⚡ Fast Access

━━━━━━━━━━━━━━

👇 Please Select Your Service
"""

    await message.answer(
        text,
        reply_markup=main_menu()
    )


@dp.callback_query(F.data.startswith("service_"))
async def service_selected(call: CallbackQuery):

    service = call.data.replace(
        "service_",
        ""
    )

    keyboard = []

    for country in COUNTRIES:

        keyboard.append([
            InlineKeyboardButton(
                text=f"🌍 {country}",
                callback_data=f"country_{service}_{country}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(
            text="🏠 Main Menu",
            callback_data="main_menu"
        )
    ])

    await call.message.edit_text(
        f"""
📌 Service Selected

✅ {service}

🌍 Please Select Country
""",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=keyboard
        )
    )


@dp.callback_query(F.data.startswith("country_"))
async def country_selected(call: CallbackQuery):

    data = call.data.split("_")

    service = data[1]
    country = data[2]

    methods = await get_methods(
        service,
        country
    )

    if not methods:

        txt = f"""
❌ No Method Available

📲 Service : {service}
🌍 Country : {country}

🕒 Please Check Again Later
"""

    else:

        txt = f"""
✅ Available Methods

📲 Service : {service}
🌍 Country : {country}

━━━━━━━━━━━━━━
"""

        count = 1

        for m in methods:

            txt += f"\n{count}. {m[0]}\n"
            count += 1

    await call.message.edit_text(
        txt,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🏠 Main Menu",
                        callback_data="main_menu"
                    )
                ]
            ]
        )
    )


@dp.callback_query(F.data == "main_menu")
async def back_main(call: CallbackQuery):

    await call.message.edit_text(
        """
🏠 Main Menu

👇 Please Select Service
""",
        reply_markup=main_menu()
    )


@dp.callback_query(F.data == "support")
async def support_btn(call: CallbackQuery):

    await call.message.edit_text(
        """
🆘 Support Center

📩 Contact Admin

@YOUR_USERNAME

⏰ Reply Time:
24 Hours
""",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🏠 Main Menu",
                        callback_data="main_menu"
                    )
                ]
            ]
        )
  from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


class AddMethodState(StatesGroup):
    service = State()
    country = State()
    method = State()


@dp.callback_query(F.data == "add_method")
async def add_method_menu(call: CallbackQuery, state: FSMContext):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📲 WhatsApp",
                    callback_data="addservice_WhatsApp"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✈️ Telegram",
                    callback_data="addservice_Telegram"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎵 TikTok",
                    callback_data="addservice_TikTok"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📘 Facebook",
                    callback_data="addservice_Facebook"
                )
            ]
        ]
    )

    await call.message.edit_text(
        """
➕ Add Method

📌 Please Select Service

⚡ Your Method Will Be Sent To Admin For Review
""",
        reply_markup=keyboard
    )


@dp.callback_query(F.data.startswith("addservice_"))
async def select_add_service(
    call: CallbackQuery,
    state: FSMContext
):

    service = call.data.replace(
        "addservice_",
        ""
    )

    await state.update_data(
        service=service
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🇧🇩 Bangladesh",
                    callback_data="addcountry_Bangladesh"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🇮🇳 India",
                    callback_data="addcountry_India"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🇵🇰 Pakistan",
                    callback_data="addcountry_Pakistan"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🇺🇸 USA",
                    callback_data="addcountry_USA"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🇬🇧 UK",
                    callback_data="addcountry_UK"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🌍 Other",
                    callback_data="addcountry_Other"
                )
            ]
        ]
    )

    await call.message.edit_text(
        """
🌍 Please Select Country
""",
        reply_markup=keyboard
    )


@dp.callback_query(F.data.startswith("addcountry_"))
async def select_country(
    call: CallbackQuery,
    state: FSMContext
):

    country = call.data.replace(
        "addcountry_",
        ""
    )

    if country == "Other":

        await state.set_state(
            AddMethodState.country
        )

        await call.message.answer(
            """
🌍 Please Send Country Name

Example:
Indonesia
Malaysia
Nepal
"""
        )
        return

    await state.update_data(
        country=country
    )

    await state.set_state(
        AddMethodState.method
    )

    await call.message.answer(
        """
📝 Send Your Method

Example:

1. Open App
2. Login Account
3. Complete Verification

⚡ Send Full Method
"""
    )


@dp.message(AddMethodState.country)
async def other_country(
    message: Message,
    state: FSMContext
):

    await state.update_data(
        country=message.text
    )

    await state.set_state(
        AddMethodState.method
    )

    await message.answer(
        """
✅ Country Added

📝 Now Send Method
"""
    )


@dp.message(AddMethodState.method)
async def receive_method(
    message: Message,
    state: FSMContext
):

    data = await state.get_data()

    service = data["service"]
    country = data["country"]

    method_text = message.text

    await add_pending(
        message.from_user.id,
        service,
        country,
        method_text
    )

    await state.clear()

    await message.answer(
        f"""
✅ Method Submitted

📲 Service: {service}
🌍 Country: {country}

⏳ Waiting For Admin Approval

After Approval All Users Can View Your Method.
"""
      )
from config import ADMINS


@dp.callback_query(F.data == "admin_panel")
async def admin_panel(call: CallbackQuery):

    if call.from_user.id not in ADMINS:
        await call.answer(
            "❌ Admin Only",
            show_alert=True
        )
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Pending Requests",
                    callback_data="pending_requests"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Statistics",
                    callback_data="statistics"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📢 Broadcast",
                    callback_data="broadcast"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏠 Main Menu",
                    callback_data="main_menu"
                )
            ]
        ]
    )

    await call.message.edit_text(
        """
👑 ADMIN PANEL

Select An Option
""",
        reply_markup=keyboard
    )


@dp.callback_query(F.data == "pending_requests")
async def pending_requests(call: CallbackQuery):

    if call.from_user.id not in ADMINS:
        return

    rows = await get_pending()

    if not rows:
        await call.message.edit_text(
            """
✅ No Pending Requests
"""
        )
        return

    for row in rows:

        pid = row[0]
        user_id = row[1]
        service = row[2]
        country = row[3]
        method = row[4]

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="✅ Approve",
                        callback_data=f"approve_{pid}"
                    ),
                    InlineKeyboardButton(
                        text="❌ Reject",
                        callback_data=f"reject_{pid}"
                    )
                ]
            ]
        )

        await call.message.answer(
            f"""
📋 Pending Method

👤 User: {user_id}

📲 Service: {service}
🌍 Country: {country}

📝 Method:

{method}
""",
            reply_markup=keyboard
        )


@dp.callback_query(F.data.startswith("approve_"))
async def approve_method(call: CallbackQuery):

    if call.from_user.id not in ADMINS:
        return

    pid = int(
        call.data.replace(
            "approve_",
            ""
        )
    )

    rows = await get_pending()

    for row in rows:

        if row[0] == pid:

            await add_method(
                row[2],
                row[3],
                row[4]
            )

            await delete_pending(pid)

            await call.message.edit_text(
                "✅ Approved Successfully"
            )

            return


@dp.callback_query(F.data.startswith("reject_"))
async def reject_method(call: CallbackQuery):

    if call.from_user.id not in ADMINS:
        return

    pid = int(
        call.data.replace(
            "reject_",
            ""
        )
    )

    await delete_pending(pid)

    await call.message.edit_text(
        "❌ Request Rejected"
    )


@dp.callback_query(F.data == "statistics")
async def statistics(call: CallbackQuery):

    if call.from_user.id not in ADMINS:
        return

    users = await total_users()

    await call.message.edit_text(
        f"""
📊 BOT STATISTICS

👥 Total Users:
{users}

🚀 Bot Running Fine
"""
    )


class BroadcastState(StatesGroup):
    text = State()


@dp.callback_query(F.data == "broadcast")
async def broadcast_menu(
    call: CallbackQuery,
    state: FSMContext
):

    if call.from_user.id not in ADMINS:
        return

    await state.set_state(
        BroadcastState.text
    )

    await call.message.answer(
        """
📢 Send Broadcast Message

All Users Will Receive It
"""
    )


@dp.message(BroadcastState.text)
async def do_broadcast(
    message: Message,
    state: FSMContext
):

    if message.from_user.id not in ADMINS:
        return

    text = message.text

    import aiosqlite

    sent = 0

    async with aiosqlite.connect(
        "users.db"
    ) as db:

        cursor = await db.execute(
            "SELECT user_id FROM users"
        )

        users = await cursor.fetchall()

        for user in users:

            try:

                await bot.send_message(
                    user[0],
                    text
                )

                sent += 1

            except:
                pass

    await state.clear()

    await message.answer(
        f"""
✅ Broadcast Completed

📨 Sent:
{sent}
"""
    )


async def main():

    await init_db()

    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
