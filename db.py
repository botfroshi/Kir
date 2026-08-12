# -*- coding: utf-8 -*-
"""
تمام توابع مربوط به دیتابیس (SQLite) در این فایل قرار دارند.
"""

import sqlite3
import time
from config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            balance INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)

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

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def get_or_create_user(telegram_id, username):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    row = cur.fetchone()
    if row is None:
        cur.execute(
            "INSERT INTO users (telegram_id, username, balance, created_at) VALUES (?, ?, 0, ?)",
            (telegram_id, username or "", int(time.time())),
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


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

def add_category(name):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO categories (name) VALUES (?)", (name,))
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
