# -*- coding: utf-8 -*-
"""
مدیریت وضعیت مکالمه (Conversation State) به صورت ساده و در حافظه.
برای هر کاربر مشخص می‌کند که ربات منتظر چه ورودی متنی از او هست.
"""

_states = {}


def set_state(telegram_id, action, data=None):
    _states[telegram_id] = {"action": action, "data": data or {}}


def get_state(telegram_id):
    return _states.get(telegram_id)


def clear_state(telegram_id):
    _states.pop(telegram_id, None)
