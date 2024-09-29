import time
import uuid
import hashlib
import logging
from functools import wraps
from typing import Callable


# 設定 logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


class PerformanceCollector:
    """效能數據收集器，用於統一處理效能數據的記錄和上報。"""

    _instance = None  # 類級變數，用於儲存單例實例

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PerformanceCollector, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "data"):
            self.data = []  # 暫存收集到的效能數據

    def record(self, instance_id: str, agent_key: str, exec_time: float):
        """記錄效能數據"""
        self.data.append({"instance_id": instance_id, "agent_key": agent_key, "execution_time": exec_time})
        logger.info(
            f"Recorded performance: Instance: {instance_id}, Agent Key: {agent_key}, Execution time: {exec_time:.4f} seconds")

    def flush(self):
        """將數據持久化或上報到遠端服務"""
        logger.info("Flushing performance data to storage or remote server.")
        # 這裡可以實作將 self.data 寫入數據庫或發送到遠端
        self.data.clear()


# 建立全域的 PerformanceCollector 實例，保證所有地方都能使用這個實例
collector = PerformanceCollector()
