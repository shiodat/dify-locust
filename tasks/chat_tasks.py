from locust import TaskSet, task
import json
import time
from typing import Optional

class ChatTasks(TaskSet):
    """チャット関連APIのテストタスク"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.conversation_id = None
        self.message_id = None
        self.api = parent.api  # APITasksのインスタンス

    @task(3)
    def send_chat_message(self):
        """チャットメッセージの送信テスト"""
        payload = {
            "inputs": {},
            "query": "What time is it now?",
            "response_mode": "streaming",  # blocking or streaming
            "conversation_id": self.conversation_id,
            "user": self.api.user_id,
            "files": []  # ファイル添付がある場合に使用
        }
        
        with self.client.post(
            "/chat-messages",
            json=payload,
            headers=self.api.headers,
            name="/chat-messages/send",
            stream=True
        ) as response:
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line.decode('utf-8').replace('data: ', ''))
                        if data.get('conversation_id'):
                            self.conversation_id = data['conversation_id']
                        if data.get('message_id'):
                            self.message_id = data['message_id']

    def stop_generation(self, task_id: str) -> bool:
        """生成処理の停止"""
        payload = {"user": self.user_id}
        with self.client.post(
            f"/chat-messages/{task_id}/stop",
            headers=self.headers,
            name="/chat-messages/stop",
            json=payload
        ) as response:
            return response.status_code == 200

    @task(2)
    def get_chat_history(self):
        """チャット履歴の取得テスト"""
        if not self.conversation_id:
            return
        
        params = {
            "user": self.api.user_id,
            "conversation_id": self.conversation_id,
            "first_id": None,
            "limit": 20
        }
        
        with self.client.get(
            "/messages",
            params=params,
            headers=self.api.headers,
            name="/messages/history"
        ) as response:
            self.api.handle_response(response, "get_chat_history")

    @task(2)
    def get_suggested_questions(self):
        """推奨質問の取得テスト"""
        if not self.message_id:
            return
            
        params = {
            "user": self.api.user_id
        }
        
        with self.client.get(
            f"/messages/{self.message_id}/suggested",
            params=params,
            headers=self.api.headers,
            name="/messages/suggested"
        ) as response:
            self.api.handle_response(response, "get_suggested_questions")

    @task(1)
    def send_message_feedback(self):
        """メッセージフィードバックのテスト"""
        if not self.message_id:
            return

        payload = {
            "rating": "like",  # like or dislike
            "user": self.api.user_id
        }
        
        with self.client.post(
            f"/messages/{self.message_id}/feedbacks",
            json=payload,
            headers=self.api.headers,
            name="/messages/feedback"
        ) as response:
            self.api.handle_response(response, "send_message_feedback")

    @task(1)
    def rename_conversation(self):
        """会話名の変更テスト"""
        if not self.conversation_id:
            return
            
        payload = {
            "name": f"Test Conversation {time.time()}",
            "user": self.api.user_id,
            "auto_generate": False
        }
        
        with self.client.post(
            f"/conversations/{self.conversation_id}/name",
            json=payload,
            headers=self.api.headers,
            name="/conversations/rename"
        ) as response:
            self.api.handle_response(response, "rename_conversation")

    @task(1)
    def delete_conversation(self):
        """会話の削除テスト"""
        if not self.conversation_id:
            return
            
        payload = {
            "user": self.api.user_id
        }
        
        with self.client.delete(
            f"/conversations/{self.conversation_id}",
            json=payload,
            headers=self.api.headers,
            name="/conversations/delete"
        ) as response:
            if response.status_code == 200:
                self.conversation_id = None
                self.message_id = None

    def _stream_processor(self, response) -> dict:
        """ストリーミングレスポンスの処理"""
        full_response = {"events": []}
        
        for line in response.iter_lines():
            if line:
                try:
                    event_data = json.loads(line.decode('utf-8').replace('data: ', ''))
                    full_response["events"].append(event_data)
                    
                    if event_data.get("event") == "message_end":
                        break
                        
                except json.JSONDecodeError:
                    continue
                
        return full_response

    def get_meta(self) -> Optional[dict]:
        """アプリケーションのメタ情報を取得"""
        with self.client.get(
            "/meta",
            headers=self.headers,
            name="/meta",
            params={"user": self.user_id}
        ) as response:
            if response.status_code == 200:
                return response.json()
            return None

    def perform_chat_tasks(self):
        """チャットタスクの一連の実行"""
        try:
            # メッセージ送信
            self.send_chat_message()
            
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
                if self.environment.runner.user_count > 10:
                    self.delete_conversation()
                    
        except Exception as e:
            self.api.log_error("chat_tasks", e)