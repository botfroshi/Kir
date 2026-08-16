# -*- coding: utf-8 -*-
"""
هندلرهای مربوط به کاربر عادی (خریدار).
"""

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.error import TelegramError

import db
import state
import keyboards
from config import ADMIN_IDS


def is_admin(telegram_id):
    return telegram_id in ADMIN_IDS


async def check_force_join(update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_id):
    """اگر عضویت اجباری فعال باشد و کاربر عضو کانال نباشد، پیام عضویت نمایش داده می‌شود.
    خروجی True یعنی کاربر مجاز است ادامه دهد."""
    enabled = db.get_setting("force_join_enabled", "0") == "1"
    if not enabled:
        return True

    channel_id = db.get_setting("force_join_channel", "")
    channel_link = db.get_setting("force_join_link", "")
    if not channel_id or not channel_link:
        return True

    try:
        member = await context.bot.get_chat_member(chat_id=channel_id, user_id=telegram_id)
        if member.status in ("member", "administrator", "creator"):
            return True
    except TelegramError:
        pass

    text = "برای استفاده از ربات، ابتدا باید در کانال زیر عضو شوید:"
    if update.callback_query:
        await update.callback_query.answer("شما هنوز در کانال عضو نشده‌اید.", show_alert=True)
        try:
            await update.callback_query.message.edit_text(
                text, reply_markup=keyboards.join_channel_keyboard(channel_link)
            )
        except TelegramError:
            await update.callback_query.message.reply_text(
                text, reply_markup=keyboards.join_channel_keyboard(channel_link)
            )
    else:
        await update.effective_message.reply_text(
            text, reply_markup=keyboards.join_channel_keyboard(channel_link)
        )
    return False


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    state.clear_state(user.id)

    referred_by = None
    if context.args:
        arg = context.args[0]
        if arg.startswith("ref_") and arg[4:].isdigit():
            referred_by = int(arg[4:])

    db_user = db.get_or_create_user(user.id, user.username, referred_by=referred_by)

    if not await check_force_join(update, context, user.id):
        return

    badge = db.get_badge(db_user["total_spent"])
    await update.effective_message.reply_text(
        f"سلام {user.first_name} 👋\nبه فروشگاه ما خوش آمدید.\n\n"
        f"👛 موجودی کیف پول: {db_user['balance']:,} تومان\n"
        f"{badge} سطح کاربری شما\n\n"
        f"از منوی زیر یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=keyboards.user_main_menu(is_admin(user.id)),
    )


async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    if not await check_force_join(update, context, user.id):
        return
    await query.answer("عضویت شما تایید شد ✅")
    await query.message.edit_text(
        "خوش آمدید! از منوی زیر یکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=keyboards.user_main_menu(is_admin(user.id)),
    )


async def back_main_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    state.clear_state(user.id)
    await query.answer()
    await query.message.edit_text(
        "منوی اصلی:", reply_markup=keyboards.user_main_menu(is_admin(user.id))
    )


async def menu_products_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    if not await check_force_join(update, context, user.id):
        return
    await query.answer()
    cats = db.get_categories()
    if not cats:
        await query.message.edit_text(
            "در حال حاضر هیچ دسته‌بندی‌ای تعریف نشده است.",
            reply_markup=keyboards.back_button("back_main"),
        )
        return
    await query.message.edit_text(
        "یک دسته‌بندی را انتخاب کنید:", reply_markup=keyboards.categories_keyboard()
    )


async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    if not await check_force_join(update, context, user.id):
        return
    category_id = int(query.data.split("_", 1)[1])
    category = db.get_category(category_id)
    await query.answer()
    if not category:
        await query.message.edit_text("این دسته یافت نشد.", reply_markup=keyboards.categories_keyboard())
        return
    products = db.get_products_by_category(category_id)
    if not products:
        await query.message.edit_text(
            f"دسته «{category['name']}» در حال حاضر محصولی ندارد.",
            reply_markup=keyboards.back_button("menu_products"),
        )
        return
    await query.message.edit_text(
        f"محصولات دسته «{category['name']}»:",
        reply_markup=keyboards.products_keyboard(category_id),
    )


