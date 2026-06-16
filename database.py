import aiosqlite

DB_NAME = "users.db"


# ================= INIT DB =================
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:

        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS methods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT,
            country TEXT,
            method TEXT
        )
        """)

        await db.execute("""
        CREATE TABLE IF NOT EXISTS pending_methods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service TEXT,
            country TEXT,
            method TEXT
        )
        """)

        await db.commit()


# ================= USERS =================
async def add_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users(user_id) VALUES(?)",
            (user_id,)
        )
        await db.commit()


async def total_users():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        return (await cursor.fetchone())[0]


# ================= METHODS =================
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


# ================= PENDING METHODS =================
async def add_pending(user_id, service, country, method):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            """
            INSERT INTO pending_methods(user_id,service,country,method)
            VALUES(?,?,?,?)
            """,
            (user_id, service, country, method)
        )
        await db.commit()


async def get_pending():
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM pending_methods")
        return await cursor.fetchall()


async def delete_pending(pid: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM pending_methods WHERE id=?",
            (pid,)
        )
        await db.commit()
