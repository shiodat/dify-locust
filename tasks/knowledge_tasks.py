import uuid
import time
from locust import TaskSet, task
import json


class KnowledgeTasks(TaskSet):
    """ナレッジベース関連APIのテストタスク"""

    def __init__(self, parent, api_key):
        super().__init__(parent)
        self.api = parent.api
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        self.dataset_id = None
        self.document_id = None
        self.segment_id = None
        self.batch_id = None

    @task(3)
    def create_knowledge_base(self):
        """空のナレッジベースを作成"""
        payload = {
            "name": str(uuid.uuid4()),
            "description": "Test description for load testing",
            "indexing_technique": "economy",
            "permission": "only_me",
            "provider": "vendor",
        }

        with self.client.post("/datasets", json=payload, headers=self.headers, name="Knowledge /datasets") as response:
            if response.status_code == 200:
                data = response.json()
                self.dataset_id = data.get("id")

    @task(3)
    def create_document_by_text(self):
        """テキストからドキュメントを作成"""
        if not self.dataset_id:
            return

        payload = {
            "name": "test_document.txt",
            "text": "This is a test document content for load testing purposes.",
            "indexing_technique": "economy",
            "process_rule": {"mode": "automatic"},
        }

        with self.client.post(
            f"/datasets/{self.dataset_id}/document/create-by-text",
            json=payload,
            headers=self.headers,
            name="Knowledge /datasets/:dataset_id/document/create-by-text",
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.document_id = data.get("document", {}).get("id")
                self.batch_id = data.get("batch")

    @task(2)
    def create_document_by_file(self):
        """ファイルからドキュメントを作成"""
        if not self.dataset_id:
            return

        file_path = "test_files/sample.txt"
        payload = {"indexing_technique": "high_quality", "process_rule": {"mode": "automatic"}}

        files = {
            "file": ("test.txt", open(file_path, "rb"), "text/plain"),
            "data": (None, json.dumps(payload), "application/json"),
        }

        with self.client.post(
            f"/datasets/{self.dataset_id}/document/create-by-file",
            files=files,
            headers={"Authorization": self.headers["Authorization"]},
            name="Knowledge /datasets/:dataset_id/document/create-by-file",
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.document_id = data.get("document", {}).get("id")
                self.batch_id = data.get("batch")

    @task(2)
    def get_documents(self):
        """ドキュメント一覧の取得"""
        if not self.dataset_id:
            return

        params = {"page": 1, "limit": 20, "keyword": ""}

        with self.client.get(
            f"/datasets/{self.dataset_id}/documents",
            params=params,
            headers=self.headers,
            name="Knowledge /datasets/:dataset_id/documents",
        ) as response:
            self.api.handle_response(response, "get_documents")

    @task(2)
    def check_indexing_status(self):
        """ドキュメントのインデックス状態確認"""
        if not all([self.dataset_id, self.batch_id]):
            return

        with self.client.get(
            f"/datasets/{self.dataset_id}/documents/{self.batch_id}/indexing-status",
            headers=self.headers,
            name="Knowledge /datasets/:dataset_id/documents/:batch_id/indexing-status",
        ) as response:
            self.api.handle_response(response, "check_indexing_status")

    def wait_for_indexing_complete(self):
        if not all([self.dataset_id, self.batch_id]):
            return True

        counter = 10
        while True:
            with self.client.get(
                f"/datasets/{self.dataset_id}/documents/{self.batch_id}/indexing-status",
                headers=self.headers,
                name="Knowledge /datasets/:dataset_id/documents/:batch_id/indexing-status",
            ) as response:
                if response.json()["data"][0]["indexing_status"] == "completed":
                    return True
                if counter > 10:
                    return False
                else:
                    counter += 1
                    time.sleep(1)

    @task(3)
    def retrieve_knowledge(self):
        """ナレッジベースからの情報検索"""
        if not self.dataset_id:
            return

        payload = {
            "query": "test",
            "retrieval_model": {
                "search_method": "keyword_search",
                "reranking_enable": False,
                "reranking_model": None,
                "top_k": 3,
                "score_threshold_enabled": False,
            },
        }

        with self.client.post(
            f"/datasets/{self.dataset_id}/retrieve",
            json=payload,
            headers=self.headers,
            name="Knowledge /datasets/:dataset_id/retrieve",
        ) as response:
            self.api.handle_response(response, "retrieve_knowledge")

    @task(1)
    def add_segments(self):
        """ドキュメントにチャンクを追加"""
        if not all([self.dataset_id, self.document_id]):
            return

        payload = {"segments": [{"content": "Test segment content", "keywords": ["test", "segment"]}]}

        with self.client.post(
            f"/datasets/{self.dataset_id}/documents/{self.document_id}/segments",
            json=payload,
            headers=self.headers,
            name="Knowledge /datasets/:dataset_id/documents/:document_id/segments",
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    self.segment_id = data["data"][0].get("id")

    @task(1)
    def delete_document(self):
        """ドキュメントの削除"""
        if not all([self.dataset_id, self.document_id]):
            return

        with self.client.delete(
            f"/datasets/{self.dataset_id}/documents/{self.document_id}",
            headers=self.headers,
            name="Knowledge /datasets/:dataset_id/documents/:document_id",
        ) as response:
            if response.status_code == 200:
                self.document_id = None
                self.segment_id = None

    @task(1)
    def delete_knowledge_base(self):
        """ナレッジベースの削除"""
        if not self.dataset_id:
            return

        with self.client.delete(
            f"/datasets/{self.dataset_id}", headers=self.headers, name="Knowledge /datasets/:dataset_id"
        ) as response:
            if response.status_code == 204:
                self.dataset_id = None
                self.document_id = None
                self.segment_id = None

    def perform_knowledge_tasks(self):
        """ナレッジベース操作タスクの一連の実行"""
        try:
            # ナレッジベース作成
            if not self.dataset_id:
                self.create_knowledge_base()

            if self.dataset_id:
                # ドキュメント作成
                if self.user.environment.runner.user_count % 2 == 0:
                    self.create_document_by_text()
                else:
                    self.create_document_by_file()

                # インデックス状態確認
                self.check_indexing_status()

                if self.batch_id:
                    self.wait_for_indexing_complete()

                # インデックス状態確認
                self.check_indexing_status()

                # 情報検索
                self.retrieve_knowledge()

                # セグメント操作
                if self.document_id:
                    self.add_segments()

                # 一定確率でクリーンアップ
                if self.user.environment.runner.user_count > 10:
                    self.delete_document()
                    self.delete_knowledge_base()

        except Exception as e:
            self.api.log_error("knowledge_tasks", e)
