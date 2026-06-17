import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import (
    State,
    StatesGroup
)

from config import *
from keyboards import *
from database import *

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# =========================
# FSM STATES
# =========================

class AddMethodState(StatesGroup):
    platform = State()
    country = State()
    custom_country = State()
    method = State()


class SupportState(StatesGroup):
    waiting_message = State()


class BroadcastState(StatesGroup):
    waiting_message = State()


class RejectState(StatesGroup):
    waiting_reason = State()


class ReplyState(StatesGroup):
    waiting_reply = State()


class EditCountryState(StatesGroup):
    waiting_name = State()


class EditMethodState(StatesGroup):
    waiting_method = State()


# =========================
# START
# =========================

@dp.message(CommandStart())
async def start_cmd(message: Message):

    await add_user(
        message.from_user.id,
        message.from_user.full_name,
        message.from_user.username
    )

    await message.answer(
        START_TEXT,
        reply_markup=start_menu()
    )


# =========================
# BACK HOME
# =========================

@dp.callback_query(F.data == "back_home")
async def back_home(call: CallbackQuery):

    await call.message.edit_text(
        START_TEXT,
        reply_markup=start_menu()
    )

    await call.answer()


# =========================
# MENU BUILDER
# =========================

@dp.callback_query(F.data == "menu_builder")
async def menu_builder_handler(call: CallbackQuery):

    is_admin = call.from_user.id in ADMINS

    await call.message.edit_text(
        "📂 Menu Builder",
        reply_markup=menu_builder_keyboard(
            is_admin
        )
    )

    await call.answer()


# =========================
# ADMIN PANEL
# =========================

@dp.callback_query(F.data == "admin_panel")
async def admin_panel(call: CallbackQuery):

    if call.from_user.id not in ADMINS:
        return await call.answer(
            "Access Denied",
            show_alert=True
        )

    await call.message.edit_text(
        "👑 Admin Panel",
        reply_markup=admin_panel_keyboard()
    )

    await call.answer()


# =========================
# STATISTICS
# =========================

@dp.callback_query(F.data == "statistics")
async def statistics_handler(
        call: CallbackQuery
):

    if call.from_user.id not in ADMINS:
        return

    stats = await get_statistics()

    text = (
        f"📊 Statistics\n\n"
        f"👤 Total Users: {stats['users']}\n"
        f"🌍 Total Countries: {stats['countries']}\n"
        f"📄 Total Methods: {stats['methods']}\n"
        f"📥 Pending Requests: {stats['pending']}"
    )

    await call.message.edit_text(
        text,
        reply_markup=admin_panel_keyboard()
    )

    await call.answer()


# =========================
# PLATFORM VIEW
# =========================

@dp.callback_query(
    F.data.startswith("platform_")
)
async def platform_view(
        call: CallbackQuery
):

    platform = call.data.split("_")[1]

    countries = await get_countries(
        platform
    )

    if not countries:

        await call.message.edit_text(
            f"❌ No country found for {platform}",
            reply_markup=back_keyboard()
        )

        return

    await call.message.edit_text(
        f"🌍 {platform} Countries",
        reply_markup=
        countries_list_keyboard(
            countries
        )
    )

    await call.answer()


# =========================
# ADD METHOD BUTTON
# =========================

@dp.callback_query(
    F.data == "add_method"
)
async def add_method_button(
        call: CallbackQuery
):

    await call.message.edit_text(
        ADD_METHOD_TEXT,
        reply_markup=platform_keyboard()
    )

    await call.answer()
  # =========================
# ADD METHOD - PLATFORM
# =========================

@dp.callback_query(
    F.data.startswith("addplatform_")
)
async def select_platform(
        call: CallbackQuery,
        state: FSMContext
):

    platform = call.data.replace(
        "addplatform_",
        ""
    )

    await state.update_data(
        platform=platform
    )

    await state.set_state(
        AddMethodState.country
    )

    await call.message.edit_text(
        SELECT_COUNTRY_TEXT,
        reply_markup=country_keyboard()
    )

    await call.answer()


# =========================
# COUNTRY SELECT
# =========================

@dp.callback_query(
    F.data.startswith("country_")
)
async def select_country(
        call: CallbackQuery,
        state: FSMContext
):

    country = call.data.replace(
        "country_",
        ""
    )

    if country == "Others":

        await state.set_state(
            AddMethodState.custom_country
        )

        await call.message.edit_text(
            CUSTOM_COUNTRY_TEXT
        )

        return

    await state.update_data(
        country=country
    )

    await state.set_state(
        AddMethodState.method
    )

    await call.message.edit_text(
        SEND_METHOD_TEXT
    )

    await call.answer()


