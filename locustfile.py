from locust import HttpUser, task, between, events
from tasks.api_tasks import APITasks
from tasks.chat_tasks import ChatTasks
from tasks.knowledge_tasks import KnowledgeTasks
from tasks.workflow_tasks import WorkflowTasks
from tasks.sandbox_tasks import SandboxTasks
from tasks.file_tasks import FileTasks
from config import Config

class DifyAPIUser(HttpUser):
   """Dify API 負荷テストクラス"""
   
   host = Config.API_HOST
   wait_time = between(1, 3)
   
   def on_start(self):
       self.api = APITasks(self)
       self.chat = ChatTasks(self)
       self.knowledge = KnowledgeTasks(self)
       self.workflow = WorkflowTasks(self)
       self.file = FileTasks(self)

   @task(3)
   def perform_chat_operations(self):
       """チャット機能のテスト"""
       self.chat.perform_chat_tasks()

   @task(2)
   def perform_knowledge_operations(self):
       """ナレッジベース機能のテスト"""
       self.knowledge.perform_knowledge_tasks()

   @task(2)
   def perform_file_operations(self):
       """ファイル操作のテスト"""
       self.file.perform_file_tasks()

   @task(1)
   def perform_workflow_operations(self):
       """ワークフロー機能のテスト"""
       self.workflow.perform_workflow_tasks()

class DifySandboxUser(HttpUser):
   """Dify Sandbox 負荷テストクラス"""
   
   host = Config.SANDBOX_HOST
   wait_time = between(1, 2)
   
   def on_start(self):
       self.sandbox = SandboxTasks(self)

   @task(3)
   def perform_sandbox_operations(self):
       """Sandboxの機能テスト"""
       self.sandbox.perform_sandbox_tasks()

@events.init.add_listener
def on_locust_init(environment, **kwargs):
   """テスト開始時の初期化処理"""
   print(f"Starting Dify load test with {environment.host}")

@events.quitting.add_listener
def on_locust_quit(environment, **kwargs):
   """テスト終了時の処理"""
   if environment.stats.total.fail_ratio > Config.PERFORMANCE.get("error_rate", 0.01):
       print("Test failed due to high error rate")
       environment.process_exit_code = 1
   
   print("\nTest Summary:")
   print(f"Total Requests: {environment.stats.total.num_requests}")
   print(f"Failed Requests: {environment.stats.total.num_failures}")
   print(f"Average Response Time: {environment.stats.total.avg_response_time:.2f}ms")
   print(f"95th Percentile: {environment.stats.total.get_response_time_percentile(0.95):.2f}ms")

def run():
   """メイン実行関数"""
   import sys
   from locust.env import Environment
   from locust.stats import stats_printer, stats_history
   from locust.log import setup_logging
   import logging
   
   # ロギング設定
   setup_logging("INFO", None)
   
   # テスト環境の設定
   env = Environment(
       user_classes=[DifyAPIUser, DifySandboxUser],
       events=events,
    #    host=Config.API_HOST
   )
   
   # 統計情報の出力設定
   env.create_local_runner()
   env.create_web_ui()
   
   try:
       env.runner.start(
           user_count=Config.LOAD_TEST["users"]["api"] + Config.LOAD_TEST["users"]["sandbox"],
           spawn_rate=Config.LOAD_TEST["spawn_rate"]
       )
       stats_printer(env.stats)
       stats_history(env.runner)
       env.web_ui.start()
       env.runner.greenlet.join()
       
   except KeyboardInterrupt:
       logging.info("Test interrupted by user")
   finally:
       env.runner.quit()

if __name__ == "__main__":
   run()