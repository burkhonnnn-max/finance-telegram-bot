import aiosqlite
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from config import DB_PATH


async def init_db():
    """Ma'lumotlar bazasini va jadvallarni yaratish"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                username TEXT,
                currency TEXT DEFAULT 'so''m',
                language TEXT DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Til ustunini tekshirish va qo'shish (migratsiya)
        try:
            await db.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT NULL")
            await db.commit()
        except Exception:
            pass

        await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL, -- 'income' (kirim) yoki 'expense' (chiqim)
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                comment TEXT,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)

        await db.execute("CREATE INDEX IF NOT EXISTS idx_user_trans ON transactions (user_id, created_at)")

        await db.execute("""
            CREATE TABLE IF NOT EXISTS sent_monthly_reports (
                year_month TEXT PRIMARY KEY,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                users_count INTEGER DEFAULT 0
            )
        """)
        await db.commit()


async def add_user(user_id: int, full_name: str, username: Optional[str] = None, language: Optional[str] = None):
    """Yangi foydalanuvchini bazaga qo'shish yoki yangilash"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, full_name, username, language)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                full_name = excluded.full_name,
                username = excluded.username,
                language = COALESCE(excluded.language, users.language)
        """, (user_id, full_name, username, language))
        await db.commit()


async def get_user_language(user_id: int) -> Optional[str]:
    """Foydalanuvchi tanlagan tilni olish ('uz' yoki 'ru')"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT language FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row and row[0]:
                return row[0]
            return None


async def set_user_language(user_id: int, language: str):
    """Foydalanuvchi tilini yangilash (agar foydalanuvchi yo'q bo'lsa yaratadi)"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (user_id, language)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET language = excluded.language
        """, (user_id, language))
        await db.commit()


async def add_transaction(
    user_id: int,
    tr_type: str,
    amount: float,
    category: str,
    comment: Optional[str] = None,
    created_at: Optional[datetime] = None
) -> int:
    """Yangi kirim yoki chiqim yozuvini qo'shish"""
    if created_at is None:
        from utils import get_tashkent_now
        created_at = get_tashkent_now()
    created_str = created_at.strftime("%Y-%m-%d %H:%M:%S")

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO transactions (user_id, type, amount, category, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, tr_type, amount, category, comment, created_str))
        await db.commit()
        return cursor.lastrowid


async def delete_transaction(transaction_id: int, user_id: int) -> bool:
    """Tranzaksiyani o'chirish (faqat o'ziga tegishlisini)"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            DELETE FROM transactions
            WHERE id = ? AND user_id = ?
        """, (transaction_id, user_id))
        await db.commit()
        return cursor.rowcount > 0


async def get_transaction(transaction_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Aynan bitta tranzaksiya ma'lumotini olish"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT id, type, amount, category, comment, created_at
            FROM transactions
            WHERE id = ? AND user_id = ?
        """, (transaction_id, user_id)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None


async def get_balance(user_id: int) -> Dict[str, float]:
    """Foydalanuvchining umumiy balansi va jami kirim/chiqimlari"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) as total_income,
                COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as total_expense
            FROM transactions
            WHERE user_id = ?
        """, (user_id,)) as cursor:
            row = await cursor.fetchone()
            income = row[0] if row else 0.0
            expense = row[1] if row else 0.0
            return {
                "income": income,
                "expense": expense,
                "balance": income - expense
            }


async def get_recent_transactions(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """Oxirgi tranzaksiyalar ro'yxati"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT id, type, amount, category, comment, created_at
            FROM transactions
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
        """, (user_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_stats_for_period(user_id: int, start_date: str, end_date: str) -> Dict[str, Any]:
    """Muayyan vaqt oralig'idagi umumiy statistika va toifalar bo'yicha taqsimot"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Umumiy kirim va chiqim
        async with db.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) as total_income,
                COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as total_expense
            FROM transactions
            WHERE user_id = ? AND created_at >= ? AND created_at <= ?
        """, (user_id, start_date, end_date)) as cursor:
            total_row = await cursor.fetchone()
            total_income = total_row[0] if total_row else 0.0
            total_expense = total_row[1] if total_row else 0.0

        # Chiqimlar toifalar bo'yicha
        categories_expense = []
        async with db.execute("""
            SELECT category, SUM(amount) as cat_total, COUNT(id) as count
            FROM transactions
            WHERE user_id = ? AND type = 'expense' AND created_at >= ? AND created_at <= ?
            GROUP BY category
            ORDER BY cat_total DESC
        """, (user_id, start_date, end_date)) as cursor:
            rows = await cursor.fetchall()
            for r in rows:
                percentage = (r["cat_total"] / total_expense * 100) if total_expense > 0 else 0
                categories_expense.append({
                    "category": r["category"],
                    "total": r["cat_total"],
                    "count": r["count"],
                    "percentage": round(percentage, 1)
                })

        # Kirimlar toifalar bo'yicha
        categories_income = []
        async with db.execute("""
            SELECT category, SUM(amount) as cat_total, COUNT(id) as count
            FROM transactions
            WHERE user_id = ? AND type = 'income' AND created_at >= ? AND created_at <= ?
            GROUP BY category
            ORDER BY cat_total DESC
        """, (user_id, start_date, end_date)) as cursor:
            rows = await cursor.fetchall()
            for r in rows:
                percentage = (r["cat_total"] / total_income * 100) if total_income > 0 else 0
                categories_income.append({
                    "category": r["category"],
                    "total": r["cat_total"],
                    "count": r["count"],
                    "percentage": round(percentage, 1)
                })

        return {
            "income": total_income,
            "expense": total_expense,
            "difference": total_income - total_expense,
            "categories_expense": categories_expense,
            "categories_income": categories_income
        }


async def get_all_users() -> List[Dict[str, Any]]:
    """Barcha faol foydalanuvchilar ro'yxatini olish"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT u.user_id, COALESCE(u.full_name, 'Foydalanuvchi') as full_name, u.language
            FROM users u
            UNION
            SELECT DISTINCT t.user_id, 'Foydalanuvchi' as full_name, 'uz' as language
            FROM transactions t
            WHERE t.user_id NOT IN (SELECT user_id FROM users)
        """) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def get_month_transactions(user_id: int, year: int, month: int) -> List[Dict[str, Any]]:
    """Muayyan oy uchun foydalanuvchining barcha tranzaksiyalari"""
    import calendar
    _, last_day = calendar.monthrange(year, month)
    start_date = f"{year}-{month:02d}-01 00:00:00"
    end_date = f"{year}-{month:02d}-{last_day:02d} 23:59:59"
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT id, type, amount, category, comment, created_at
            FROM transactions
            WHERE user_id = ? AND created_at >= ? AND created_at <= ?
            ORDER BY created_at ASC, id ASC
        """, (user_id, start_date, end_date)) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def is_monthly_report_sent(year_month: str) -> bool:
    """Muayyan oy hisoboti yuborilgan yoki yo'qligini tekshirish"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM sent_monthly_reports WHERE year_month = ?", (year_month,)
        ) as cursor:
            row = await cursor.fetchone()
            return bool(row)


async def mark_monthly_report_sent(year_month: str, users_count: int):
    """Oy hisoboti yuborilgan deb belgilash"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO sent_monthly_reports (year_month, users_count)
            VALUES (?, ?)
            ON CONFLICT(year_month) DO UPDATE SET
                sent_at = CURRENT_TIMESTAMP,
                users_count = excluded.users_count
        """, (year_month, users_count))
        await db.commit()
