"""
lake1 (Oracle ADB · AJD, 韩国区) MongoDB API 落库
==================================================
经 haproxy 100.93.5.81:27018 反代 → lake1 ADB MongoDB API (:27017 TLS)。
认证: authMechanism=PLAIN + authSource=$external（Oracle ADB 芒果 API 专用）。

注意: 该代理对源 IP 的突发新连接有限流（连续新建连接会被直接关闭），
因此这里使用进程级单例 MongoClient（长连接池）+ 退避重试，绝不每次新建。
落库为尽力而为（best-effort）：失败只告警，本地 擂台存档/ + MinIO 仍是权威存储。
"""

import logging
import os
import time

log = logging.getLogger("kunpengzhi")

LAKE1_MONGO_URI = os.environ.get(
    "LAKE1_MONGO_URI",
    "mongodb://admin:CZTqVMU9oMercE@100.93.5.81:27018/admin"
    "?authMechanism=PLAIN&authSource=%24external"
    "&loadBalanced=true&retryWrites=false&serverSelectionTimeoutMS=10000",
)
LANDING_DB = "default"
LANDING_COLLECTION = "landing"

_client_singleton = None


def _client():
    global _client_singleton
    if _client_singleton is None:
        from pymongo import MongoClient  # 延迟导入：轻量 CLI 路径不强制依赖
        _client_singleton = MongoClient(
            LAKE1_MONGO_URI,
            maxPoolSize=4,
            minPoolSize=0,
            connectTimeoutMS=10000,
            socketTimeoutMS=30000,
        )
    return _client_singleton


def upsert(doc_id: str, fields: dict, retries: int = 2) -> bool:
    """按 _id upsert 一条记录到 landing 集合。失败仅告警，返回是否成功。"""
    for attempt in range(retries):
        try:
            col = _client()[LANDING_DB][LANDING_COLLECTION]
            col.update_one({"_id": doc_id}, {"$set": fields}, upsert=True)
            return True
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            log.warning(f"Lake1 upsert {doc_id} 失败: {str(e)[:200]}")
            return False


def ping() -> dict:
    """连通性自检（供验证脚本使用）"""
    return _client().admin.command("ping")