async def product_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    if not await check_force_join(update, context, user.id):
        return
    product_id = int(query.data.split("_", 1)[1])
    product = db.get_product(product_id)
    await query.answer()
    if not product:
        await query.message.edit_text("این محصول یافت نشد.")
        return
    status_text = "✅ موجود" if product["stock_status"] == "available" else "❌ ناموجود"
    text = (
        f"🛍 <b>{product['name']}</b>\n\n"
        f"{product['description'] or 'بدون توضیحات'}\n\n"
        f"💵 قیمت: {product['price']:,} تومان\n"
        f"📦 وضعیت: {status_text}"
    )
    await query.message.edit_text(
        text, parse_mode=ParseMode.HTML, reply_markup=keyboards.product_detail_keyboard(product)
    )


async def notify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    product_id = int(query.data.split("_", 1)[1])
    db.add_notify_request(user.id, product_id)
    await query.answer("به محض موجود شدن این محصول به شما اطلاع داده می‌شود ✅", show_alert=True)


async def buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    if not await check_force_join(update, context, user.id):
        return
    product_id = int(query.data.split("_", 1)[1])
    product = db.get_product(product_id)
    if not product or product["stock_status"] != "available":
        await query.answer("این محصول در حال حاضر موجود نیست.", show_alert=True)
        return

    db_user = db.get_or_create_user(user.id, user.username)
    if db_user["balance"] < product["price"]:
        await query.answer(
            f"موجودی کیف پول شما کافی نیست.\nموجودی شما: {db_user['balance']:,} تومان\nقیمت محصول: {product['price']:,} تومان",
            show_alert=True,
        )
        return

    is_first_purchase = db.count_orders(user.id) == 0

    db.update_balance(user.id, -product["price"])
    db.create_order(user.id, product["id"], product["name"], product["price"])
    db.add_total_spent(user.id, product["price"])
    db.add_transaction(user.id, "purchase", -product["price"], f"خرید {product['name']}")
    await query.answer("خرید با موفقیت انجام شد ✅", show_alert=True)

    if is_first_purchase and db_user.get("referred_by"):
        referrer_id = db_user["referred_by"]
        bonus = 2000
        db.update_balance(referrer_id, bonus)
        db.add_transaction(referrer_id, "referral_bonus", bonus, f"پاداش دعوت کاربر {user.id}")
        try:
            await context.bot.send_message(
                referrer_id,
                f"🤝 یکی از کاربرانی که با لینک شما عضو شده بود اولین خریدش را انجام داد!\n"
                f"🎁 مبلغ {bonus:,} تومان به کیف پول شما اضافه شد.",
            )
        except TelegramError:
            pass

    new_balance = db.get_user(user.id)["balance"]
    text = (
        f"✅ خرید محصول «{product['name']}» با موفقیت انجام شد.\n\n"
        f"💵 مبلغ کسر شده: {product['price']:,} تومان\n"
        f"👛 موجودی جدید کیف پول: {new_balance:,} تومان"
    )
    await query.message.edit_text(text, reply_markup=keyboards.back_button("back_main"))

    for admin_id in ADMIN_IDS:
        try:
            uname = f"@{user.username}" if user.username else "بدون‌یوزرنیم"
            await context.bot.send_message(
                admin_id,
                f"🛒 خرید جدید!\nکاربر: {uname} | آیدی عددی: {user.id}\nمحصول: {product['name']}\nمبلغ: {product['price']:,} تومان",
            )
        except TelegramError:
            pass


async def menu_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    db_user = db.get_or_create_user(user.id, user.username)
    await query.answer()
    uname = f"@{user.username}" if user.username else "ثبت نشده"
    badge = db.get_badge(db_user["total_spent"])
    referrals = db.count_referrals(user.id)
    text = (
        f"👤 <b>حساب کاربری شما</b>\n\n"
        f"نام کاربری: {uname}\n"
        f"آیدی عددی: <code>{user.id}</code>\n"
        f"👛 موجودی کیف پول: {db_user['balance']:,} تومان\n"
        f"{badge} سطح کاربری (بر اساس {db_user['total_spent']:,} تومان خرید)\n"
        f"🤝 تعداد دعوت‌شدگان: {referrals} نفر"
    )
    await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboards.back_button("back_main"))


async def menu_referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()
    bot_username = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_username}?start=ref_{user.id}"
    referrals = db.count_referrals(user.id)
    text = (
        f"🤝 <b>دعوت از دوستان</b>\n\n"
        f"لینک اختصاصی شما:\n{link}\n\n"
        f"تا الان {referrals} نفر با لینک شما عضو شده‌اند.\n"
        f"به ازای اولین خرید هر کاربری که با لینک شما بیاید، جایزه نقدی به کیف پولتان اضافه می‌شود."
    )
    await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboards.back_button("back_main"))


