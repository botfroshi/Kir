# -*- coding: utf-8 -*-
"""
تمام توابع مربوط به دیتابیس (SQLite) در این فایل قرار دارند.
"""

import sqlite3
import time
import random
from datetime import date
from config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _migrate_add_column(cur, conn, table, column_def):
    """اضافه کردن ستون جدید به جدول موجود در صورت عدم وجود (بدون خطا در دیتابیس‌های قدیمی)."""
    col_name = column_def.split()[0]
    try:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
        conn.commit()
    except sqlite3.OperationalError:
        pass


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            balance INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL,
            referred_by INTEGER,
            total_spent INTEGER NOT NULL DEFAULT 0
        )
    """)
    _migrate_add_column(cur, conn, "users", "referred_by INTEGER")
    _migrate_add_column(cur, conn, "users", "total_spent INTEGER NOT NULL DEFAULT 0")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            is_special INTEGER NOT NULL DEFAULT 0
        )
    """)
    _migrate_add_column(cur, conn, "categories", "is_special INTEGER NOT NULL DEFAULT 0")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            price INTEGER NOT NULL DEFAULT 0,
            stock_status TEXT NOT NULL DEFAULT 'unavailable',
            FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS notify_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            username TEXT,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            created_at INTEGER NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS charge_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            username TEXT,
            amount INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at INTEGER NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price INTEGER NOT NULL,
            created_at INTEGER NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            amount INTEGER NOT NULL,
            description TEXT DEFAULT '',
            created_at INTEGER NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS coupons (
            code TEXT PRIMARY KEY,
            amount INTEGER NOT NULL,
            max_uses INTEGER NOT NULL DEFAULT 1,
            used_count INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at INTEGER NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS coupon_redemptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            telegram_id INTEGER NOT NULL,
            created_at INTEGER NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS spins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            spin_date TEXT NOT NULL,
            prize_amount INTEGER NOT NULL,
            created_at INTEGER NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def get_or_create_user(telegram_id, username, referred_by=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cur.fetchone()
    if row is None:
        safe_ref = referred_by if (referred_by and referred_by != telegram_id) else None
        cur.execute(
            "INSERT INTO users (telegram_id, username, balance, created_at, referred_by, total_spent) "
            "VALUES (?, ?, 0, ?, ?, 0)",
            (telegram_id, username or "", int(time.time()), safe_ref),
        )
        conn.commit()
        cur.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = cur.fetchone()
    else:
        if (row["username"] or "") != (username or ""):
            cur.execute(
                "UPDATE users SET username = ? WHERE telegram_id = ?",
                (username or "", telegram_id),
            )
            conn.commit()
    conn.close()
    return dict(row)


def get_user(telegram_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_users():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_balance(telegram_id, delta):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET balance = balance + ? WHERE telegram_id = ?",
        (delta, telegram_id),
    )
    conn.commit()
    conn.close()


def set_balance(telegram_id, new_balance):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET balance = ? WHERE telegram_id = ?",
        (new_balance, telegram_id),
    )
    conn.commit()
    conn.close()


def add_total_spent(telegram_id, amount):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET total_spent = total_spent + ? WHERE telegram_id = ?",
        (amount, telegram_id),
    )
    conn.commit()
    conn.close()


