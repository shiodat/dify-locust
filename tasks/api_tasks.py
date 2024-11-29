from locust import TaskSet, task
import json
import os
from typing import Optional

class APITasks(TaskSet):
    """API共通処理とユーティリティ機能を提供するクラス"""
    
    def __init__(self, parent, api_key):
        super().__init__(parent)
        self.api_key = api_key
        self.user_id = f"test_user_{self.host}"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def get_parameters(self) -> Optional[dict]:
        """アプリケーション情報を取得"""
        with self.client.get(
            "/parameters",
            headers=self.headers,
            name="/parameters",
            params={"user": self.user_id}
        ) as response:
            if response.status_code == 200:
                return response.json()
            return None

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
            500: "Internal Server Error"
        }
        
        error_message = error_messages.get(status_code, "Unknown Error")
        response.failure(f"{task_name} failed: {error_message} ({status_code})")
        return None

    def _get_mime_type(self, file_path: str) -> str:
        """ファイルのMIMEタイプを取得"""
        mime_types = {
            '.txt': 'text/plain',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.mp4': 'video/mp4'
        }
        ext = os.path.splitext(file_path)[1].lower()
        return mime_types.get(ext, 'application/octet-stream')

    def check_rate_limits(self) -> bool:
        """レート制限のチェック"""
        with self.client.get(
            "/meta",
            headers=self.headers,
            name="/meta-rate-limit-check",
            catch_response=True
        ) as response:
            if response.status_code == 429:
                return False
            return True

    @task(1)
    def health_check(self):
        """API健全性チェック"""
        with self.client.get(
            "/parameters",
            headers=self.headers,
            name="/health-check",
            params={"user": self.user_id}
        ) as response:
            self.handle_response(response, "health_check")

    def log_error(self, task_name: str, error: Exception):
        """エラーログの記録"""
        error_message = f"{task_name} error: {str(error)}"
        print(error_message)  # 実際の環境では適切なロギング方法に置き換える
        
        # エラーメトリクスの記録
        self.environment.events.request_failure.fire(
            request_type="ERROR",
            name=task_name,
            response_time=0,
            exception=error
        )