import os
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()


class Config:
    # API設定
    API_HOST = os.environ["API_HOST"]
    SANDBOX_HOST = os.environ["SANDBOX_HOST"]

    CHATFLOW_API_KEY = os.environ["CHATFLOW_API_KEY"]
    WORKFLOW_API_KEY = os.environ["WORKFLOW_API_KEY"]
    KNOWLEDGE_API_KEY = os.environ["KNOWLEDGE_API_KEY"]
    SANDBOX_API_KEY = os.environ["SANDBOX_API_KEY"]

    # テスト設定
    LOAD_TEST = {"users": {"api": 100, "sandbox": 50}, "spawn_rate": 10, "duration": "30m"}

    # パフォーマンス要件
    PERFORMANCE = {
        "response_time_95": 1000,  # ms
        "response_time_99": 2000,  # ms
        "error_rate": 0.001,  # 0.1%
        "min_rps": 100,  # requests per second
    }

    # システムリソース制限
    RESOURCES = {"cpu_limit": 80, "memory_limit": 85, "disk_io_limit": 70}  # percent  # percent  # percent
