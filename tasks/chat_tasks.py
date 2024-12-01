from locust import TaskSet, task
import json
import time
from typing import Optional


class ChatTasks(TaskSet):
    """チャット関連APIのテストタスク"""

    def __init__(self, parent, api_key):
        super().__init__(parent)
        self.api = parent.api  # APITasksのインスタンス
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        self.conversation_id = None
        self.message_id = None

    def _send_chat_message(self, response_mode: str):
        """チャットメッセージの送信テスト"""
        assert response_mode in ["streaming", "blocking"]
        payload = {
            "inputs": {},
            "query": "What time is it now?",
            "response_mode": response_mode,  # blocking or streaming
            "conversation_id": self.conversation_id,
            "user": self.api.user_id,
            "files": [],  # ファイル添付がある場合に使用
        }

        with self.client.post(
            "/chat-messages",
            json=payload,
            headers=self.headers,
            name="/chat-messages/send",
            stream=(response_mode == "streaming"),
        ) as response:
            if response.status_code == 200:
                if response_mode == "streaming":
                    self.conversation_id, self.message_id = self._stream_processor(response)
                else:  # blocking mode
                    data = response.json()
                    if data.get("conversation_id"):
                        self.conversation_id = data["conversation_id"]
                    if data.get("message_id"):
                        self.message_id = data["message_id"]

    def _stream_processor(self, response) -> dict:
        """ストリーミングレスポンスの処理"""
        conversation_id = None
        message_id = None

        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode("utf-8").replace("data: ", ""))
                    if data.get("event") == "message_end":
                        break
                    if data.get("event") == "message":
                        conversation_id = data["conversation_id"]
                        message_id = data["message_id"]
                except json.JSONDecodeError:
                    continue

        return conversation_id, message_id

    @task(3)
    def send_chat_message_streaming(self):
        return self._send_chat_message("streaming")

    @task(1)
    def send_chat_message_blocking(self):
        return self._send_chat_message("blocking")

    @task(2)
    def get_chat_history(self):
        """チャット履歴の取得テスト"""
        if not self.conversation_id:
            return

        params = {"user": self.api.user_id, "conversation_id": self.conversation_id, "first_id": None, "limit": 20}

        with self.client.get("/messages", params=params, headers=self.headers, name="/messages/history") as response:
            self.api.handle_response(response, "get_chat_history")

    @task(2)
    def get_suggested_questions(self):
        """推奨質問の取得テスト"""
        if not self.message_id:
            return

        params = {"user": self.api.user_id}

        with self.client.get(
            f"/messages/{self.message_id}/suggested",
            params=params,
            headers=self.headers,
            name="/messages/suggested",
        ) as response:
            self.api.handle_response(response, "get_suggested_questions")

    @task(1)
    def send_message_feedback(self):
        """メッセージフィードバックのテスト"""
        if not self.message_id:
            return

        payload = {"rating": "like", "user": self.api.user_id}  # like or dislike

        with self.client.post(
            f"/messages/{self.message_id}/feedbacks", json=payload, headers=self.headers, name="/messages/feedback"
        ) as response:
            self.api.handle_response(response, "send_message_feedback")

    @task(2)
    def get_conversation_history(self):
        """会話履歴の取得テスト"""
        if not self.conversation_id:
            return

        params = {"user": self.api.user_id, "last_id": None, "limit": 20}

        with self.client.get(
            "/conversations", params=params, headers=self.headers, name="/messages/history"
        ) as response:
            self.api.handle_response(response, "get_conversation_history")

    @task(1)
    def rename_conversation(self):
        """会話名の変更テスト"""
        if not self.conversation_id:
            return

        payload = {"name": f"Test Conversation {time.time()}", "user": self.api.user_id, "auto_generate": False}

        with self.client.post(
            f"/conversations/{self.conversation_id}/name",
            json=payload,
            headers=self.headers,
            name="/conversations/rename",
        ) as response:
            self.api.handle_response(response, "rename_conversation")

    @task(1)
    def delete_conversation(self):
        """会話の削除テスト"""
        if not self.conversation_id:
            return

        payload = {"user": self.api.user_id}

        with self.client.delete(
            f"/conversations/{self.conversation_id}",
            json=payload,
            headers=self.headers,
            name="/conversations/delete",
        ) as response:
            if response.status_code == 200:
                self.conversation_id = None
                self.message_id = None

    @task(1)
    def get_parameters(self) -> Optional[dict]:
        """アプリケーション情報を取得"""
        with self.client.get(
            "/parameters", headers=self.headers, name="/parameters", params={"user": self.api.user_id}
        ) as response:
            if response.status_code == 200:
                return response.json()
            return None

    @task(1)
    def get_meta(self) -> Optional[dict]:
        """アプリケーションのメタ情報を取得"""
        with self.client.get(
            "/meta", headers=self.headers, name="/meta", params={"user": self.api.user_id}
        ) as response:
            if response.status_code == 200:
                return response.json()
            return None

    def perform_chat_tasks(self):
        """チャットタスクの一連の実行"""
        try:
            # データ確認
            self.get_parameters()
            self.get_meta()

            # メッセージ送信
            if self.user.environment.runner.user_count % 5 == 0:
                self.send_chat_message_blocking()
            else:
                self.send_chat_message_streaming()

            if self.conversation_id:
                # 履歴取得
                self.get_chat_history()

                if self.message_id:
                    # フィードバック送信
                    self.send_message_feedback()
                    # 推奨質問取得
                    self.get_suggested_questions()

                # 会話名変更
                self.rename_conversation()

                # 一定確率で会話を削除
                if self.user.environment.runner.user_count > 10:
                    self.delete_conversation()

        except Exception as e:
            self.api.log_error("chat_tasks", e)
