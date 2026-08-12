# -*- coding: utf-8 -*-
"""
ساخت کیبوردهای شیشه‌ای (Inline) و معمولی ربات.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

import db


# ---------------------------------------------------------------------------
# کاربر عادی
# ---------------------------------------------------------------------------

def user_main_menu(is_admin=False):
    keyboard = [
        [InlineKeyboardButton("🛍 محصولات", callback_data="menu_products")],
        [InlineKeyboardButton("👤 حساب من", callback_data="menu_account"),
         InlineKeyboardButton("💰 کیف پول من", callback_data="menu_wallet")],
        [InlineKeyboardButton("🎫 پشتیبانی / تیکت", callback_data="menu_ticket")],
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton("⚙️ پنل ادمین", callback_data="admin_home")])
    return InlineKeyboardMarkup(keyboard)


def back_button(callback_data):
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data=callback_data)]])


def categories_keyboard(prefix="cat"):
    cats = db.get_categories()
    rows = []
    for c in cats:
        rows.append([InlineKeyboardButton(c["name"], callback_data=f"{prefix}_{c['id']}")])
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")])
    return InlineKeyboardMarkup(rows)


def products_keyboard(category_id, prefix="prod"):
    products = db.get_products_by_category(category_id)
    rows = []
    for p in products:
        icon = "✅" if p["stock_status"] == "available" else "❌"
        rows.append([InlineKeyboardButton(f"{icon} {p['name']}", callback_data=f"{prefix}_{p['id']}")])
    rows.append([InlineKeyboardButton("🔙 بازگشت به دسته‌ها", callback_data="menu_products")])
    return InlineKeyboardMarkup(rows)


def product_detail_keyboard(product):
    rows = []
    if product["stock_status"] == "available":
        rows.append([InlineKeyboardButton("🛒 خرید", callback_data=f"buy_{product['id']}")])
    else:
        rows.append([InlineKeyboardButton("🔔 اطلاع بده وقتی موجود شد", callback_data=f"notify_{product['id']}")])
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"cat_{product['category_id']}")])
    return InlineKeyboardMarkup(rows)


def wallet_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ شارژ کیف پول", callback_data="wallet_charge")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")],
    ])


def confirm_charge_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ پرداخت کردم", callback_data="wallet_paid")],
        [InlineKeyboardButton("❌ انصراف", callback_data="back_main")],
    ])


def join_channel_keyboard(link):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 عضویت در کانال", url=link)],
        [InlineKeyboardButton("✅ عضو شدم", callback_data="check_join")],
    ])


# ---------------------------------------------------------------------------
# ادمین
# ---------------------------------------------------------------------------

def admin_main_menu():
    keyboard = [
        [InlineKeyboardButton("📦 مدیریت محصولات", callback_data="admin_products")],
        [InlineKeyboardButton("🗂 مدیریت دسته‌ها", callback_data="admin_categories")],
        [InlineKeyboardButton("👥 کاربران و آمار", callback_data="admin_users")],
        [InlineKeyboardButton("💳 تنظیم شماره کارت", callback_data="admin_card")],
        [InlineKeyboardButton("🎧 تنظیم آیدی پشتیبانی", callback_data="admin_support")],
        [InlineKeyboardButton("🔒 عضویت اجباری", callback_data="admin_forcejoin")],
        [InlineKeyboardButton("💰 درخواست‌های شارژ کیف پول", callback_data="admin_charges")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_main")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_categories_menu():
    cats = db.get_categories()
    rows = [[InlineKeyboardButton("➕ افزودن دسته", callback_data="admin_addcat")]]
    for c in cats:
        rows.append([
            InlineKeyboardButton(f"✏️ {c['name']}", callback_data=f"admin_editcat_{c['id']}"),
            InlineKeyboardButton("🗑", callback_data=f"admin_delcat_{c['id']}"),
        ])
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_home")])
    return InlineKeyboardMarkup(rows)


def admin_edit_category_keyboard(category_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ ویرایش نام", callback_data=f"admin_setcat_{category_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_categories")],
    ])


def admin_products_categories_keyboard():
    cats = db.get_categories()
    rows = []
    for c in cats:
        rows.append([InlineKeyboardButton(c["name"], callback_data=f"admin_prodcat_{c['id']}")])
    if not cats:
        rows.append([InlineKeyboardButton("⚠️ ابتدا یک دسته اضافه کنید", callback_data="admin_categories")])
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_home")])
    return InlineKeyboardMarkup(rows)


def admin_products_list_keyboard(category_id):
    products = db.get_products_by_category(category_id)
    rows = [[InlineKeyboardButton("➕ افزودن محصول", callback_data=f"admin_addprod_{category_id}")]]
    for p in products:
        icon = "✅" if p["stock_status"] == "available" else "❌"
        rows.append([InlineKeyboardButton(f"{icon} {p['name']}", callback_data=f"admin_prod_{p['id']}")])
    rows.append([InlineKeyboardButton("🔙 بازگشت به دسته‌ها", callback_data="admin_products")])
    return InlineKeyboardMarkup(rows)


def admin_product_manage_keyboard(product):
    stock_toggle_text = "❌ تنظیم ناموجود" if product["stock_status"] == "available" else "✅ تنظیم موجود"
    stock_toggle_data = f"admin_stockoff_{product['id']}" if product["stock_status"] == "available" else f"admin_stockon_{product['id']}"
    rows = [
        [InlineKeyboardButton("✏️ ویرایش نام", callback_data=f"admin_editname_{product['id']}")],
        [InlineKeyboardButton("📝 ویرایش توضیحات", callback_data=f"admin_editdesc_{product['id']}")],
        [InlineKeyboardButton("💵 ویرایش قیمت", callback_data=f"admin_editprice_{product['id']}")],
        [InlineKeyboardButton(stock_toggle_text, callback_data=stock_toggle_data)],
        [InlineKeyboardButton("🗑 حذف محصول", callback_data=f"admin_delprod_{product['id']}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"admin_prodcat_{product['category_id']}")],
    ]
    return InlineKeyboardMarkup(rows)


def admin_users_list_keyboard(users, page=0, per_page=10):
    start = page * per_page
    chunk = users[start:start + per_page]
    rows = []
    for u in chunk:
        uname = f"@{u['username']}" if u["username"] else "بدون‌یوزرنیم"
        rows.append([InlineKeyboardButton(
            f"{uname} | {u['telegram_id']} | موجودی: {u['balance']:,}",
            callback_data=f"admin_user_{u['telegram_id']}"
        )])
    nav = []
    if start > 0:
        nav.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"admin_users_page_{page-1}"))
    if start + per_page < len(users):
        nav.append(InlineKeyboardButton("➡️ بعدی", callback_data=f"admin_users_page_{page+1}"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_home")])
    return InlineKeyboardMarkup(rows)


def admin_user_manage_keyboard(telegram_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ ویرایش موجودی کیف پول", callback_data=f"admin_setbalance_{telegram_id}")],
        [InlineKeyboardButton("🔙 بازگشت به لیست کاربران", callback_data="admin_users")],
    ])


def admin_charge_request_keyboard(request_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تایید", callback_data=f"admin_chargeok_{request_id}"),
            InlineKeyboardButton("❌ رد", callback_data=f"admin_chargeno_{request_id}"),
        ]
    ])


def admin_forcejoin_keyboard():
    from config import DB_PATH  # noqa
    enabled = db.get_setting("force_join_enabled", "0") == "1"
    toggle_text = "🔴 غیرفعال کردن عضویت اجباری" if enabled else "🟢 فعال کردن عضویت اجباری"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 تنظیم لینک/آیدی کانال", callback_data="admin_setforcejoin")],
        [InlineKeyboardButton(toggle_text, callback_data="admin_toggleforcejoin")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_home")],
    ])
