
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from db import add_api_record, SessionLocal
import time

scheduler = BackgroundScheduler()
scheduler.start()

# 添加排程任務
def schedule_task(user, api_name, func, cron_schedule):
    db = SessionLocal()
    trigger = CronTrigger.from_crontab(cron_schedule)
    scheduler.add_job(
        func=lambda: execute_task(user, api_name, func),
        trigger=trigger,
        id=f"{user}_{api_name}_task"
    )
    # 保存排程任務到資料庫
    add_scheduled_task(db, user, api_name, cron_schedule)

# 執行排程任務並記錄
def execute_task(user, api_name, func):
    db = SessionLocal()
    start_time = time.time()
    try:
        result = func()
        duration = time.time() - start_time
        add_api_record(db, user, api_name, f"/{user}/{api_name}", "Success", duration, str(result))
    except Exception as e:
        duration = time.time() - start_time
        add_api_record(db, user, api_name, f"/{user}/{api_name}", "Failed", duration, str(e))
