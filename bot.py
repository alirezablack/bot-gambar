import logging
from telebot import TeleBot, types
from ai_handler import process_ai_command
from db_handler import load_settings, save_settings, log_event, load_levels, save_levels, load_roles, save_roles
from analytics import generate_dashboard
import re
import random
from datetime import datetime, timedelta
import threading
import time

TOKEN = 'توکن_بات_تو'
bot = TeleBot(TOKEN)
logging.basicConfig(level=logging.INFO)

ROBOT_NAME = "قمبر"

# ================== بارگذاری داده‌ها ==================
settings = load_settings()
user_levels = load_levels()
roles = load_roles()

# ================== پنل تنظیمات ==================
def show_panel(chat_id, group_id):
    group_settings = settings.get(str(group_id), {})
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for key, value in group_settings.items():
        status = "✅ فعال" if value else "❌ غیرفعال"
        button = types.InlineKeyboardButton(f"{key} : {status}", callback_data=key)
        keyboard.add(button)
    bot.send_message(chat_id, "پنل تنظیمات گروه:", reply_markup=keyboard)

@bot.message_handler(commands=['panel'])
def panel_command(message):
    if message.from_user.id in roles.get(str(message.chat.id), {}).get("admins", []):
        show_panel(message.chat.id, message.chat.id)

@bot.callback_query_handler(func=lambda call: True)
def toggle_setting(call):
    group_settings = settings.get(str(call.message.chat.id), {})
    key = call.data
    if call.from_user.id not in roles.get(str(call.message.chat.id), {}).get("admins", []):
        bot.answer_callback_query(call.id, "شما دسترسی ندارید")
        return
    group_settings[key] = not group_settings.get(key, True)
    settings[str(call.message.chat.id)] = group_settings
    save_settings(settings)
    status = "✅ فعال" if group_settings[key] else "❌ غیرفعال"
    bot.answer_callback_query(call.id, f"{key} اکنون {status} است")
    show_panel(call.message.chat.id, call.message.chat.id)

# ================== مدیریت پیام‌ها ==================
@bot.message_handler(func=lambda m: True)
def handle_messages(message):
    group_id = str(message.chat.id)
    group_roles = roles.setdefault(group_id, {"admins": [], "vip": []})
    group_settings = settings.get(group_id, {})

    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    text = message.text or ""

    # ================== خوشامدگویی ==================
    if group_settings.get("welcome_msg") and hasattr(message, "new_chat_members"):
        for user in message.new_chat_members:
            bot.send_message(message.chat.id, f"خوش آمدی {user.first_name}!")

    # ================== سیستم لول ==================
    if group_id not in user_levels:
        user_levels[group_id] = {}
    if user_id not in user_levels[group_id]:
        user_levels[group_id][user_id] = {"messages": 0, "level": 0}

    user_levels[group_id][user_id]["messages"] += 1
    messages_count = user_levels[group_id][user_id]["messages"]
    current_level = user_levels[group_id][user_id]["level"]

    new_level = messages_count // 70
    if new_level > current_level:
        user_levels[group_id][user_id]["level"] = new_level
        save_levels(user_levels)
        bot.send_message(message.chat.id,
            f"@{username} خوش بحالت! سطحت شد Level {new_level} 🎉")

    # ================== دستورات مدیر روی کاربر ==================
    if message.reply_to_message and user_id in group_roles.get("admins", []):
        target = message.reply_to_message.from_user
        if text.startswith("بن"):
            bot.kick_chat_member(group_id, target.id)
            bot.send_message(group_id, f"کاربر @{target.username} بن شد 🚫")
        elif text.startswith("سکوت"):
            match = re.search(r"سکوت\s*(\d*)", text)
            minutes = int(match.group(1)) if match.group(1) else 0
            until = datetime.now() + timedelta(minutes=minutes) if minutes else None
            bot.restrict_chat_member(group_id, target.id, until_date=until, can_send_messages=False)
            bot.send_message(group_id, f"کاربر @{target.username} سکوت شد 🤫")
        elif text.startswith("افزودن مدیر"):
            if target.id not in group_roles["admins"]:
                group_roles["admins"].append(target.id)
                save_roles(roles)
                bot.send_message(group_id, f"کاربر @{target.username} مدیر شد ✅")
        elif text.startswith("حذف مدیر"):
            if target.id in group_roles["admins"]:
                group_roles["admins"].remove(target.id)
                save_roles(roles)
                bot.send_message(group_id, f"کاربر @{target.username} از مدیران حذف شد ❌")
        elif text.startswith("اعضای ویژه"):
            if target.id not in group_roles["vip"]:
                group_roles["vip"].append(target.id)
                save_roles(roles)
                bot.send_message(group_id, f"کاربر @{target.username} عضو ویژه شد ⭐")

    # ================== نمایش بزرگان گروه ==================
    if text.startswith("بزرگان گروه"):
        admins = [f"@{bot.get_chat_member(group_id, uid).user.username}" for uid in group_roles["admins"]]
        vip = [f"@{bot.get_chat_member(group_id, uid).user.username}" for uid in group_roles["vip"]]
        bot.send_message(group_id, f"مدیران: {', '.join(admins)}\nاعضای ویژه: {', '.join(vip)}")

    # ================== پاسخ به صدا شدن بات ==================
    if ROBOT_NAME in text:
        response_text = ""
        if user_id in group_roles.get("admins", []):
            response_text = f"جانم مدیر! دستور شما: {text}"
            bot.send_message(group_id, response_text)
        else:
            response_text = "بله، کاری دارید به مدیر اطلاع بدید ⚡"
            bot.send_message(group_id, response_text)

        # هوش مصنوعی با همه حرف بزنه
        if group_settings.get("ai_chat"):
            ai_response = process_ai_command(text, group_id)
            if ai_response:
                bot.send_message(group_id, ai_response)

    # ================== سرگرمی و بازی‌ها ==================
    if text.lower() == "/guess":
        number = random.randint(1, 10)
        bot.send_message(message.chat.id, "حدس بزن عدد بین 1 تا 10 چنده؟")
        bot.register_next_step_handler(message, lambda msg: guess_number(msg, number))

    if text.lower() == "/quiz":
        question, options, answer = generate_quiz()
        keyboard = types.InlineKeyboardMarkup()
        for opt in options:
            keyboard.add(types.InlineKeyboardButton(opt, callback_data=f"quiz_{opt}_{answer}"))
        bot.send_message(message.chat.id, question, reply_markup=keyboard)

    # ================== داشبورد تصویری ==================
    if user_id in group_roles.get("admins", []) and text.lower() == "/dashboard":
        img_path = generate_dashboard(group_id)
        bot.send_photo(message.chat.id, open(img_path, 'rb'))

