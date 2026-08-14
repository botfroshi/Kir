# -*- coding: utf-8 -*-
"""
ساخت کیبوردهای شیشه‌ای (Inline) و معمولی ربات.

نکته: از نسخه Bot API 9.4 به بعد، تلگرام پارامتر style را برای
InlineKeyboardButton اضافه کرده که سه رنگ زیر را پشتیبانی می‌کند:
  - "primary" -> آبی   (برای اکشن‌های اصلی و پیمایش)
  - "success" -> سبز   (برای تایید / خرید / اکشن‌های مثبت)
  - "danger"  -> قرمز  (برای حذف / رد / اکشن‌های مخرب یا هشدار)
اگر style ست نشود، دکمه به همان حالت پیش‌فرض قبلی (خاکستری/شفاف) نمایش
داده می‌شود. کتابخانه python-telegram-bot==22.8 این پارامتر را پشتیبانی می‌کند.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

import db


# ---------------------------------------------------------------------------
# کاربر عادی
# ---------------------------------------------------------------------------

def user_main_menu(is_admin=False):
    keyboard = [
        [InlineKeyboardButton("🛍 محصولات", callback_data="menu_products", style="primary")],
        [InlineKeyboardButton("👤 حساب من", callback_data="menu_account", style="primary"),
         InlineKeyboardButton("💰 کیف پول من", callback_data="menu_wallet", style="primary")],
        [InlineKeyboardButton("🎡 چرخ شانس روزانه", callback_data="menu_spin", style="success"),
         InlineKeyboardButton("🤝 دعوت دوستان", callback_data="menu_referral", style="primary")],
        [InlineKeyboardButton("🎫 پشتیبانی / تیکت", callback_data="menu_ticket", style="primary")],
    ]
    if is_admin:
        keyboard.append([InlineKeyboardButton("⚙️ پنل ادمین", callback_data="admin_home", style="danger")])
    return InlineKeyboardMarkup(keyboard)


def back_button(callback_data):
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data=callback_data)]])


def categories_keyboard(prefix="cat"):
    cats = db.get_categories()
    rows = [[InlineKeyboardButton("🔍 جستجوی محصول", callback_data="menu_search", style="primary")]]
    for c in cats:
        label = f"⭐ {c['name']}" if c.get("is_special") else c["name"]
        style = "success" if c.get("is_special") else "primary"
        rows.append([InlineKeyboardButton(label, callback_data=f"{prefix}_{c['id']}", style=style)])
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")])
    return InlineKeyboardMarkup(rows)


def products_keyboard(category_id, prefix="prod"):
    products = db.get_products_by_category(category_id)
    rows = []
    for p in products:
        icon = "✅" if p["stock_status"] == "available" else "❌"
        style = "success" if p["stock_status"] == "available" else "danger"
        rows.append([InlineKeyboardButton(f"{icon} {p['name']}", callback_data=f"{prefix}_{p['id']}", style=style)])
    rows.append([InlineKeyboardButton("🔙 بازگشت به دسته‌ها", callback_data="menu_products")])
    return InlineKeyboardMarkup(rows)


def product_detail_keyboard(product):
    rows = []
    if product["stock_status"] == "available":
        rows.append([InlineKeyboardButton("🛒 خرید", callback_data=f"buy_{product['id']}", style="success")])
    else:
        rows.append([InlineKeyboardButton("🔔 اطلاع بده وقتی موجود شد", callback_data=f"notify_{product['id']}", style="primary")])
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"cat_{product['category_id']}")])
    return InlineKeyboardMarkup(rows)


def wallet_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ شارژ کیف پول", callback_data="wallet_charge", style="success")],
        [InlineKeyboardButton("🎟 وارد کردن کد تخفیف", callback_data="wallet_coupon", style="primary")],
        [InlineKeyboardButton("📜 تاریخچه تراکنش‌ها", callback_data="wallet_history", style="primary")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")],
    ])


def confirm_charge_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ پرداخت کردم", callback_data="wallet_paid", style="success")],
        [InlineKeyboardButton("❌ انصراف", callback_data="back_main", style="danger")],
    ])


def join_channel_keyboard(link):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 عضویت در کانال", url=link, style="primary")],
        [InlineKeyboardButton("✅ عضو شدم", callback_data="check_join", style="success")],
    ])


# ---------------------------------------------------------------------------
# ادمین
# ---------------------------------------------------------------------------

def admin_main_menu():
    keyboard = [
        [InlineKeyboardButton("📦 مدیریت محصولات", callback_data="admin_products", style="primary")],
        [InlineKeyboardButton("🗂 مدیریت دسته‌ها", callback_data="admin_categories", style="primary")],
        [InlineKeyboardButton("👥 کاربران و آمار", callback_data="admin_users", style="primary")],
        [InlineKeyboardButton("💳 تنظیم شماره کارت", callback_data="admin_card", style="primary")],
        [InlineKeyboardButton("🎧 تنظیم آیدی پشتیبانی", callback_data="admin_support", style="primary")],
        [InlineKeyboardButton("🔒 عضویت اجباری", callback_data="admin_forcejoin", style="primary")],
        [InlineKeyboardButton("💰 درخواست‌های شارژ کیف پول", callback_data="admin_charges", style="success")],
        [InlineKeyboardButton("🎟 مدیریت کدهای تخفیف", callback_data="admin_coupons", style="success"),
         InlineKeyboardButton("📊 آمار فروش", callback_data="admin_stats", style="success")],
        [InlineKeyboardButton("📢 پیام همگانی", callback_data="admin_broadcast", style="success")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="back_main", style="danger")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_coupons_menu():
    coupons = db.get_all_coupons()
    rows = [[InlineKeyboardButton("➕ ساخت کد تخفیف جدید", callback_data="admin_addcoupon", style="success")]]
    for c in coupons:
        label = f"{c['code']} | {c['amount']:,} تومان | {c['used_count']}/{c['max_uses']}"
        rows.append([
            InlineKeyboardButton(label, callback_data=f"admin_coupon_{c['code']}", style="primary"),
            InlineKeyboardButton("🗑", callback_data=f"admin_delcoupon_{c['code']}", style="danger"),
        ])
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_home")])
    return InlineKeyboardMarkup(rows)


def category_type_choice_keyboard():
    """بعد از دریافت نام دسته، نوع دسته (ویژه/عادی) را می‌پرسد."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ دسته ویژه", callback_data="admin_newcat_special_yes", style="success")],
        [InlineKeyboardButton("📦 دسته عادی", callback_data="admin_newcat_special_no", style="primary")],
        [InlineKeyboardButton("❌ انصراف", callback_data="admin_categories", style="danger")],
    ])


