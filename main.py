# -*- coding: utf-8 -*-
"""
نقطه شروع ربات فروشگاهی تلگرام.
اجرا با: python main.py
"""

import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

import db
import keyboards
import user_handlers
import admin_handlers
from config import BOT_TOKEN, ADMIN_IDS

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in ADMIN_IDS:
        await update.effective_message.reply_text("شما به این بخش دسترسی ندارید.")
        return
    await update.effective_message.reply_text(
        "⚙️ پنل ادمین - یک بخش را انتخاب کنید:", reply_markup=keyboards.admin_main_menu()
    )


async def generic_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    handled = await admin_handlers.admin_text_router(update, context)
    if handled:
        return
    handled = await user_handlers.user_text_router(update, context)
    if handled:
        return
    # پیام متنی بدون وضعیت مشخص - راهنمایی کلی
    user = update.effective_user
    await update.effective_message.reply_text(
        "برای شروع، دستور /start را بزنید و از منو استفاده کنید.",
        reply_markup=keyboards.user_main_menu(user.id in ADMIN_IDS),
    )


def main():
    db.init_db()

    application = Application.builder().token(BOT_TOKEN).build()

    # --- دستورات ---
    application.add_handler(CommandHandler("start", user_handlers.start_command))
    application.add_handler(CommandHandler("admin", admin_command))

    # --- کاربر عادی ---
    application.add_handler(CallbackQueryHandler(user_handlers.back_main_callback, pattern=r"^back_main$"))
    application.add_handler(CallbackQueryHandler(user_handlers.check_join_callback, pattern=r"^check_join$"))
    application.add_handler(CallbackQueryHandler(user_handlers.menu_products_callback, pattern=r"^menu_products$"))
    application.add_handler(CallbackQueryHandler(user_handlers.menu_account_callback, pattern=r"^menu_account$"))
    application.add_handler(CallbackQueryHandler(user_handlers.menu_wallet_callback, pattern=r"^menu_wallet$"))
    application.add_handler(CallbackQueryHandler(user_handlers.menu_ticket_callback, pattern=r"^menu_ticket$"))
    application.add_handler(CallbackQueryHandler(user_handlers.category_callback, pattern=r"^cat_\d+$"))
    application.add_handler(CallbackQueryHandler(user_handlers.product_detail_callback, pattern=r"^prod_\d+$"))
    application.add_handler(CallbackQueryHandler(user_handlers.notify_callback, pattern=r"^notify_\d+$"))
    application.add_handler(CallbackQueryHandler(user_handlers.buy_callback, pattern=r"^buy_\d+$"))
    application.add_handler(CallbackQueryHandler(user_handlers.wallet_charge_callback, pattern=r"^wallet_charge$"))
    application.add_handler(CallbackQueryHandler(user_handlers.wallet_paid_callback, pattern=r"^wallet_paid$"))

    # --- ادمین: منوی اصلی ---
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_home_callback, pattern=r"^admin_home$"))

    # --- ادمین: دسته‌بندی‌ها ---
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_categories_callback, pattern=r"^admin_categories$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_addcat_callback, pattern=r"^admin_addcat$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_editcat_callback, pattern=r"^admin_editcat_\d+$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_setcat_callback, pattern=r"^admin_setcat_\d+$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_delcat_callback, pattern=r"^admin_delcat_\d+$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_delcat_confirm_callback, pattern=r"^admin_delcatY_\d+$"))

    # --- ادمین: محصولات ---
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_products_callback, pattern=r"^admin_products$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_prodcat_callback, pattern=r"^admin_prodcat_\d+$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_addprod_callback, pattern=r"^admin_addprod_\d+$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_prod_callback, pattern=r"^admin_prod_\d+$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_editname_callback, pattern=r"^admin_editname_\d+$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_editdesc_callback, pattern=r"^admin_editdesc_\d+$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_editprice_callback, pattern=r"^admin_editprice_\d+$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_stock_toggle_callback, pattern=r"^admin_stock(on|off)_\d+$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_delprod_callback, pattern=r"^admin_delprod_\d+$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_delprod_confirm_callback, pattern=r"^admin_delprodY_\d+$"))

    # --- ادمین: کاربران ---
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_users_callback, pattern=r"^admin_users$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_users_page_callback, pattern=r"^admin_users_page_\d+$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_user_detail_callback, pattern=r"^admin_user_\d+$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_setbalance_callback, pattern=r"^admin_setbalance_\d+$"))

    # --- ادمین: شماره کارت ---
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_card_callback, pattern=r"^admin_card$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_setcardnum_callback, pattern=r"^admin_setcardnum$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_setcardholder_callback, pattern=r"^admin_setcardholder$"))

    # --- ادمین: پشتیبانی ---
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_support_callback, pattern=r"^admin_support$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_setsupportid_callback, pattern=r"^admin_setsupportid$"))

    # --- ادمین: عضویت اجباری ---
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_forcejoin_callback, pattern=r"^admin_forcejoin$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_setforcejoin_callback, pattern=r"^admin_setforcejoin$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_toggleforcejoin_callback, pattern=r"^admin_toggleforcejoin$"))

    # --- ادمین: درخواست‌های شارژ ---
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_charges_callback, pattern=r"^admin_charges$"))
    application.add_handler(CallbackQueryHandler(admin_handlers.admin_charge_decision_callback, pattern=r"^admin_charge(ok|no)_\d+$"))

    # --- پیام متنی آزاد (بر اساس وضعیت) ---
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generic_text_handler))

    logger.info("ربات در حال اجراست...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