# =========================
# CUSTOM COUNTRY
# =========================

@dp.message(
    AddMethodState.custom_country
)
async def custom_country_handler(
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
        SEND_METHOD_TEXT
    )


# =========================
# METHOD SUBMIT
# =========================

@dp.message(
    AddMethodState.method
)
async def submit_method(
        message: Message,
        state: FSMContext
):

    data = await state.get_data()

    platform = data["platform"]
    country = data["country"]
    method_text = message.text

    user_id = message.from_user.id

    # =====================
    # ADMIN DIRECT ADD
    # =====================

    if user_id in ADMINS:

        country_id = (
            await create_country_if_not_exists(
                platform,
                country
            )
        )

        await add_method(
            platform,
            country_id,
            method_text,
            user_id
        )

        await message.answer(
            "✅ Method Added Successfully."
        )

        # notify all users

        users = await get_all_users()

        for user in users:

            try:
                await bot.send_message(
                    user[0],
                    NEW_METHOD_NOTIFICATION
                )
            except:
                pass

        await state.clear()

        return

    # =====================
    # USER REQUEST
    # =====================

    await add_pending_request(
        user_id,
        platform,
        country,
        method_text
    )

    await message.answer(
        "✅ Method request submitted.\n\nWaiting for admin approval."
    )

    # send to admins

    pending = await get_pending_requests()

    request_id = pending[0][0]

    admin_text = (
        f"🆕 New Method Request\n\n"
        f"📱 Platform: {platform}\n"
        f"🌍 Country: {country}\n\n"
        f"📄 Method:\n"
        f"{method_text}\n\n"
        f"👤 User: {message.from_user.full_name}\n"
        f"🔗 Username: @{message.from_user.username}\n"
        f"🆔 Chat ID: {user_id}"
    )

    for admin in ADMINS:

        try:
            await bot.send_message(
                admin,
                admin_text,
                reply_markup=
                approval_keyboard(
                    request_id
                )
            )
        except:
            pass

    await state.clear()


# =========================
# PENDING REQUESTS
# =========================

@dp.callback_query(
    F.data == "pending_requests"
)
async def pending_requests_handler(
        call: CallbackQuery
):

    if call.from_user.id not in ADMINS:
        return

    requests = (
        await get_pending_requests()
    )

    if not requests:

        await call.message.edit_text(
            "📭 No pending requests."
        )

        return

    for req in requests:

        request_id = req[0]
        user_id = req[1]
        platform = req[2]
        country = req[3]
        method_text = req[4]

        text = (
            f"🆕 Pending Request\n\n"
            f"📱 Platform: {platform}\n"
            f"🌍 Country: {country}\n\n"
            f"📄 Method:\n"
            f"{method_text}\n\n"
            f"🆔 User ID: {user_id}"
        )

        await call.message.answer(
            text,
            reply_markup=
            approval_keyboard(
                request_id
            )
        )

    await call.answer()


# =========================
# ACCEPT REQUEST
# =========================

@dp.callback_query(
    F.data.startswith("accept_")
)
async def accept_request(
        call: CallbackQuery
):

    if call.from_user.id not in ADMINS:
        return

    request_id = int(
        call.data.split("_")[1]
    )

    request = await get_pending_request(
        request_id
    )

    if not request:
        return

    user_id = request[1]
    platform = request[2]
    country = request[3]
    method_text = request[4]

    country_id = (
        await create_country_if_not_exists(
            platform,
            country
        )
    )

    await add_method(
        platform,
        country_id,
        method_text,
        user_id
    )

    await approve_request(
        request_id
    )

    await call.message.edit_text(
        "✅ Request Approved."
    )

    # notify submitter

    try:
        await bot.send_message(
            user_id,
            "✅ Your method has been approved."
        )
    except:
        pass

    # notify all users

    users = await get_all_users()

    for user in users:

        try:
            await bot.send_message(
                user[0],
                NEW_METHOD_NOTIFICATION
            )
        except:
            pass

    await call.answer()


# =========================
# REJECT REQUEST
# =========================

@dp.callback_query(
    F.data.startswith("reject_")
)
async def reject_request_handler(
        call: CallbackQuery,
        state: FSMContext
):

    if call.from_user.id not in ADMINS:
        return

    request_id = int(
        call.data.split("_")[1]
    )

    await state.update_data(
        request_id=request_id
    )

    await state.set_state(
        RejectState.waiting_reason
    )

    await call.message.answer(
        REJECT_REASON_TEXT
    )

    await call.answer()
  # =========================
