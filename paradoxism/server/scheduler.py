from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from db import add_api_record, SessionLocal, add_scheduled_task
from models import ScheduledTask
from sqlalchemy.orm import Session
import time
import logging

scheduler = BackgroundScheduler()
scheduler.start()


# 添加排程任務
def schedule_task(user, api_name, func, cron_schedule):
    db = SessionLocal()

    # 添加排程任務到 APScheduler
    trigger = CronTrigger.from_crontab(cron_schedule)
    job_id = f"{user}_{api_name}_task"

    # 確認是否已經有此排程，避免重複
    if scheduler.get_job(job_id):
        logging.info("排程任務 %s 已存在，跳過創建。", job_id)
        return

    scheduler.add_job(
        func=lambda: execute_task(user, api_name, func),
        trigger=trigger,
        id=job_id,
        replace_existing=True
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


# 在啟動時重新加載排程任務
def load_scheduled_tasks():
    db = SessionLocal()
    tasks = db.query(ScheduledTask).all()
    for task in tasks:
        # 假設已加載 API 函數作為動態路由的一部分
        func = get_api_function(task.user, task.api_name)
        if func:
            schedule_task(task.user, task.api_name, func, task.cron_schedule)


# 載入 API 函數的方法 (假設已有此方法)
def get_api_function(user, api_name):
    route_path = f"/{user}/{api_name}"
    return dynamic_routes.get(route_path)