# -*- coding: utf-8 -*-
"""
تنظیمات ربات از طریق متغیرهای محیطی (Environment Variables) خوانده می‌شوند.
این متغیرها را در پنل Railway در بخش Variables تنظیم کنید:

BOT_TOKEN   -> توکن ربات که از @BotFather گرفته‌اید (اجباری)
ADMIN_IDS   -> آیدی عددی ادمین/ادمین‌ها با کاما جدا شده، مثال: 123456789,987654321 (اجباری)
DB_PATH     -> مسیر فایل دیتابیس (اختیاری - پیش‌فرض shop.db)
"""

import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()

_admin_ids_raw = os.environ.get("ADMIN_IDS", "").strip()
ADMIN_IDS = [int(x) for x in _admin_ids_raw.split(",") if x.strip().isdigit()]

DB_PATH = os.environ.get("DB_PATH", "shop.db").strip()

if not BOT_TOKEN:
    raise RuntimeError(
        "متغیر محیطی BOT_TOKEN تنظیم نشده است. آن را در تنظیمات Railway اضافه کنید."
    )

if not ADMIN_IDS:
    raise RuntimeError(
        "متغیر محیطی ADMIN_IDS تنظیم نشده است. آیدی عددی ادمین را در تنظیمات Railway اضافه کنید."
    )