async def menu_spin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()
    if not db.can_spin_today(user.id):
        await query.message.edit_text(
            "🎡 شما امروز قبلاً چرخ شانس را زده‌اید. فردا دوباره امتحان کنید!",
            reply_markup=keyboards.back_button("back_main"),
        )
        return
    prize = db.do_spin(user.id)
    if prize > 0:
        db.add_transaction(user.id, "spin", prize, "جایزه چرخ شانس روزانه")
        text = f"🎉 تبریک! شما {prize:,} تومان جایزه بردید و به کیف پولتان اضافه شد."
    else:
        text = "😅 این‌بار جایزه‌ای نبردید. فردا دوباره شانستان را امتحان کنید!"
    await query.message.edit_text(text, reply_markup=keyboards.back_button("back_main"))


async def menu_wallet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    db_user = db.get_or_create_user(user.id, user.username)
    await query.answer()
    text = f"👛 موجودی فعلی کیف پول شما: {db_user['balance']:,} تومان"
    await query.message.edit_text(text, reply_markup=keyboards.wallet_menu_keyboard())


async def wallet_charge_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()
    state.set_state(user.id, "await_charge_amount")
    await query.message.edit_text(
        "لطفاً مبلغی که می‌خواهید شارژ کنید را به تومان و فقط به صورت عدد ارسال کنید:\nمثال: 50000",
        reply_markup=keyboards.back_button("back_main"),
    )


async def wallet_paid_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    st = state.get_state(user.id)
    if not st or st.get("action") != "await_payment_confirm":
        await query.answer()
        return
    amount = st["data"]["amount"]
    request_id = db.create_charge_request(user.id, user.username, amount)
    state.clear_state(user.id)
    await query.answer("درخواست شما برای ادمین ارسال شد ✅", show_alert=True)
    await query.message.edit_text(
        "درخواست شارژ کیف پول شما ثبت شد و پس از تایید ادمین، مبلغ به حساب شما اضافه خواهد شد.",
        reply_markup=keyboards.back_button("back_main"),
    )

    uname = f"@{user.username}" if user.username else "بدون‌یوزرنیم"
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                f"💰 درخواست شارژ کیف پول جدید!\n\n"
                f"کاربر: {uname}\n"
                f"آیدی عددی: {user.id}\n"
                f"مبلغ درخواستی: {amount:,} تومان\n\n"
                f"لطفاً پس از بررسی واریزی، تایید یا رد کنید:",
                reply_markup=keyboards.admin_charge_request_keyboard(request_id),
            )
        except TelegramError:
            pass


async def wallet_history_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()
    txs = db.get_transactions(user.id, limit=10)
    if not txs:
        text = "📜 هنوز هیچ تراکنشی در کیف پول شما ثبت نشده است."
    else:
        labels = {
            "purchase": "🛒 خرید",
            "charge": "➕ شارژ",
            "referral_bonus": "🤝 پاداش دعوت",
            "coupon": "🎟 کد تخفیف",
            "spin": "🎡 چرخ شانس",
        }
        lines = []
        for t in txs:
            label = labels.get(t["type"], t["type"])
            sign = "+" if t["amount"] >= 0 else ""
            lines.append(f"{label}: {sign}{t['amount']:,} تومان — {t['description']}")
        text = "📜 <b>۱۰ تراکنش اخیر شما:</b>\n\n" + "\n".join(lines)
    await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboards.back_button("menu_wallet"))


async def wallet_coupon_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()
    state.set_state(user.id, "await_coupon_code")
    await query.message.edit_text(
        "کد تخفیف خود را ارسال کنید:", reply_markup=keyboards.back_button("menu_wallet")
    )


async def menu_search_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()
    state.set_state(user.id, "await_search_query")
    await query.message.edit_text(
        "نام محصول موردنظر خود را ارسال کنید:", reply_markup=keyboards.back_button("menu_products")
    )


async def menu_ticket_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()
    state.set_state(user.id, "await_ticket_message")
    support_id = db.get_setting("support_id", "")
    extra = ""
    if support_id:
        extra = f"\n\nهمچنین می‌توانید مستقیماً به پشتیبانی پیام دهید: {support_id}"
    await query.message.edit_text(
        "پیام خود را برای پشتیبانی ارسال کنید. پیام شما مستقیماً برای ادمین ارسال می‌شود:" + extra,
        reply_markup=keyboards.back_button("back_main"),
    )


