import matplotlib.pyplot as plt
from db_handler import LOG_FILE
import datetime

def generate_dashboard(group_id):
    timestamps = []
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if f"در گروه {group_id}" in line:
                timestamp_str = line.split(']')[0][1:]
                dt = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                timestamps.append(dt)

    hours = [t.hour for t in timestamps]
    data = [hours.count(h) for h in range(24)]

    plt.figure(figsize=(10,4))
    plt.bar(range(24), data)
    plt.xlabel("ساعت روز")
    plt.ylabel("فعالیت کاربران")
    plt.title(f"داشبورد گروه {group_id}")
    img_path = f"dashboard_{group_id}.png"
    plt.savefig(img_path)
    plt.close()
    return img_path