# REJECT REASON COMPLETE
# =========================

@dp.message(
    RejectState.waiting_reason
)
async def reject_reason_complete(
        message: Message,
        state: FSMContext
):

    data = await state.get_data()

    request_id = data.get(
        "request_id"
    )

    request = await get_pending_request(
        request_id
    )

    if not request:

        await message.answer(
            "❌ Request not found."
        )

        await state.clear()
        return

    user_id = request[1]

    reason = message.text

    await reject_request(
        request_id
    )

    try:
        await bot.send_message(
            user_id,
            f"❌ Your method request was rejected.\n\n"
            f"Reason:\n{reason}"
        )
    except:
        pass

    await message.answer(
        "✅ Request rejected successfully."
    )

    await state.clear()


# =========================
# BROADCAST BUTTON
# =========================

@dp.callback_query(
    F.data == "broadcast"
)
async def broadcast_button(
        call: CallbackQuery,
        state: FSMContext
):

    if call.from_user.id not in ADMINS:
        return

    await state.set_state(
        BroadcastState.waiting_message
    )

    await call.message.answer(
        BROADCAST_TEXT
    )

    await call.answer()


# =========================
# BROADCAST SEND
# =========================

@dp.message(
    BroadcastState.waiting_message
)
async def broadcast_send(
        message: Message,
        state: FSMContext
):

    if message.from_user.id not in ADMINS:
        return

    text = message.text

    users = await get_all_users()

    sent = 0
    failed = 0

    for user in users:

        try:
            await bot.send_message(
                user[0],
                text
            )

            sent += 1

        except:
            failed += 1

    await add_broadcast_history(
        text
    )

    await message.answer(
        f"📢 Broadcast Completed\n\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {failed}"
    )

    await state.clear()


# =========================
# SUPPORT BUTTON
# =========================

@dp.callback_query(
    F.data == "support"
)
async def support_button(
        call: CallbackQuery,
        state: FSMContext
):

    await state.set_state(
        SupportState.waiting_message
    )

    await call.message.answer(
        SUPPORT_TEXT
    )

    await call.answer()


# =========================
# SUPPORT MESSAGE
# =========================

@dp.message(
    SupportState.waiting_message
)
async def support_message_handler(
        message: Message,
        state: FSMContext
):

    user_id = message.from_user.id

    text = message.text

    await add_support_message(
        user_id,
        text
    )

    admin_text = (
        f"📨 Support Request\n\n"
        f"👤 User: "
        f"{message.from_user.full_name}\n"
        f"🔗 Username: "
        f"@{message.from_user.username}\n"
        f"🆔 Chat ID: "
        f"{user_id}\n\n"
        f"💬 Message:\n"
        f"{text}"
    )

    for admin in ADMINS:

        try:
            await bot.send_message(
                admin,
                admin_text,
                reply_markup=
                support_reply_keyboard(
                    user_id
                )
            )
        except:
            pass

    await message.answer(
        "✅ Your message has been sent to support."
    )

    await state.clear()


# =========================
# ADMIN REPLY BUTTON
# =========================

@dp.callback_query(
    F.data.startswith("reply_")
)
async def admin_reply_button(
        call: CallbackQuery,
        state: FSMContext
):

    if call.from_user.id not in ADMINS:
        return

    user_id = int(
        call.data.split("_")[1]
    )

    await state.update_data(
        reply_user=user_id
    )

    await state.set_state(
        ReplyState.waiting_reply
    )

    await call.message.answer(
        REPLY_TEXT
    )

    await call.answer()


# =========================
# ADMIN SEND REPLY
# =========================

@dp.message(
    ReplyState.waiting_reply
)
async def admin_send_reply(
        message: Message,
        state: FSMContext
):

    if message.from_user.id not in ADMINS:
        return

    data = await state.get_data()

    user_id = data.get(
        "reply_user"
    )

    reply_text = message.text

    try:

        await bot.send_message(
            user_id,
            f"💬 Support Reply\n\n"
            f"{reply_text}",
            reply_markup=
            support_reply_keyboard(
                user_id
            )
        )

        await add_support_message(
            user_id,
            f"ADMIN: {reply_text}"
        )

        await message.answer(
            "✅ Reply sent."
        )

    except Exception as e:

        await message.answer(
            f"❌ Failed:\n{e}"
        )

    await state.clear()
  # =========================