def count_orders(telegram_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM orders WHERE telegram_id = ?", (telegram_id,))
    c = cur.fetchone()["c"]
    conn.close()
    return c


def count_referrals(telegram_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM users WHERE referred_by = ?", (telegram_id,))
    c = cur.fetchone()["c"]
    conn.close()
    return c


def get_badge(total_spent):
    """بر اساس مجموع خرید، نشان کاربر را برمی‌گرداند."""
    if total_spent >= 2_000_000:
        return "🥇 طلایی"
    if total_spent >= 500_000:
        return "🥈 نقره‌ای"
    return "🥉 برنزی"


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

def add_category(name, is_special=0):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO categories (name, is_special) VALUES (?, ?)", (name, int(is_special)))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def get_categories():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM categories ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_category(category_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_category(category_id, name):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE categories SET name = ? WHERE id = ?", (name, category_id))
    conn.commit()
    conn.close()


def set_category_special(category_id, is_special):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE categories SET is_special = ? WHERE id = ?", (int(is_special), category_id))
    conn.commit()
    conn.close()


def delete_category(category_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE category_id = ?", (category_id,))
    cur.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

def add_product(category_id, name, description, price, stock_status="unavailable"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO products (category_id, name, description, price, stock_status) VALUES (?, ?, ?, ?, ?)",
        (category_id, name, description, price, stock_status),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def get_products_by_category(category_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE category_id = ? ORDER BY id DESC", (category_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_products():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_products(query, limit=15):
    conn = get_conn()
    cur = conn.cursor()
    like = f"%{query}%"
    cur.execute(
        "SELECT * FROM products WHERE name LIKE ? OR description LIKE ? ORDER BY id DESC LIMIT ?",
        (like, like, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_product(product_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_product_field(product_id, field, value):
    assert field in ("name", "description", "price", "stock_status")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"UPDATE products SET {field} = ? WHERE id = ?", (value, product_id))
    conn.commit()
    conn.close()


def delete_product(product_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id = ?", (product_id,))
    cur.execute("DELETE FROM notify_requests WHERE product_id = ?", (product_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Notify requests (اطلاع بده وقتی موجود شد)
# ---------------------------------------------------------------------------

def add_notify_request(telegram_id, product_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM notify_requests WHERE telegram_id = ? AND product_id = ?",
        (telegram_id, product_id),
    )
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO notify_requests (telegram_id, product_id) VALUES (?, ?)",
            (telegram_id, product_id),
        )
        conn.commit()
    conn.close()


def get_notify_requests_for_product(product_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM notify_requests WHERE product_id = ?", (product_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def clear_notify_requests_for_product(product_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM notify_requests WHERE product_id = ?", (product_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Settings (key/value) - شماره کارت، آیدی پشتیبانی، عضویت اجباری و ...
# ---------------------------------------------------------------------------

def set_setting(key, value):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()
    conn.close()


def get_setting(key, default=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return row["value"] if row else default


# ---------------------------------------------------------------------------
# Tickets (تیکت پشتیبانی)
# ---------------------------------------------------------------------------

def create_ticket(telegram_id, username, message):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tickets (telegram_id, username, message, status, created_at) VALUES (?, ?, ?, 'open', ?)",
        (telegram_id, username or "", message, int(time.time())),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def get_ticket(ticket_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Charge requests (شارژ کیف پول)
# ---------------------------------------------------------------------------

def create_charge_request(telegram_id, username, amount):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO charge_requests (telegram_id, username, amount, status, created_at) VALUES (?, ?, ?, 'pending', ?)",
        (telegram_id, username or "", amount, int(time.time())),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def get_charge_request(request_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM charge_requests WHERE id = ?", (request_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_charge_request_status(request_id, status):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE charge_requests SET status = ? WHERE id = ?", (status, request_id))
    conn.commit()
    conn.close()


def get_pending_charge_requests():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM charge_requests WHERE status = 'pending' ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Orders (خریدها)
# ---------------------------------------------------------------------------

def create_order(telegram_id, product_id, product_name, price):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO orders (telegram_id, product_id, product_name, price, created_at) VALUES (?, ?, ?, ?, ?)",
        (telegram_id, product_id, product_name, price, int(time.time())),
    )
    conn.commit()
    conn.close()


def get_sales_stats():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS cnt, COALESCE(SUM(price), 0) AS total FROM orders")
    overall = cur.fetchone()

    today_start = int(time.mktime(date.today().timetuple()))
    cur.execute(
        "SELECT COUNT(*) AS cnt, COALESCE(SUM(price), 0) AS total FROM orders WHERE created_at >= ?",
        (today_start,),
    )
    today = cur.fetchone()

    cur.execute(
        "SELECT product_name, COUNT(*) AS cnt, COALESCE(SUM(price), 0) AS total "
        "FROM orders GROUP BY product_name ORDER BY cnt DESC LIMIT 5"
    )
    top_products = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {
        "total_orders": overall["cnt"],
        "total_revenue": overall["total"],
        "today_orders": today["cnt"],
        "today_revenue": today["total"],
        "top_products": top_products,
    }


# ---------------------------------------------------------------------------
# Transactions (تاریخچه تراکنش‌های کیف پول)
# ---------------------------------------------------------------------------

def add_transaction(telegram_id, ttype, amount, description=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO transactions (telegram_id, type, amount, description, created_at) VALUES (?, ?, ?, ?, ?)",
        (telegram_id, ttype, amount, description, int(time.time())),
    )
    conn.commit()
    conn.close()


def get_transactions(telegram_id, limit=10):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM transactions WHERE telegram_id = ? ORDER BY id DESC LIMIT ?",
        (telegram_id, limit),
    )
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Coupons (کد تخفیف / شارژ هدیه)
# ---------------------------------------------------------------------------

def create_coupon(code, amount, max_uses=1):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO coupons (code, amount, max_uses, used_count, is_active, created_at) "
        "VALUES (?, ?, ?, 0, 1, ?)",
        (code.upper().strip(), amount, max_uses, int(time.time())),
    )
    conn.commit()
    conn.close()


def get_coupon(code):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM coupons WHERE code = ?", (code.upper().strip(),))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_coupons():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM coupons ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_coupon(code):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM coupons WHERE code = ?", (code.upper().strip(),))
    conn.commit()
    conn.close()


def redeem_coupon(code, telegram_id):
    """تلاش برای استفاده از کد تخفیف. خروجی: (موفق؟, پیام یا مبلغ)."""
    code = code.upper().strip()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM coupons WHERE code = ?", (code,))
    coupon = cur.fetchone()
    if not coupon:
        conn.close()
        return False, "کد تخفیف نامعتبر است."
    if not coupon["is_active"] or coupon["used_count"] >= coupon["max_uses"]:
        conn.close()
        return False, "این کد تخفیف منقضی شده یا به سقف استفاده رسیده است."
    cur.execute(
        "SELECT id FROM coupon_redemptions WHERE code = ? AND telegram_id = ?",
        (code, telegram_id),
    )
    if cur.fetchone():
        conn.close()
        return False, "شما قبلاً از این کد استفاده کرده‌اید."

    cur.execute(
        "INSERT INTO coupon_redemptions (code, telegram_id, created_at) VALUES (?, ?, ?)",
        (code, telegram_id, int(time.time())),
    )
    cur.execute("UPDATE coupons SET used_count = used_count + 1 WHERE code = ?", (code,))
    cur.execute("UPDATE users SET balance = balance + ? WHERE telegram_id = ?", (coupon["amount"], telegram_id))
    conn.commit()
    amount = coupon["amount"]
    conn.close()
    return True, amount


# ---------------------------------------------------------------------------
# Spin (چرخ شانس روزانه)
# ---------------------------------------------------------------------------

SPIN_PRIZES = [0, 0, 5000, 5000, 10000, 10000, 20000, 50000]


def can_spin_today(telegram_id):
    today_str = date.today().isoformat()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM spins WHERE telegram_id = ? AND spin_date = ?",
        (telegram_id, today_str),
    )
    row = cur.fetchone()
    conn.close()
    return row is None


def do_spin(telegram_id):
    today_str = date.today().isoformat()
    prize = random.choice(SPIN_PRIZES)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO spins (telegram_id, spin_date, prize_amount, created_at) VALUES (?, ?, ?, ?)",
        (telegram_id, today_str, prize, int(time.time())),
    )
    if prize > 0:
        cur.execute("UPDATE users SET balance = balance + ? WHERE telegram_id = ?", (prize, telegram_id))
    conn.commit()
    conn.close()
    return prize