def broadcast_confirm_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ ارسال برای همه", callback_data="admin_broadcast_send", style="success")],
        [InlineKeyboardButton("❌ انصراف", callback_data="admin_broadcast_cancel", style="danger")],
    ])


def admin_categories_menu():
    cats = db.get_categories()
    rows = [[InlineKeyboardButton("➕ افزودن دسته", callback_data="admin_addcat", style="success")]]
    for c in cats:
        prefix = "⭐" if c.get("is_special") else "✏️"
        rows.append([
            InlineKeyboardButton(f"{prefix} {c['name']}", callback_data=f"admin_editcat_{c['id']}", style="primary"),
            InlineKeyboardButton("🗑", callback_data=f"admin_delcat_{c['id']}", style="danger"),
        ])
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_home")])
    return InlineKeyboardMarkup(rows)


def admin_edit_category_keyboard(category_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ ویرایش نام", callback_data=f"admin_setcat_{category_id}", style="primary")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_categories")],
    ])


def admin_products_categories_keyboard():
    cats = db.get_categories()
    rows = []
    for c in cats:
        rows.append([InlineKeyboardButton(c["name"], callback_data=f"admin_prodcat_{c['id']}", style="primary")])
    if not cats:
        rows.append([InlineKeyboardButton("⚠️ ابتدا یک دسته اضافه کنید", callback_data="admin_categories", style="danger")])
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_home")])
    return InlineKeyboardMarkup(rows)


