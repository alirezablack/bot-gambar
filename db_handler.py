import json
import logging
from datetime import datetime

DATA_FILE = 'settings.json'
LOG_FILE = 'bot_logs.txt'
LEVELS_FILE = 'user_levels.json'
ROLES_FILE = 'roles.json'

def load_settings():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"default":{"anti_spam": True, "auto_delete_links": True, "welcome_msg": True, "ai_chat": True}}

def save_settings(settings):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def log_event(text):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {text}\n")
    logging.info(text)

def load_levels():
    try:
        with open(LEVELS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_levels(levels):
    with open(LEVELS_FILE, 'w', encoding='utf-8') as f:
        json.dump(levels, f, ensure_ascii=False, indent=4)

def load_roles():
    try:
        with open(ROLES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_roles(roles):
    with open(ROLES_FILE, 'w', encoding='utf-8') as f:
        json.dump(roles, f, ensure_ascii=False, indent=4)