# USER REPLY TO SUPPORT
# =========================

@dp.callback_query(
    F.data.startswith("reply_")
)
async def user_reply_button(
        call: CallbackQuery,
        state: FSMContext
):

    if call.from_user.id in ADMINS:
        return

    await state.set_state(
        SupportState.waiting_message
    )

    await call.message.answer(
        "💬 Please send your reply."
    )

    await call.answer()


# =========================
# VIEW COUNTRY METHODS
# =========================

@dp.callback_query(
    F.data.startswith("viewcountry_")
)
async def view_country_methods(
        call: CallbackQuery
):

    country_id = int(
        call.data.split("_")[1]
    )

    methods = await get_methods(
        country_id
    )

    country = await get_country(
        country_id
    )

    if not methods:

        await call.message.edit_text(
            "❌ No methods found.",
            reply_markup=
            back_keyboard()
        )

        return

    await call.message.answer(
        f"🌍 Country: {country[2]}"
    )

    for method in methods:

        method_id = method[0]
        method_text = method[1]

        if call.from_user.id in ADMINS:

            await call.message.answer(
                f"📄 Method ID: {method_id}\n\n"
                f"{method_text}",
                reply_markup=
                method_manage_keyboard(
                    method_id
                )
            )

        else:

            await call.message.answer(
                method_text
            )

    if call.from_user.id in ADMINS:

        await call.message.answer(
            "⚙ Country Management",
            reply_markup=
            country_manage_keyboard(
                country_id
            )
        )

    await call.answer()


# =========================
# EDIT COUNTRY
# =========================

@dp.callback_query(
    F.data.startswith(
        "editcountry_"
    )
)
async def edit_country_button(
        call: CallbackQuery,
        state: FSMContext
):

    if call.from_user.id not in ADMINS:
        return

    country_id = int(
        call.data.split("_")[1]
    )

    await state.update_data(
        country_id=country_id
    )

    await state.set_state(
        EditCountryState.waiting_name
    )

    await call.message.answer(
        "✏️ Send new country name."
    )

    await call.answer()


@dp.message(
    EditCountryState.waiting_name
)
async def save_country_edit(
        message: Message,
        state: FSMContext
):

    data = await state.get_data()

    country_id = data["country_id"]

    await edit_country(
        country_id,
        message.text
    )

    await message.answer(
        "✅ Country updated."
    )

    await state.clear()


# =========================
# DELETE COUNTRY
# =========================

@dp.callback_query(
    F.data.startswith(
        "deletecountry_"
    )
)
async def delete_country_handler(
        call: CallbackQuery
):

    if call.from_user.id not in ADMINS:
        return

    country_id = int(
        call.data.split("_")[1]
    )

    await delete_country(
        country_id
    )

    await call.message.edit_text(
        "✅ Country deleted."
    )

    await call.answer()


# =========================
# EDIT METHOD
# =========================

@dp.callback_query(
    F.data.startswith(
        "editmethod_"
    )
)
async def edit_method_button(
        call: CallbackQuery,
        state: FSMContext
):

    if call.from_user.id not in ADMINS:
        return

    method_id = int(
        call.data.split("_")[1]
    )

    await state.update_data(
        method_id=method_id
    )

    await state.set_state(
        EditMethodState.waiting_method
    )

    await call.message.answer(
        "✏️ Send new method."
    )

    await call.answer()


@dp.message(
    EditMethodState.waiting_method
)
async def save_method_edit(
        message: Message,
        state: FSMContext
):

    data = await state.get_data()

    method_id = data["method_id"]

    await edit_method(
        method_id,
        message.text
    )

    await message.answer(
        "✅ Method updated."
    )

    await state.clear()


# =========================
# DELETE METHOD
# =========================

@dp.callback_query(
    F.data.startswith(
        "deletemethod_"
    )
)
async def delete_method_handler(
        call: CallbackQuery
):

    if call.from_user.id not in ADMINS:
        return

    method_id = int(
        call.data.split("_")[1]
    )

    await delete_method(
        method_id
    )

    await call.message.edit_text(
        "✅ Method deleted."
    )

    await call.answer()


# =========================
# STARTUP
# =========================

async def on_startup():

    await create_db()

    print(
        "Database Ready"
    )


# =========================
# MAIN
# =========================

async def main():

    await on_startup()

    print(
        "Bot Started..."
    )

    await dp.start_polling(
        bot
    )


if __name__ == "__main__":
    asyncio.run(
        main()
  )
