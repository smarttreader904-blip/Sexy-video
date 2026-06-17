from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from config import DEFAULT_COUNTRIES


# =========================
# START MENU
# =========================

def start_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Telegram",
                    callback_data="platform_Telegram"
                ),
                InlineKeyboardButton(
                    text="WhatsApp",
                    callback_data="platform_WhatsApp"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Facebook",
                    callback_data="platform_Facebook"
                ),
                InlineKeyboardButton(
                    text="TikTok",
                    callback_data="platform_TikTok"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📂 Menu Builder",
                    callback_data="menu_builder"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🛠 Support",
                    callback_data="support"
                )
            ]
        ]
    )


# =========================
# MENU BUILDER
# =========================

def menu_builder_keyboard(is_admin=False):
    buttons = [
        [
            InlineKeyboardButton(
                text="➕ Add Method",
                callback_data="add_method"
            )
        ]
    ]

    if is_admin:
        buttons.append(
            [
                InlineKeyboardButton(
                    text="👑 Admin Panel",
                    callback_data="admin_panel"
                )
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


# =========================
# ADMIN PANEL
# =========================

def admin_panel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Statistics",
                    callback_data="statistics"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📥 Pending Requests",
                    callback_data="pending_requests"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📢 Broadcast",
                    callback_data="broadcast"
                )
            ]
        ]
    )


# =========================
# PLATFORM SELECT
# =========================

def platform_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Telegram",
                    callback_data="addplatform_Telegram"
                ),
                InlineKeyboardButton(
                    text="WhatsApp",
                    callback_data="addplatform_WhatsApp"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Facebook",
                    callback_data="addplatform_Facebook"
                ),
                InlineKeyboardButton(
                    text="TikTok",
                    callback_data="addplatform_TikTok"
                )
            ]
        ]
    )


# =========================
# COUNTRY SELECT
# =========================

def country_keyboard():
    rows = []

    for country in DEFAULT_COUNTRIES:
        rows.append(
            [
                InlineKeyboardButton(
                    text=country,
                    callback_data=f"country_{country}"
                )
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=rows
    )


# =========================
# DYNAMIC COUNTRY LIST
# =========================

def countries_list_keyboard(countries):
    rows = []

    for country_id, country_name in countries:
        rows.append(
            [
                InlineKeyboardButton(
                    text=country_name,
                    callback_data=f"viewcountry_{country_id}"
                )
            ]
        )

    return InlineKeyboardMarkup(
        inline_keyboard=rows
    )


# =========================
# METHOD MANAGEMENT
# =========================

def method_manage_keyboard(method_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Edit",
                    callback_data=f"editmethod_{method_id}"
                ),
                InlineKeyboardButton(
                    text="🗑 Delete",
                    callback_data=f"deletemethod_{method_id}"
                )
            ]
        ]
    )


# =========================
# COUNTRY MANAGEMENT
# =========================

def country_manage_keyboard(country_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✏️ Edit Country",
                    callback_data=f"editcountry_{country_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Delete Country",
                    callback_data=f"deletecountry_{country_id}"
                )
            ]
        ]
    )


# =========================
# ACCEPT / REJECT
# =========================

def approval_keyboard(request_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Accept",
                    callback_data=f"accept_{request_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Reject",
                    callback_data=f"reject_{request_id}"
                )
            ]
        ]
    )


# =========================
# SUPPORT REPLY
# =========================

def support_reply_keyboard(user_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Reply",
                    callback_data=f"reply_{user_id}"
                )
            ]
        ]
    )


# =========================
# BACK BUTTON
# =========================

def back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅ Back",
                    callback_data="back_home"
                )
            ]
        ]
    )
