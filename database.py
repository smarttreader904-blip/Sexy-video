import aiosqlite

DB_NAME = "bot.db"


async def create_db():
    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            full_name TEXT,
            username TEXT,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS countries(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT,
            country TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS methods(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT,
            country_id INTEGER,
            method_text TEXT,
            created_by INTEGER,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS pending_requests(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            platform TEXT,
            country TEXT,
            method_text TEXT,
            status TEXT DEFAULT 'pending'
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS support_messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            reply_to INTEGER,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS broadcast_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT,
            sent_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        await db.commit()


# =========================
# USERS
# =========================

async def add_user(user_id, full_name, username):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO users
            (user_id, full_name, username)
            VALUES (?, ?, ?)
            """,
            (user_id, full_name, username)
        )
        await db.commit()


async def get_all_users():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT user_id FROM users"
        )
        return await cursor.fetchall()


async def get_total_users():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM users"
        )
        return (await cursor.fetchone())[0]


# =========================
# COUNTRIES
# =========================

async def add_country(platform, country):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO countries
            (platform, country)
            VALUES (?, ?)
            """,
            (platform, country)
        )
        await db.commit()


async def get_countries(platform):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT id, country
            FROM countries
            WHERE platform=?
            ORDER BY country
            """,
            (platform,)
        )
        return await cursor.fetchall()


async def get_country(country_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT *
            FROM countries
            WHERE id=?
            """,
            (country_id,)
        )
        return await cursor.fetchone()


async def edit_country(country_id, new_name):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            UPDATE countries
            SET country=?
            WHERE id=?
            """,
            (new_name, country_id)
        )
        await db.commit()


async def delete_country(country_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM countries WHERE id=?",
            (country_id,)
        )

        await db.execute(
            "DELETE FROM methods WHERE country_id=?",
            (country_id,)
        )

        await db.commit()


async def get_total_countries():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM countries"
        )
        return (await cursor.fetchone())[0]


# =========================
# METHODS
# =========================

async def add_method(
        platform,
        country_id,
        method_text,
        created_by
):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO methods
            (
            platform,
            country_id,
            method_text,
            created_by
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                platform,
                country_id,
                method_text,
                created_by
            )
        )
        await db.commit()


async def get_methods(country_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT id, method_text
            FROM methods
            WHERE country_id=?
            ORDER BY id DESC
            """,
            (country_id,)
        )
        return await cursor.fetchall()


async def get_method(method_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT *
            FROM methods
            WHERE id=?
            """,
            (method_id,)
        )
        return await cursor.fetchone()
      # =========================
# METHODS (CONTINUE)
# =========================

async def edit_method(method_id, new_method):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            UPDATE methods
            SET method_text=?
            WHERE id=?
            """,
            (new_method, method_id)
        )
        await db.commit()


async def delete_method(method_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            DELETE FROM methods
            WHERE id=?
            """,
            (method_id,)
        )
        await db.commit()


async def get_total_methods():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM methods"
        )
        return (await cursor.fetchone())[0]


# =========================
# PENDING REQUESTS
# =========================

async def add_pending_request(
        user_id,
        platform,
        country,
        method_text
):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO pending_requests
            (
            user_id,
            platform,
            country,
            method_text
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                platform,
                country,
                method_text
            )
        )
        await db.commit()


async def get_pending_requests():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT *
            FROM pending_requests
            WHERE status='pending'
            ORDER BY id DESC
            """
        )
        return await cursor.fetchall()


async def get_pending_request(request_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT *
            FROM pending_requests
            WHERE id=?
            """,
            (request_id,)
        )
        return await cursor.fetchone()


async def approve_request(request_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            UPDATE pending_requests
            SET status='approved'
            WHERE id=?
            """,
            (request_id,)
        )
        await db.commit()


async def reject_request(request_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            UPDATE pending_requests
            SET status='rejected'
            WHERE id=?
            """,
            (request_id,)
        )
        await db.commit()


async def delete_pending_request(request_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            DELETE FROM pending_requests
            WHERE id=?
            """,
            (request_id,)
        )
        await db.commit()


async def get_total_pending():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT COUNT(*)
            FROM pending_requests
            WHERE status='pending'
            """
        )
        return (await cursor.fetchone())[0]


# =========================
# SUPPORT SYSTEM
# =========================

async def add_support_message(
        user_id,
        message,
        reply_to=None
):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO support_messages
            (
            user_id,
            message,
            reply_to
            )
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                message,
                reply_to
            )
        )
        await db.commit()


async def get_support_message(msg_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT *
            FROM support_messages
            WHERE id=?
            """,
            (msg_id,)
        )
        return await cursor.fetchone()


async def get_user_support_history(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT *
            FROM support_messages
            WHERE user_id=?
            ORDER BY id DESC
            """,
            (user_id,)
        )
        return await cursor.fetchall()


# =========================
# BROADCAST HISTORY
# =========================

async def add_broadcast_history(message):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO broadcast_history
            (message)
            VALUES (?)
            """,
            (message,)
        )
        await db.commit()


async def get_broadcast_history():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT *
            FROM broadcast_history
            ORDER BY id DESC
            """
        )
        return await cursor.fetchall()


# =========================
# STATISTICS
# =========================

async def get_statistics():
    users = await get_total_users()
    countries = await get_total_countries()
    methods = await get_total_methods()
    pending = await get_total_pending()

    return {
        "users": users,
        "countries": countries,
        "methods": methods,
        "pending": pending
    }


# =========================
# COUNTRY HELPERS
# =========================

async def find_country(platform, country):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            SELECT *
            FROM countries
            WHERE platform=? AND country=?
            """,
            (
                platform,
                country
            )
        )
        return await cursor.fetchone()


async def create_country_if_not_exists(
        platform,
        country
):
    existing = await find_country(
        platform,
        country
    )

    if existing:
        return existing[0]

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            """
            INSERT INTO countries
            (platform, country)
            VALUES (?, ?)
            """,
            (
                platform,
                country
            )
        )

        await db.commit()

        return cursor.lastrowid
      
