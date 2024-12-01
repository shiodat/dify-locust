from locust import TaskSet, task
import json
import time
from typing import Optional


class WorkflowTasks(TaskSet):
    """ワークフロー関連APIのテストタスク"""

    def __init__(self, parent, api_key):
        super().__init__(parent)
        self.api = parent.api
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        self.workflow_id = None
        self.task_id = None

    @task(3)
    def run_workflow_blocking(self):
        """シンプルなワークフローの実行"""
        payload = {"inputs": {"query": "Simple workflow test"}, "response_mode": "blocking", "user": self.api.user_id}

        with self.client.post(
            "/workflows/run", json=payload, headers=self.headers, name="/workflows/run/simple"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.workflow_id = data.get("workflow_run_id")
                self.task_id = data.get("task_id")

    @task(2)
    def run_workflow_streaming(self):
        """ストリーミングモードでのワークフロー実行"""
        payload = {
            "inputs": {"query": "Streaming workflow test"},
            "response_mode": "streaming",
            "user": self.api.user_id,
        }

        with self.client.post(
            "/workflows/run", json=payload, headers=self.headers, name="/workflows/run/streaming", stream=True
        ) as response:
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line.decode("utf-8").replace("data: ", ""))
                        if data.get("event") == "workflow_started":
                            self.workflow_id = data.get("workflow_run_id")
                            self.task_id = data.get("task_id")

    @task(2)
    def get_workflow_status(self):
        """ワークフロー実行状態の取得"""
        if not self.workflow_id:
            return

        with self.client.get(
            f"/workflows/run/{self.workflow_id}", headers=self.headers, name="Workflow /workflows/run/:workflow_id"
        ) as response:
            self.api.handle_response(response, "get_workflow_status")

    @task(2)
    def get_workflow_logs(self):
        """ワークフローログの取得"""
        params = {"page": 1, "limit": 20, "keyword": "", "status": "succeeded"}  # succeeded/failed/stopped

        with self.client.get(
            "/workflows/logs", params=params, headers=self.headers, name="/workflows/logs"
        ) as response:
            self.api.handle_response(response, "get_workflow_logs")

    @task(1)
    def stop_workflow(self):
        """ワークフロー実行の停止"""
        if not self.task_id:
            return

        payload = {"user": self.api.user_id}

        with self.client.post(
            f"/workflows/tasks/{self.task_id}/stop",
            json=payload,
            headers=self.headers,
            name="Workflow /workflows/tasks/:task_id/stop",
        ) as response:
            if response.status_code == 200:
                self.task_id = None

    @task(1)
    def get_parameters(self) -> Optional[dict]:
        """アプリケーション情報を取得"""
        with self.client.get(
            "/parameters", headers=self.headers, name="Workflow /parameters", params={"user": self.api.user_id}
        ) as response:
            if response.status_code == 200:
                return response.json()
            return None

    @task(1)
    def get_meta(self) -> Optional[dict]:
        """アプリケーションのメタ情報を取得"""
        with self.client.get(
            "/meta", headers=self.headers, name="Workflow /meta", params={"user": self.api.user_id}
        ) as response:
            if response.status_code == 200:
                return response.json()
            return None

    def _monitor_workflow_completion(self, workflow_id: str, timeout: int = 30) -> bool:
        """ワークフローの完了を監視"""

        # 一定確率で実行停止
        if self.user.environment.runner.user_count > 10:
            self.stop_workflow()

        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.client.get(
                f"/workflows/run/{workflow_id}", headers=self.headers, name="Workflow /workflows/run/:workflow_id"
            ) as response:
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status")
                    if status in ["succeeded", "failed", "stopped"]:
                        return status == "succeeded"
            time.sleep(1)
        return False

    def perform_workflow_tasks(self):
        """ワークフロータスクの一連の実行"""
        try:
            # データ確認
            self.get_parameters()
            self.get_meta()

            if self.user.environment.runner.user_count % 2 == 0:
                # ブロッキングでワークフロー実行
                self.run_workflow_blocking()
                # ステータス確認
                self.get_workflow_status()
            else:
                # 一定確率でストリーミング実行
                self.run_workflow_streaming()
                # 処理が完了するまで待機
                self._monitor_workflow_completion(self.workflow_id)

            if self.workflow_id:
                # ログ取得
                self.get_workflow_logs()

        except Exception as e:
            self.api.log_error("workflow_tasks", e)
