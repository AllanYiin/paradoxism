
from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

# API 記錄模型
class ApiRecord(Base):
    __tablename__ = "api_records"
    id = Column(Integer, primary_key=True)
    user = Column(String, index=True)
    api_name = Column(String, index=True)
    route = Column(String, index=True)
    executed_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String)
    duration = Column(Float)  # 執行時間
    result = Column(Text)

# 排程任務模型
class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"
    id = Column(Integer, primary_key=True)
    user = Column(String, index=True)
    api_name = Column(String)
    cron_schedule = Column(String)  # Cron 格式排程
    last_executed = Column(DateTime, nullable=True)