# ================== بازی حدس عدد ==================
def guess_number(message, number):
    try:
        guess = int(message.text)
        if guess == number:
            bot.reply_to(message, f"آفرین! درست حدس زدی {number} 🎉")
        else:
            bot.reply_to(message, f"نه درست نبود، جواب درست {number} بود 😅")
    except:
        bot.reply_to(message, "لطفاً فقط عدد وارد کن.")

# ================== Callback کوییز ==================
@bot.callback_query_handler(func=lambda call: call.data.startswith("quiz_"))
def quiz_answer(call):
    parts = call.data.split("_")
    selected, correct = parts[1], parts[2]
    if selected == correct:
        bot.answer_callback_query(call.id, "درست جواب دادی! 🎉")
    else:
        bot.answer_callback_query(call.id, f"جواب درست: {correct} 😅")

# ================== تولید کوییز نمونه ==================
def generate_quiz():
    question = "پایتون در چه سالی معرفی شد؟"
    options = ["1991", "2000", "1985"]
    answer = "1991"
    return question, options, answer

# ================== مدیریت خودکار روزانه ==================
def daily_tasks():
    while True:
        time.sleep(24*60*60)  # هر 24 ساعت
        for group_id in roles.keys():
            group_roles = roles[group_id]
            user_ids = list(user_levels.get(group_id, {}).keys())
            if not user_ids:
                continue
            # انتخاب کاربر تصادفی برای چالش روزانه
            user_id = random.choice(user_ids)
            username = bot.get_chat_member(group_id, user_id).user.username
            bot.send_message(group_id, f"چالش روزانه برای @{username}: جواب درست را پیدا کن! 🏆")
            # جایزه خودکار: افزایش یک سطح
            if user_id in user_levels.get(group_id, {}):
                user_levels[group_id][user_id]["level"] += 1
                save_levels(user_levels)
                bot.send_message(group_id, f"تبریک @{username}! سطحت به دلیل برنده شدن چالش روزانه افزایش یافت 🌟")

threading.Thread(target=daily_tasks, daemon=True).start()

logging.info("Bot is running...")
bot.infinity_polling()
