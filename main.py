# -*- coding: utf-8 -*-
"""
فایل اصلی اجرای ربات فروشگاهی.
تمام هندلرهای کاربر و ادمین را ثبت و ربات را اجرا می‌کند.
"""

import logging

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import db
import state
import keyboards
import user_handlers as uh
import admin_handlers as ah
from config import BOT_TOKEN

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("shop_bot")


# ---------------------------------------------------------------------------
# هندلر متن آزاد (پیام‌های معمولی کاربر که در حالت انتظار ورودی هستند)
# ---------------------------------------------------------------------------

async def text_message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ابتدا بررسی می‌کند آیا پیام مربوط به یک state ادمین است یا کاربر عادی."""
    if not update.message or not update.message.text:
        return
    user = update.effective_user

    # اگر ادمین در حالت انتظار ورودی خاص ادمین است، اول آنجا بررسی شود
    if ah.is_admin(user.id):
        handled = await ah.admin_text_router(update, context)
        if handled:
            return

    await uh.user_text_router(update, context)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.exception("خطای پیش‌بینی‌نشده در پردازش آپدیت: %s", context.error)


def build_application() -> Application:
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # --- دستورات ---
    app.add_handler(CommandHandler("start", uh.start_command))

    # --- کاربر عادی ---
    app.add_handler(CallbackQueryHandler(uh.check_join_callback, pattern=r"^check_join$"))
    app.add_handler(CallbackQueryHandler(uh.back_main_callback, pattern=r"^back_main$"))
    app.add_handler(CallbackQueryHandler(uh.menu_products_callback, pattern=r"^menu_products$"))
    app.add_handler(CallbackQueryHandler(uh.category_callback, pattern=r"^cat_\d+$"))
    app.add_handler(CallbackQueryHandler(uh.product_detail_callback, pattern=r"^prod_\d+$"))
    app.add_handler(CallbackQueryHandler(uh.notify_callback, pattern=r"^notify_\d+$"))
    app.add_handler(CallbackQueryHandler(uh.buy_callback, pattern=r"^buy_\d+$"))
    app.add_handler(CallbackQueryHandler(uh.menu_account_callback, pattern=r"^menu_account$"))
    app.add_handler(CallbackQueryHandler(uh.menu_referral_callback, pattern=r"^menu_referral$"))
    app.add_handler(CallbackQueryHandler(uh.menu_spin_callback, pattern=r"^menu_spin$"))
    app.add_handler(CallbackQueryHandler(uh.menu_wallet_callback, pattern=r"^menu_wallet$"))
    app.add_handler(CallbackQueryHandler(uh.wallet_charge_callback, pattern=r"^wallet_charge$"))
    app.add_handler(CallbackQueryHandler(uh.wallet_paid_callback, pattern=r"^wallet_paid$"))
    app.add_handler(CallbackQueryHandler(uh.wallet_history_callback, pattern=r"^wallet_history$"))
    app.add_handler(CallbackQueryHandler(uh.wallet_coupon_callback, pattern=r"^wallet_coupon$"))
    app.add_handler(CallbackQueryHandler(uh.menu_search_callback, pattern=r"^menu_search$"))
    app.add_handler(CallbackQueryHandler(uh.menu_ticket_callback, pattern=r"^menu_ticket$"))

    # --- ادمین: خانه و دسته‌بندی‌ها ---
    app.add_handler(CallbackQueryHandler(ah.admin_home_callback, pattern=r"^admin_home$"))
    app.add_handler(CallbackQueryHandler(ah.admin_categories_callback, pattern=r"^admin_categories$"))
    app.add_handler(CallbackQueryHandler(ah.admin_addcat_callback, pattern=r"^admin_addcat$"))
    app.add_handler(CallbackQueryHandler(ah.admin_newcat_special_callback, pattern=r"^admin_newcat_special_(yes|no)$"))
    app.add_handler(CallbackQueryHandler(ah.admin_setcat_callback, pattern=r"^admin_setcat_\d+$"))
    app.add_handler(CallbackQueryHandler(ah.admin_delcat_confirm_callback, pattern=r"^admin_delcatY_\d+$"))
    app.add_handler(CallbackQueryHandler(ah.admin_delcat_callback, pattern=r"^admin_delcat_\d+$"))
    app.add_handler(CallbackQueryHandler(ah.admin_editcat_callback, pattern=r"^admin_editcat_\d+$"))

    # --- ادمین: محصولات ---
    app.add_handler(CallbackQueryHandler(ah.admin_products_callback, pattern=r"^admin_products$"))
    app.add_handler(CallbackQueryHandler(ah.admin_addprod_callback, pattern=r"^admin_addprod_\d+$"))
    app.add_handler(CallbackQueryHandler(ah.admin_prodcat_callback, pattern=r"^admin_prodcat_\d+$"))
    app.add_handler(CallbackQueryHandler(ah.admin_editname_callback, pattern=r"^admin_editname_\d+$"))
    app.add_handler(CallbackQueryHandler(ah.admin_editdesc_callback, pattern=r"^admin_editdesc_\d+$"))
    app.add_handler(CallbackQueryHandler(ah.admin_editprice_callback, pattern=r"^admin_editprice_\d+$"))
    app.add_handler(CallbackQueryHandler(ah.admin_stock_toggle_callback, pattern=r"^admin_stock(on|off)_\d+$"))
    app.add_handler(CallbackQueryHandler(ah.admin_delprod_confirm_callback, pattern=r"^admin_delprodY_\d+$"))
    app.add_handler(CallbackQueryHandler(ah.admin_delprod_callback, pattern=r"^admin_delprod_\d+$"))
    app.add_handler(CallbackQueryHandler(ah.admin_prod_callback, pattern=r"^admin_prod_\d+$"))

    # --- ادمین: کاربران، پیام مستقیم و آمار ---
    app.add_handler(CallbackQueryHandler(ah.admin_users_callback, pattern=r"^admin_users$"))
    app.add_handler(CallbackQueryHandler(ah.admin_users_page_callback, pattern=r"^admin_users_page_\d+$"))
    app.add_handler(CallbackQueryHandler(ah.admin_setbalance_callback, pattern=r"^admin_setbalance_\d+$"))
    app.add_handler(CallbackQueryHandler(ah.admin_replyuser_callback, pattern=r"^admin_replyuser_\d+$"))
    app.add_handler(CallbackQueryHandler(ah.admin_user_detail_callback, pattern=r"^admin_user_\d+$"))
    app.add_handler(CallbackQueryHandler(ah.admin_stats_callback, pattern=r"^admin_stats$"))

    # --- ادمین: کارت، پشتیبانی، عضویت اجباری ---
    app.add_handler(CallbackQueryHandler(ah.admin_card_callback, pattern=r"^admin_card$"))
    app.add_handler(CallbackQueryHandler(ah.admin_setcardnum_callback, pattern=r"^admin_setcardnum$"))
    app.add_handler(CallbackQueryHandler(ah.admin_setcardholder_callback, pattern=r"^admin_setcardholder$"))
    app.add_handler(CallbackQueryHandler(ah.admin_support_callback, pattern=r"^admin_support$"))
    app.add_handler(CallbackQueryHandler(ah.admin_setsupportid_callback, pattern=r"^admin_setsupportid$"))
    app.add_handler(CallbackQueryHandler(ah.admin_forcejoin_callback, pattern=r"^admin_forcejoin$"))
    app.add_handler(CallbackQueryHandler(ah.admin_setforcejoin_callback, pattern=r"^admin_setforcejoin$"))
    app.add_handler(CallbackQueryHandler(ah.admin_toggleforcejoin_callback, pattern=r"^admin_toggleforcejoin$"))

    # --- ادمین: شارژ کیف پول ---
    app.add_handler(CallbackQueryHandler(ah.admin_charges_callback, pattern=r"^admin_charges$"))
    app.add_handler(CallbackQueryHandler(ah.admin_charge_decision_callback, pattern=r"^admin_charge(ok|no)_\d+$"))

    # --- ادمین: پیام همگانی ---
    app.add_handler(CallbackQueryHandler(ah.admin_broadcast_callback, pattern=r"^admin_broadcast$"))
    app.add_handler(CallbackQueryHandler(ah.admin_broadcast_send_callback, pattern=r"^admin_broadcast_send$"))
    app.add_handler(CallbackQueryHandler(ah.admin_broadcast_cancel_callback, pattern=r"^admin_broadcast_cancel$"))

    # --- ادمین: کدهای تخفیف (دقت شود admin_coupons از admin_coupon_ متمایز است) ---
    app.add_handler(CallbackQueryHandler(ah.admin_coupons_callback, pattern=r"^admin_coupons$"))
    app.add_handler(CallbackQueryHandler(ah.admin_addcoupon_callback, pattern=r"^admin_addcoupon$"))
    app.add_handler(CallbackQueryHandler(ah.admin_delcoupon_callback, pattern=r"^admin_delcoupon_.+$"))
    app.add_handler(CallbackQueryHandler(ah.admin_coupon_detail_callback, pattern=r"^admin_coupon_.+$"))

    # --- پیام‌های متنی آزاد (بر اساس state) ---
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_router))

    app.add_error_handler(on_error)
    return app


def main():
    db.init_db()
    app = build_application()
    log.info("ربات در حال اجراست...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
