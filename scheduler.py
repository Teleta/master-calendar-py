"""Модуль планировщика: помещает задачи в свободные слоты в течение недели.
Логика: жадное размещение задач по времени.
"""
from datetime import datetime, timedelta
from collections import defaultdict
import db


def build_week_schedule(user_id: int):
    tasks = db.get_tasks(user_id)
    busy_rows = db.get_busy(user_id)

    # Преобразуем busy в удобный формат
    busy_slots = []
    for r in busy_rows:
        busy_slots.append({
            "label": r["label"],
            "start": datetime.fromtimestamp(r["start_ts"]),
            "end": datetime.fromtimestamp(r["end_ts"]),
        })

    schedule = defaultdict(list)
    today = datetime.now().date()

    # Получаем пользовательские рабочие часы
    start_hour, end_hour = db.get_user_hours(user_id)

    # Добавляем busy в расписание для следующей недели
    for slot in busy_slots:
        day_date = slot["start"].date()
        if day_date >= today and day_date < today + timedelta(days=7):
            schedule[day_date].append({
                "type": "busy",
                "label": slot["label"],
                "start": slot["start"],
                "end": slot["end"],
            })

    pending_tasks = [t.copy() for t in tasks]

    for i in range(7):
        current_date = today + timedelta(days=i)
        day_items = schedule.get(current_date, [])
        all_day = datetime.combine(current_date, datetime.min.time())
        free_slots = [(all_day.replace(hour=start_hour), all_day.replace(hour=end_hour))]

        # вычитаем busy
        for busy in day_items:
            new_free = []
            for fs, fe in free_slots:
                if busy["start"] <= fs and busy["end"] >= fe:
                    # busy полностью занимает свободный слот
                    continue
                if busy["start"] <= fs < busy["end"] < fe:
                    new_free.append((busy["end"], fe))
                elif fs < busy["start"] < fe <= busy["end"]:
                    new_free.append((fs, busy["start"]))
                elif fs < busy["start"] and busy["end"] < fe:
                    new_free.append((fs, busy["start"]))
                    new_free.append((busy["end"], fe))
                else:
                    new_free.append((fs, fe))
            free_slots = new_free

        # размещаем задачи жадно
        for fs, fe in free_slots:
            free_minutes = int((fe - fs).total_seconds() / 60)
            # работаем по копии списка, чтобы можно было удалять
            for task in list(pending_tasks):
                needed = int(task["duration_hours"] * 60)
                if needed <= free_minutes:
                    task_end = fs + timedelta(hours=task["duration_hours"])
                    schedule[current_date].append({
                        "type": "task",
                        "label": task["label"],
                        "start": fs,
                        "end": task_end,
                    })
                    fs = task_end
                    free_minutes = int((fe - fs).total_seconds() / 60)
                    pending_tasks.remove(task)

    return schedule