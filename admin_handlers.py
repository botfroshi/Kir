# -*- coding: utf-8 -*-
"""
هندلرهای مربوط به پنل ادمین.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.error import TelegramError

import db
import state
import keyboards
from config import ADMIN_IDS


def is_admin(telegram_id):
    return telegram_id in ADMIN_IDS


async def guard(update: Update) -> bool:
    """اگر کاربر ادمین نبود پیام رد دسترسی می‌دهد. True یعنی مجاز است."""
    user = update.effective_user
    if not is_admin(user.id):
        if update.callback_query:
            await update.callback_query.answer("شما به این بخش دسترسی ندارید.", show_alert=True)
        else:
            await update.effective_message.reply_text("شما به این بخش دسترسی ندارید.")
        return False
    return True


async def admin_home_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    await query.answer()
    state.clear_state(query.from_user.id)
    await query.message.edit_text("⚙️ پنل ادمین - یک بخش را انتخاب کنید:", reply_markup=keyboards.admin_main_menu())


# ---------------------------------------------------------------------------
# دسته‌بندی‌ها
# ---------------------------------------------------------------------------

async def admin_categories_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    await query.answer()
    await query.message.edit_text("🗂 مدیریت دسته‌بندی‌ها:", reply_markup=keyboards.admin_categories_menu())


async def admin_addcat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    await query.answer()
    state.set_state(query.from_user.id, "admin_add_category_name")
    await query.message.edit_text(
        "نام دسته جدید را ارسال کنید:", reply_markup=keyboards.back_button("admin_categories")
    )


async def admin_editcat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    category_id = int(query.data.split("_")[-1])
    category = db.get_category(category_id)
    await query.answer()
    if not category:
        await query.message.edit_text("این دسته یافت نشد.", reply_markup=keyboards.admin_categories_menu())
        return
    await query.message.edit_text(
        f"دسته انتخاب شده: {category['name']}",
        reply_markup=keyboards.admin_edit_category_keyboard(category_id),
    )


async def admin_setcat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    category_id = int(query.data.split("_")[-1])
    await query.answer()
    state.set_state(query.from_user.id, "admin_edit_category_name", {"category_id": category_id})
    await query.message.edit_text(
        "نام جدید دسته را ارسال کنید:",
        reply_markup=keyboards.back_button(f"admin_editcat_{category_id}"),
    )


async def admin_delcat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    category_id = int(query.data.split("_")[-1])
    await query.answer()
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ بله، حذف شود", callback_data=f"admin_delcatY_{category_id}"),
         InlineKeyboardButton("❌ انصراف", callback_data="admin_categories")],
    ])
    await query.message.edit_text(
        "⚠️ با حذف این دسته، تمام محصولات داخل آن نیز حذف می‌شوند. آیا مطمئن هستید؟",
        reply_markup=kb,
    )


async def admin_delcat_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    category_id = int(query.data.split("_")[-1])
    db.delete_category(category_id)
    await query.answer("دسته حذف شد ✅", show_alert=True)
    await query.message.edit_text("🗂 مدیریت دسته‌بندی‌ها:", reply_markup=keyboards.admin_categories_menu())


# ---------------------------------------------------------------------------
# محصولات
# ---------------------------------------------------------------------------

async def admin_products_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        "یک دسته را برای مدیریت محصولاتش انتخاب کنید:",
        reply_markup=keyboards.admin_products_categories_keyboard(),
    )


async def admin_prodcat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    category_id = int(query.data.split("_")[-1])
    category = db.get_category(category_id)
    await query.answer()
    if not category:
        await query.message.edit_text("این دسته یافت نشد.", reply_markup=keyboards.admin_products_categories_keyboard())
        return
    await query.message.edit_text(
        f"محصولات دسته «{category['name']}»:",
        reply_markup=keyboards.admin_products_list_keyboard(category_id),
    )


async def admin_addprod_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    category_id = int(query.data.split("_")[-1])
    await query.answer()
    state.set_state(query.from_user.id, "admin_add_product_name", {"category_id": category_id})
    await query.message.edit_text(
        "نام محصول جدید را ارسال کنید:",
        reply_markup=keyboards.back_button(f"admin_prodcat_{category_id}"),
    )


def _product_detail_text(product):
    status_text = "✅ موجود" if product["stock_status"] == "available" else "❌ ناموجود"
    return (
        f"🛍 <b>{product['name']}</b>\n\n"
        f"توضیحات: {product['description'] or 'ندارد'}\n"
        f"💵 قیمت: {product['price']:,} تومان\n"
        f"📦 وضعیت: {status_text}"
    )


async def admin_prod_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    product_id = int(query.data.split("_")[-1])
    product = db.get_product(product_id)
    await query.answer()
    if not product:
        await query.message.edit_text("این محصول یافت نشد.")
        return
    await query.message.edit_text(
        _product_detail_text(product),
        parse_mode=ParseMode.HTML,
        reply_markup=keyboards.admin_product_manage_keyboard(product),
    )


async def admin_editname_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    product_id = int(query.data.split("_")[-1])
    await query.answer()
    state.set_state(query.from_user.id, "admin_edit_product_name", {"product_id": product_id})
    await query.message.edit_text("نام جدید محصول را ارسال کنید:", reply_markup=keyboards.back_button(f"admin_prod_{product_id}"))


async def admin_editdesc_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    product_id = int(query.data.split("_")[-1])
    await query.answer()
    state.set_state(query.from_user.id, "admin_edit_product_desc", {"product_id": product_id})
    await query.message.edit_text("توضیحات جدید محصول را ارسال کنید:", reply_markup=keyboards.back_button(f"admin_prod_{product_id}"))


async def admin_editprice_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    product_id = int(query.data.split("_")[-1])
    await query.answer()
    state.set_state(query.from_user.id, "admin_edit_product_price", {"product_id": product_id})
    await query.message.edit_text("قیمت جدید محصول را به تومان و فقط عدد ارسال کنید:", reply_markup=keyboards.back_button(f"admin_prod_{product_id}"))


async def admin_stock_toggle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    data = query.data
    product_id = int(data.split("_")[-1])
    new_status = "available" if data.startswith("admin_stockon_") else "unavailable"
    db.update_product_field(product_id, "stock_status", new_status)
    product = db.get_product(product_id)
    await query.answer("وضعیت موجودی بروزرسانی شد ✅")

    if new_status == "available":
        requests = db.get_notify_requests_for_product(product_id)
        for r in requests:
            try:
                await context.bot.send_message(
                    r["telegram_id"],
                    f"🔔 خبر خوب! محصول «{product['name']}» موجود شد و آماده خرید است.",
                )
            except TelegramError:
                pass
        db.clear_notify_requests_for_product(product_id)

    await query.message.edit_text(
        _product_detail_text(product), parse_mode=ParseMode.HTML,
        reply_markup=keyboards.admin_product_manage_keyboard(product),
    )


async def admin_delprod_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    product_id = int(query.data.split("_")[-1])
    await query.answer()
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ بله، حذف شود", callback_data=f"admin_delprodY_{product_id}"),
         InlineKeyboardButton("❌ انصراف", callback_data=f"admin_prod_{product_id}")],
    ])
    await query.message.edit_text("⚠️ آیا از حذف این محصول مطمئن هستید؟", reply_markup=kb)


async def admin_delprod_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    product_id = int(query.data.split("_")[-1])
    product = db.get_product(product_id)
    category_id = product["category_id"] if product else None
    db.delete_product(product_id)
    await query.answer("محصول حذف شد ✅", show_alert=True)
    if category_id:
        await query.message.edit_text(
            "محصولات این دسته:", reply_markup=keyboards.admin_products_list_keyboard(category_id)
        )
    else:
        await query.message.edit_text("⚙️ پنل ادمین:", reply_markup=keyboards.admin_main_menu())


# ---------------------------------------------------------------------------
# کاربران و آمار
# ---------------------------------------------------------------------------

async def admin_users_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    await query.answer()
    users = db.get_all_users()
    text = f"👥 تعداد کل کاربران: {len(users)}\n\nروی هر کاربر بزنید تا موجودی او را ویرایش کنید:"
    if not users:
        text = "هنوز هیچ کاربری با ربات شروع نکرده است."
    await query.message.edit_text(text, reply_markup=keyboards.admin_users_list_keyboard(users, page=0))


async def admin_users_page_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    page = int(query.data.split("_")[-1])
    await query.answer()
    users = db.get_all_users()
    await query.message.edit_text(
        f"👥 تعداد کل کاربران: {len(users)}\n\nروی هر کاربر بزنید تا موجودی او را ویرایش کنید:",
        reply_markup=keyboards.admin_users_list_keyboard(users, page=page),
    )


async def admin_user_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    telegram_id = int(query.data.split("_")[-1])
    u = db.get_user(telegram_id)
    await query.answer()
    if not u:
        await query.message.edit_text("کاربر یافت نشد.", reply_markup=keyboards.admin_main_menu())
        return
    uname = f"@{u['username']}" if u["username"] else "بدون‌یوزرنیم"
    text = (
        f"👤 اطلاعات کاربر\n\n"
        f"نام کاربری: {uname}\n"
        f"آیدی عددی: <code>{u['telegram_id']}</code>\n"
        f"👛 موجودی کیف پول: {u['balance']:,} تومان"
    )
    await query.message.edit_text(
        text, parse_mode=ParseMode.HTML, reply_markup=keyboards.admin_user_manage_keyboard(telegram_id)
    )


async def admin_setbalance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    telegram_id = int(query.data.split("_")[-1])
    await query.answer()
    state.set_state(query.from_user.id, "admin_set_balance", {"telegram_id": telegram_id})
    await query.message.edit_text(
        "موجودی جدید کیف پول این کاربر را فقط به صورت عدد (تومان) ارسال کنید:",
        reply_markup=keyboards.back_button(f"admin_user_{telegram_id}"),
    )


# ---------------------------------------------------------------------------
# شماره کارت
# ---------------------------------------------------------------------------

def _card_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ ویرایش شماره کارت", callback_data="admin_setcardnum")],
        [InlineKeyboardButton("✏️ ویرایش نام و نام‌خانوادگی", callback_data="admin_setcardholder")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_home")],
    ])


async def admin_card_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    await query.answer()
    number = db.get_setting("card_number", "تنظیم نشده")
    holder = db.get_setting("card_holder", "تنظیم نشده")
    text = f"💳 تنظیمات شماره کارت\n\nشماره کارت فعلی: {number}\nنام صاحب کارت: {holder}"
    await query.message.edit_text(text, reply_markup=_card_menu_keyboard())


async def admin_setcardnum_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    await query.answer()
    state.set_state(query.from_user.id, "admin_set_card_number")
    await query.message.edit_text("شماره کارت جدید را ارسال کنید:", reply_markup=keyboards.back_button("admin_card"))


async def admin_setcardholder_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    await query.answer()
    state.set_state(query.from_user.id, "admin_set_card_holder")
    await query.message.edit_text("نام و نام‌خانوادگی صاحب کارت را ارسال کنید:", reply_markup=keyboards.back_button("admin_card"))


# ---------------------------------------------------------------------------
# آیدی پشتیبانی
# ---------------------------------------------------------------------------

async def admin_support_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    await query.answer()
    support_id = db.get_setting("support_id", "تنظیم نشده")
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ ویرایش آیدی پشتیبانی", callback_data="admin_setsupportid")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_home")],
    ])
    await query.message.edit_text(f"🎧 آیدی پشتیبانی فعلی: {support_id}", reply_markup=kb)


async def admin_setsupportid_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    await query.answer()
    state.set_state(query.from_user.id, "admin_set_support_id")
    await query.message.edit_text(
        "آیدی پشتیبانی را ارسال کنید (مثال: @support_username):",
        reply_markup=keyboards.back_button("admin_support"),
    )


# ---------------------------------------------------------------------------
# عضویت اجباری
# ---------------------------------------------------------------------------

async def admin_forcejoin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    await query.answer()
    enabled = db.get_setting("force_join_enabled", "0") == "1"
    channel = db.get_setting("force_join_channel", "تنظیم نشده")
    link = db.get_setting("force_join_link", "تنظیم نشده")
    text = (
        f"🔒 عضویت اجباری\n\n"
        f"وضعیت: {'فعال ✅' if enabled else 'غیرفعال ❌'}\n"
        f"آیدی کانال (برای بررسی عضویت): {channel}\n"
        f"لینک کانال (برای نمایش به کاربر): {link}"
    )
    await query.message.edit_text(text, reply_markup=keyboards.admin_forcejoin_keyboard())


async def admin_setforcejoin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    await query.answer()
    state.set_state(query.from_user.id, "admin_set_forcejoin_channel")
    await query.message.edit_text(
        "آیدی عددی یا یوزرنیم کانال را ارسال کنید (مثال: @mychannel یا -1001234567890):\n\n"
        "⚠️ توجه: ربات باید در آن کانال ادمین باشد تا بتواند عضویت را بررسی کند.",
        reply_markup=keyboards.back_button("admin_forcejoin"),
    )


async def admin_toggleforcejoin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    enabled = db.get_setting("force_join_enabled", "0") == "1"
    new_value = "0" if enabled else "1"
    db.set_setting("force_join_enabled", new_value)
    await query.answer("وضعیت بروزرسانی شد ✅")
    channel = db.get_setting("force_join_channel", "تنظیم نشده")
    link = db.get_setting("force_join_link", "تنظیم نشده")
    text = (
        f"🔒 عضویت اجباری\n\n"
        f"وضعیت: {'فعال ✅' if new_value == '1' else 'غیرفعال ❌'}\n"
        f"آیدی کانال (برای بررسی عضویت): {channel}\n"
        f"لینک کانال (برای نمایش به کاربر): {link}"
    )
    await query.message.edit_text(text, reply_markup=keyboards.admin_forcejoin_keyboard())


# ---------------------------------------------------------------------------
# درخواست‌های شارژ کیف پول
# ---------------------------------------------------------------------------

async def admin_charges_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    await query.answer()
    requests = db.get_pending_charge_requests()
    if not requests:
        await query.message.edit_text(
            "در حال حاضر درخواست شارژ در انتظار تاییدی وجود ندارد.",
            reply_markup=keyboards.back_button("admin_home"),
        )
        return
    await query.message.edit_text(
        f"💰 تعداد درخواست‌های در انتظار: {len(requests)}\nهر درخواست به صورت جداگانه ارسال می‌شود:",
        reply_markup=keyboards.back_button("admin_home"),
    )
    for r in requests:
        uname = f"@{r['username']}" if r["username"] else "بدون‌یوزرنیم"
        text = (
            f"درخواست #{r['id']}\n"
            f"کاربر: {uname}\n"
            f"آیدی عددی: {r['telegram_id']}\n"
            f"مبلغ: {r['amount']:,} تومان"
        )
        await context.bot.send_message(
            query.from_user.id, text, reply_markup=keyboards.admin_charge_request_keyboard(r["id"])
        )


async def admin_charge_decision_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await guard(update):
        return
    query = update.callback_query
    data = query.data
    request_id = int(data.split("_")[-1])
    approve = data.startswith("admin_chargeok_")
    req = db.get_charge_request(request_id)

    if not req or req["status"] != "pending":
        await query.answer("این درخواست قبلاً بررسی شده است.", show_alert=True)
        return

    if approve:
        db.update_balance(req["telegram_id"], req["amount"])
        db.update_charge_request_status(request_id, "approved")
        await query.answer("شارژ تایید و به حساب کاربر اضافه شد ✅", show_alert=True)
        try:
            await query.edit_message_text(query.message.text + "\n\n✅ تایید شد و به حساب کاربر اضافه شد.")
        except TelegramError:
            pass
        try:
            new_balance = db.get_user(req["telegram_id"])["balance"]
            await context.bot.send_message(
                req["telegram_id"],
                f"✅ درخواست شارژ کیف پول شما به مبلغ {req['amount']:,} تومان تایید شد.\n"
                f"👛 موجودی جدید شما: {new_balance:,} تومان",
            )
        except TelegramError:
            pass
    else:
        db.update_charge_request_status(request_id, "rejected")
        await query.answer("درخواست رد شد.", show_alert=True)
        try:
            await query.edit_message_text(query.message.text + "\n\n❌ رد شد.")
        except TelegramError:
            pass
        try:
            await context.bot.send_message(
                req["telegram_id"],
                f"❌ درخواست شارژ کیف پول شما به مبلغ {req['amount']:,} تومان رد شد.\n"
                f"در صورت داشتن سوال، از بخش پشتیبانی با ما در تماس باشید.",
            )
        except TelegramError:
            pass


# ---------------------------------------------------------------------------
# هندلر متن آزاد ادمین (بر اساس وضعیت state)
# ---------------------------------------------------------------------------

async def admin_text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """در صورتی که پیام مربوط به یک وضعیت ادمین باشد آن را پردازش می‌کند.
    خروجی True یعنی پیام مصرف شد."""
    user = update.effective_user
    if not is_admin(user.id):
        return False

    st = state.get_state(user.id)
    if not st:
        return False

    action = st["action"]
    data = st["data"]
    text = (update.message.text or "").strip()

    if action == "admin_add_category_name":
        if not text:
            await update.message.reply_text("نام دسته نمی‌تواند خالی باشد.")
            return True
        db.add_category(text)
        state.clear_state(user.id)
        await update.message.reply_text(f"✅ دسته «{text}» اضافه شد.", reply_markup=keyboards.admin_categories_menu())
        return True

    if action == "admin_edit_category_name":
        if not text:
            await update.message.reply_text("نام دسته نمی‌تواند خالی باشد.")
            return True
        db.update_category(data["category_id"], text)
        state.clear_state(user.id)
        await update.message.reply_text(f"✅ نام دسته به «{text}» تغییر یافت.", reply_markup=keyboards.admin_categories_menu())
        return True

    if action == "admin_add_product_name":
        if not text:
            await update.message.reply_text("نام محصول نمی‌تواند خالی باشد.")
            return True
        data["name"] = text
        state.set_state(user.id, "admin_add_product_price", data)
        await update.message.reply_text("قیمت محصول را به تومان و فقط عدد ارسال کنید:")
        return True

    if action == "admin_add_product_price":
        if not text.isdigit():
            await update.message.reply_text("لطفاً فقط عدد ارسال کنید. مثال: 150000")
            return True
        data["price"] = int(text)
        state.set_state(user.id, "admin_add_product_desc", data)
        await update.message.reply_text("توضیحات محصول را ارسال کنید (یا - برای رد شدن):")
        return True

    if action == "admin_add_product_desc":
        description = "" if text == "-" else text
        product_id = db.add_product(data["category_id"], data["name"], description, data["price"], "unavailable")
        state.clear_state(user.id)
        product = db.get_product(product_id)
        await update.message.reply_text(
            "✅ محصول با موفقیت اضافه شد. وضعیت پیش‌فرض آن «ناموجود» است.",
        )
        await update.message.reply_text(
            _product_detail_text(product), parse_mode=ParseMode.HTML,
            reply_markup=keyboards.admin_product_manage_keyboard(product),
        )
        return True

    if action == "admin_edit_product_name":
        if not text:
            await update.message.reply_text("نام محصول نمی‌تواند خالی باشد.")
            return True
        db.update_product_field(data["product_id"], "name", text)
        state.clear_state(user.id)
        product = db.get_product(data["product_id"])
        await update.message.reply_text(
            "✅ نام محصول بروزرسانی شد.", reply_markup=keyboards.admin_product_manage_keyboard(product)
        )
        return True

    if action == "admin_edit_product_desc":
        db.update_product_field(data["product_id"], "description", text)
        state.clear_state(user.id)
        product = db.get_product(data["product_id"])
        await update.message.reply_text(
            "✅ توضیحات محصول بروزرسانی شد.", reply_markup=keyboards.admin_product_manage_keyboard(product)
        )
        return True

    if action == "admin_edit_product_price":
        if not text.isdigit():
            await update.message.reply_text("لطفاً فقط عدد ارسال کنید.")
            return True
        db.update_product_field(data["product_id"], "price", int(text))
        state.clear_state(user.id)
        product = db.get_product(data["product_id"])
        await update.message.reply_text(
            "✅ قیمت محصول بروزرسانی شد.", reply_markup=keyboards.admin_product_manage_keyboard(product)
        )
        return True

    if action == "admin_set_balance":
        if not text.lstrip("-").isdigit():
            await update.message.reply_text("لطفاً فقط عدد ارسال کنید.")
            return True
        telegram_id = data["telegram_id"]
        db.set_balance(telegram_id, int(text))
        state.clear_state(user.id)
        await update.message.reply_text(
            f"✅ موجودی کاربر {telegram_id} به {int(text):,} تومان تغییر یافت.",
            reply_markup=keyboards.admin_user_manage_keyboard(telegram_id),
        )
        try:
            await context.bot.send_message(
                telegram_id, f"👛 موجودی کیف پول شما توسط ادمین به {int(text):,} تومان تغییر یافت."
            )
        except TelegramError:
            pass
        return True

    if action == "admin_set_card_number":
        db.set_setting("card_number", text)
        state.clear_state(user.id)
        await update.message.reply_text("✅ شماره کارت بروزرسانی شد.", reply_markup=_card_menu_keyboard())
        return True

    if action == "admin_set_card_holder":
        db.set_setting("card_holder", text)
        state.clear_state(user.id)
        await update.message.reply_text("✅ نام صاحب کارت بروزرسانی شد.", reply_markup=_card_menu_keyboard())
        return True

    if action == "admin_set_support_id":
        db.set_setting("support_id", text)
        state.clear_state(user.id)
        await update.message.reply_text("✅ آیدی پشتیبانی بروزرسانی شد.")
        return True

    if action == "admin_set_forcejoin_channel":
        data["channel"] = text
        db.set_setting("force_join_channel", text)
        state.set_state(user.id, "admin_set_forcejoin_link", data)
        await update.message.reply_text("حالا لینک عضویت کانال را ارسال کنید (مثال: https://t.me/mychannel):")
        return True

    if action == "admin_set_forcejoin_link":
        db.set_setting("force_join_link", text)
        state.clear_state(user.id)
        await update.message.reply_text("✅ تنظیمات عضویت اجباری ذخیره شد.", reply_markup=keyboards.admin_forcejoin_keyboard())
        return True

    return False