def admin_products_list_keyboard(category_id):
    products = db.get_products_by_category(category_id)
    rows = [[InlineKeyboardButton("➕ افزودن محصول", callback_data=f"admin_addprod_{category_id}", style="success")]]
    for p in products:
        icon = "✅" if p["stock_status"] == "available" else "❌"
        style = "success" if p["stock_status"] == "available" else "danger"
        rows.append([InlineKeyboardButton(f"{icon} {p['name']}", callback_data=f"admin_prod_{p['id']}", style=style)])
    rows.append([InlineKeyboardButton("🔙 بازگشت به دسته‌ها", callback_data="admin_products")])
    return InlineKeyboardMarkup(rows)


def admin_product_manage_keyboard(product):
    stock_toggle_text = "❌ تنظیم ناموجود" if product["stock_status"] == "available" else "✅ تنظیم موجود"
    stock_toggle_data = f"admin_stockoff_{product['id']}" if product["stock_status"] == "available" else f"admin_stockon_{product['id']}"
    stock_toggle_style = "danger" if product["stock_status"] == "available" else "success"
    rows = [
        [InlineKeyboardButton("✏️ ویرایش نام", callback_data=f"admin_editname_{product['id']}", style="primary")],
        [InlineKeyboardButton("📝 ویرایش توضیحات", callback_data=f"admin_editdesc_{product['id']}", style="primary")],
        [InlineKeyboardButton("💵 ویرایش قیمت", callback_data=f"admin_editprice_{product['id']}", style="primary")],
        [InlineKeyboardButton(stock_toggle_text, callback_data=stock_toggle_data, style=stock_toggle_style)],
        [InlineKeyboardButton("🗑 حذف محصول", callback_data=f"admin_delprod_{product['id']}", style="danger")],
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
            callback_data=f"admin_user_{u['telegram_id']}",
            style="primary",
        )])
    nav = []
    if start > 0:
        nav.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f"admin_users_page_{page-1}", style="primary"))
    if start + per_page < len(users):
        nav.append(InlineKeyboardButton("➡️ بعدی", callback_data=f"admin_users_page_{page+1}", style="primary"))
    if nav:
        rows.append(nav)
    rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_home")])
    return InlineKeyboardMarkup(rows)


def admin_user_manage_keyboard(telegram_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ ویرایش موجودی کیف پول", callback_data=f"admin_setbalance_{telegram_id}", style="primary")],
        [InlineKeyboardButton("💬 ارسال پیام به این کاربر", callback_data=f"admin_replyuser_{telegram_id}", style="success")],
        [InlineKeyboardButton("🔙 بازگشت به لیست کاربران", callback_data="admin_users")],
    ])


def admin_charge_request_keyboard(request_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تایید", callback_data=f"admin_chargeok_{request_id}", style="success"),
            InlineKeyboardButton("❌ رد", callback_data=f"admin_chargeno_{request_id}", style="danger"),
        ]
    ])


def admin_forcejoin_keyboard():
    from config import DB_PATH  # noqa
    enabled = db.get_setting("force_join_enabled", "0") == "1"
    toggle_text = "🔴 غیرفعال کردن عضویت اجباری" if enabled else "🟢 فعال کردن عضویت اجباری"
    toggle_style = "danger" if enabled else "success"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 تنظیم لینک/آیدی کانال", callback_data="admin_setforcejoin", style="primary")],
        [InlineKeyboardButton(toggle_text, callback_data="admin_toggleforcejoin", style=toggle_style)],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_home")],
    ])