# ---------------------------------------------------------------------------
# هندلر متن آزاد کاربر (بر اساس وضعیت state)
# ---------------------------------------------------------------------------

async def user_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """در صورتی که پیام مربوط به یک وضعیت کاربر عادی باشد آن را پردازش می‌کند.
    خروجی True یعنی پیام مصرف شد."""
    user = update.effective_user
    st = state.get_state(user.id)
    if not st:
        return False

    action = st["action"]
    text = (update.message.text or "").strip()

    if action == "await_charge_amount":
        if not text.isdigit() or int(text) <= 0:
            await update.message.reply_text("لطفاً فقط یک عدد صحیح و مثبت ارسال کنید. مثال: 50000")
            return True
        amount = int(text)
        card_number = db.get_setting("card_number", "تنظیم نشده")
        card_holder = db.get_setting("card_holder", "تنظیم نشده")
        state.set_state(user.id, "await_payment_confirm", {"amount": amount})
        await update.message.reply_text(
            f"مبلغ قابل پرداخت: {amount:,} تومان\n\n"
            f"لطفاً مبلغ فوق را به شماره کارت زیر واریز کنید:\n\n"
            f"💳 شماره کارت: <code>{card_number}</code>\n"
            f"👤 به نام: {card_holder}\n\n"
            f"پس از واریز، روی دکمه «پرداخت کردم» بزنید تا درخواست شما برای ادمین ارسال شود.",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboards.confirm_charge_keyboard(),
        )
        return True

    if action == "await_coupon_code":
        if not text:
            await update.message.reply_text("لطفاً یک کد ارسال کنید.")
            return True
        ok, result = db.redeem_coupon(text, user.id)
        state.clear_state(user.id)
        if ok:
            db.add_transaction(user.id, "coupon", result, f"استفاده از کد {text.upper().strip()}")
            new_balance = db.get_user(user.id)["balance"]
            await update.message.reply_text(
                f"✅ کد تخفیف با موفقیت اعمال شد!\n💵 مبلغ هدیه: {result:,} تومان\n👛 موجودی جدید: {new_balance:,} تومان",
                reply_markup=keyboards.back_button("back_main"),
            )
        else:
            await update.message.reply_text(f"❌ {result}", reply_markup=keyboards.back_button("menu_wallet"))
        return True

    if action == "await_search_query":
        if not text:
            await update.message.reply_text("لطفاً یک عبارت برای جستجو ارسال کنید.")
            return True
        state.clear_state(user.id)
        results = db.search_products(text)
        if not results:
            await update.message.reply_text(
                f"هیچ محصولی با عبارت «{text}» پیدا نشد.",
                reply_markup=keyboards.back_button("menu_products"),
            )
            return True
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        rows = []
        for p in results:
            icon = "✅" if p["stock_status"] == "available" else "❌"
            style = "success" if p["stock_status"] == "available" else "danger"
            rows.append([InlineKeyboardButton(f"{icon} {p['name']}", callback_data=f"prod_{p['id']}", style=style)])
        rows.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu_products")])
        await update.message.reply_text(f"نتایج جستجو برای «{text}»:", reply_markup=InlineKeyboardMarkup(rows))
        return True

    if action == "await_ticket_message":
        if not text:
            await update.message.reply_text("لطفاً یک پیام متنی ارسال کنید.")
            return True
        ticket_id = db.create_ticket(user.id, user.username, text)
        state.clear_state(user.id)
        await update.message.reply_text(
            "✅ پیام شما برای پشتیبانی ارسال شد. به زودی پاسخ داده می‌شود.",
            reply_markup=keyboards.back_button("back_main"),
        )
        uname = f"@{user.username}" if user.username else "بدون‌یوزرنیم"
        support_id = db.get_setting("support_id", "")
        support_line = f"\n\nآیدی پشتیبانی جهت پیگیری: {support_id}" if support_id else ""
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        reply_kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("💬 پاسخ به این کاربر", callback_data=f"admin_replyuser_{user.id}", style="success")
        ]])
        for admin_id in ADMIN_IDS:
            try:
                await context.bot.send_message(
                    admin_id,
                    f"🎫 تیکت جدید (#{ticket_id})\n\n"
                    f"از طرف: {uname}\n"
                    f"آیدی عددی: {user.id}\n\n"
                    f"متن پیام:\n{text}" + support_line,
                    reply_markup=reply_kb,
                )
            except TelegramError:
                pass
        return True

    return False
