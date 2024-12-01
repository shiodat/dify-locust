from locust import TaskSet, task
import json
import os
from typing import Optional


class APITasks(TaskSet):
    """API共通処理とユーティリティ機能を提供するクラス"""

    def __init__(self, parent):
        super().__init__(parent)
        self.user_id = f"test_user_{parent.host}"

    def handle_response(self, response, task_name: str) -> Optional[dict]:
        """API応答の共通ハンドリング"""
        status_code = response.status_code

        # 成功レスポンスの処理
        if 200 <= status_code < 300:
            try:
                return response.json()
            except json.JSONDecodeError:
                response.failure(f"Invalid JSON response in {task_name}")
                return None

        # エラーレスポンスの処理
        error_messages = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            429: "Too Many Requests",
            500: "Internal Server Error",
        }

        error_message = error_messages.get(status_code, "Unknown Error")
        response.failure(f"{task_name} failed: {error_message} ({status_code})")
        return None

    def log_error(self, task_name: str, error: Exception):
        """エラーログの記録"""
        error_message = f"{task_name} error: {str(error)}"
        print(error_message)

        # エラーメトリクスの記録
        self.user.environment.events.request.fire(
            request_type="ERROR",
            name=task_name,
            response_time=0,
            response_length=0,
            exception=error,
            context={},  # 追加のコンテキスト情報が必要な場合
            user=self.user,
        )

    @task(1)
    def health_check(self):
        """API健全性チェック"""
        with self.client.get("/", name="/health-check") as response:
            self.handle_response(response, "health_check")
