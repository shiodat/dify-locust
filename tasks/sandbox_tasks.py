from locust import TaskSet, task
import os
from typing import Dict, Any

class SandboxTasks(TaskSet):
   """Sandbox関連APIのテストタスク"""
   
   def __init__(self, parent):
       super().__init__(parent)
       self.headers = {
           "Content-Type": "application/json",
           "X-Api-Key": parent.api_key,
       }
       self.test_codes = self._initialize_test_codes()

   def _initialize_test_codes(self) -> Dict[str, Dict[str, Any]]:
       """テストコードの初期化"""
       return {
           "simple": {
               "code": """
def main() -> dict:
   return {"message": "Hello World"}
print(main())
               """,
               "name": "simple_execution",
               "enable_network": False
           },
           "cpu_intensive": {
               "code": """
def main() -> dict:
   # CPU負荷のかかる処理
   result = 0
   for i in range(1000000):
       result += i
   return {"result": result}
print(main())
               """,
               "name": "cpu_intensive",
               "enable_network": False
           },
           "memory_intensive": {
               "code": """
def main() -> dict:
   # メモリを大量に使用する処理
   large_list = list(range(1000000))
   return {"length": len(large_list)}
print(main())
               """,
               "name": "memory_intensive",
               "enable_network": False
           },
           "network_operation": {
               "code": """
import json
def main() -> dict:
   data = {"test": "data"}
   return json.dumps(data)
print(main())
               """,
               "name": "network_operation",
               "enable_network": True
           },
           "error_case": {
               "code": """
def main() -> dict:
   # エラーを発生させる処理
   raise Exception("Test error")
print(main())
               """,
               "name": "error_case",
               "enable_network": False
           },
           "with_preload": {
               "code": """
def main() -> dict:
   return {"math_result": math.sqrt(16)}
print(main())
               """,
               "name": "with_preload",
               "preload": "import math",
               "enable_network": False
           }
       }

   @task(3)
   def execute_simple_code(self):
       """シンプルなコード実行のテスト"""
       self._execute_code(self.test_codes["simple"])

   @task(2)
   def execute_cpu_intensive_code(self):
       """CPU負荷の高いコード実行のテスト"""
       self._execute_code(self.test_codes["cpu_intensive"])

   @task(2)
   def execute_memory_intensive_code(self):
       """メモリ使用量の多いコード実行のテスト"""
       self._execute_code(self.test_codes["memory_intensive"])

   @task(1)
   def execute_network_code(self):
       """ネットワークアクセスを伴うコード実行のテスト"""
       self._execute_code(self.test_codes["network_operation"])

   @task(1)
   def execute_error_case(self):
       """エラーケースのテスト"""
       self._execute_code(self.test_codes["error_case"])

   @task(1)
   def execute_with_preload(self):
       """プリロードを使用したコード実行のテスト"""
       self._execute_code(self.test_codes["with_preload"])

   def _execute_code(self, test_case: Dict[str, Any]):
       """コード実行の共通処理"""
       payload = {
           "language": "python3",
           "code": test_case["code"].strip(),
           "preload": test_case.get("preload", ""),
           "enable_network": test_case["enable_network"]
       }

       with self.client.post(
           "/v1/sandbox/run",
           json=payload,
           headers=self.headers,
           name=f"/sandbox/run_{test_case['name']}"
       ) as response:
           if response.status_code == 200:
               result = response.json()
               
               # エラーチェック
               if result.get("code") != 0:
                   response.failure(f"Execution failed: {result.get('message')}")
                   return
               
               # 実行結果の検証
               if "error" in result.get("data", {}):
                   response.failure(f"Execution error: {result['data']['error']}")
                   return

           else:
               response.failure(f"Request failed: {response.status_code}")

   def perform_sandbox_tasks(self):
       """Sandboxタスクの一連の実行"""
       try:
           # シンプルなコード実行
           self.execute_simple_code()
           
           # リソース負荷のテスト
           self.execute_cpu_intensive_code()
           self.execute_memory_intensive_code()
           
           # ネットワーク操作のテスト
           self.execute_network_code()
           
           # プリロード機能のテスト
           self.execute_with_preload()
           
           # エラーケースのテスト
           self.execute_error_case()
           
       except Exception as e:
           print(f"Sandbox task error: {str(e)}")