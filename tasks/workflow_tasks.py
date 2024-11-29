from locust import TaskSet, task
import json
from ..config import Config

class WorkflowTasks(TaskSet):
   """ワークフロー関連APIのテストタスク"""
   
   def __init__(self, parent):
       super().__init__(parent)
       self.api = parent.api
       self.workflow_id = None
       self.task_id = None

   @task(3)
   def run_simple_workflow(self):
       """シンプルなワークフローの実行"""
       payload = {
           "inputs": {
               "query": "Simple workflow test"
           },
           "response_mode": "blocking",
           "user": self.api.user_id
       }
       
       with self.client.post(
           "/workflows/run",
           json=payload,
           headers=self.api.headers,
           name="/workflows/run/simple"
       ) as response:
           if response.status_code == 200:
               data = response.json()
               self.workflow_id = data.get("workflow_run_id")
               self.task_id = data.get("task_id")

   @task(2)
   def run_streaming_workflow(self):
       """ストリーミングモードでのワークフロー実行"""
       payload = {
           "inputs": {
               "query": "Streaming workflow test"
           },
           "response_mode": "streaming",
           "user": self.api.user_id
       }
       
       with self.client.post(
           "/workflows/run",
           json=payload,
           headers=self.api.headers,
           name="/workflows/run/streaming",
           stream=True
       ) as response:
           if response.status_code == 200:
               for line in response.iter_lines():
                   if line:
                       data = json.loads(line.decode('utf-8').replace('data: ', ''))
                       self.workflow_id = data.get("workflow_run_id")
                       self.task_id = data.get("task_id")

   @task(2)
   def run_workflow_with_file(self):
       """ファイルを含むワークフローの実行"""
       # まずファイルをアップロード
       file_id = self.api.upload_file("test_files/sample.txt")
       if not file_id:
           return

       payload = {
           "inputs": {
               "file": {
                   "type": "document",
                   "transfer_method": "local_file",
                   "upload_file_id": file_id
               }
           },
           "response_mode": "blocking",
           "user": self.api.user_id
       }
       
       with self.client.post(
           "/workflows/run",
           json=payload,
           headers=self.api.headers,
           name="/workflows/run/with_file"
       ) as response:
           self.api.handle_response(response, "run_workflow_with_file")

   @task(2)
   def get_workflow_status(self):
       """ワークフロー実行状態の取得"""
       if not self.workflow_id:
           return
           
       with self.client.get(
           f"/workflows/run/{self.workflow_id}",
           headers=self.api.headers,
           name="/workflows/status"
       ) as response:
           self.api.handle_response(response, "get_workflow_status")

   @task(2)
   def get_workflow_logs(self):
       """ワークフローログの取得"""
       params = {
           "page": 1,
           "limit": 20,
           "keyword": "",
           "status": "succeeded"  # succeeded/failed/stopped
       }
       
       with self.client.get(
           "/workflows/logs",
           params=params,
           headers=self.api.headers,
           name="/workflows/logs"
       ) as response:
           self.api.handle_response(response, "get_workflow_logs")

   @task(1)
   def stop_workflow(self):
       """ワークフロー実行の停止"""
       if not self.task_id:
           return
           
       payload = {
           "user": self.api.user_id
       }
       
       with self.client.post(
           f"/workflows/tasks/{self.task_id}/stop",
           json=payload,
           headers=self.api.headers,
           name="/workflows/stop"
       ) as response:
           if response.status_code == 200:
               self.task_id = None

   def _monitor_workflow_completion(self, workflow_id: str, timeout: int = 30) -> bool:
       """ワークフローの完了を監視"""
       import time
       start_time = time.time()
       
       while time.time() - start_time < timeout:
           with self.client.get(
               f"/workflows/run/{workflow_id}",
               headers=self.api.headers,
               name="/workflows/monitor"
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
           # シンプルなワークフロー実行
           self.run_simple_workflow()
           
           if self.workflow_id:
               # ステータス確認
               self.get_workflow_status()
               
               # 一定確率でストリーミング実行
               if self.environment.runner.user_count % 2 == 0:
                   self.run_streaming_workflow()
               
               # ログ取得
               self.get_workflow_logs()
               
               # ファイル付きワークフロー
               self.run_workflow_with_file()
               
               # 一定確率で実行停止
               if self.environment.runner.user_count > 10:
                   self.stop_workflow()
               
       except Exception as e:
           self.api.log_error("workflow_tasks", e)