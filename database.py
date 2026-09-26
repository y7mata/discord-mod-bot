import aiosqlite

DB_PATH = "bot.db"


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS guild_config (
                guild_id    INTEGER PRIMARY KEY,
                log_channel INTEGER,
                auto_role   INTEGER
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS button_roles (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id    INTEGER NOT NULL,
                message_id  INTEGER,
                role_id     INTEGER NOT NULL,
                label       TEXT    NOT NULL,
                emoji       TEXT,
                style       TEXT    DEFAULT 'primary'
            )
        """)
        await db.commit()


async def get_config(guild_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM guild_config WHERE guild_id = ?", (guild_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else {}


async def set_config(guild_id: int, **kwargs):
    async with aiosqlite.connect(DB_PATH) as db:
        existing = await (
            await db.execute(
                "SELECT 1 FROM guild_config WHERE guild_id = ?", (guild_id,)
            )
        ).fetchone()
        if existing:
            sets = ", ".join(f"{k} = ?" for k in kwargs)
            await db.execute(
                f"UPDATE guild_config SET {sets} WHERE guild_id = ?",
                (*kwargs.values(), guild_id),
            )
        else:
            cols = "guild_id, " + ", ".join(kwargs.keys())
            vals = ", ".join(["?"] * (len(kwargs) + 1))
            await db.execute(
                f"INSERT INTO guild_config ({cols}) VALUES ({vals})",
                (guild_id, *kwargs.values()),
            )
        await db.commit()


async def add_button_role(
    guild_id: int, role_id: int, label: str, emoji: str | None, style: str
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO button_roles (guild_id, role_id, label, emoji, style) "
            "VALUES (?, ?, ?, ?, ?)",
            (guild_id, role_id, label, emoji, style),
        )
        await db.commit()
        return cur.lastrowid


async def set_button_role_message(row_id: int, message_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE button_roles SET message_id = ? WHERE id = ?",
            (message_id, row_id),
        )
        await db.commit()


async def get_button_roles(guild_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM button_roles WHERE guild_id = ?", (guild_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def remove_button_role(row_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM button_roles WHERE id = ?", (row_id,))
        await db.commit()
