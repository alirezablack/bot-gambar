import openai
import logging
from db_handler import log_event

openai.api_key = 'کلید_API_تو'
GROUP_MEMORY = {}

def process_ai_command(prompt, group_id):
    if not prompt:
        return None
    if group_id not in GROUP_MEMORY:
        GROUP_MEMORY[group_id] = []
    GROUP_MEMORY[group_id].append(prompt)
    if len(GROUP_MEMORY[group_id]) > 50:
        GROUP_MEMORY[group_id].pop(0)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role":"system","content":"تو یک بات تلگرام هوشمند هستی که با کاربران و مدیران گروه حرف می‌زنی، سرگرمی و تحلیل را اجرا می‌کنی و دستور مدیر را اعمال می‌کنی."},
                {"role":"user","content": prompt}
            ],
            max_tokens=300
        )
        reply = response.choices[0].message['content']
        log_event(f"AI پاسخ داد در گروه {group_id}: {reply}")
        return reply
    except Exception as e:
        logging.error(f"AI Error: {e}")
        return "مشکل در پردازش دستور هوش مصنوعی پیش آمد."
