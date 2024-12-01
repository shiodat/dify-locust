from locust import TaskSet, task
from typing import Dict, Any


class SandboxTasks(TaskSet):
    """Sandbox関連APIのテストタスク"""

    def __init__(self, parent, api_key):
        super().__init__(parent)
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "X-Api-Key": self.api_key,
        }
        self.test_codes = self._initialize_test_codes()

    def _initialize_test_codes(self) -> Dict[str, Dict[str, Any]]:
        """テストコードの初期化"""
        return {
            "simple": {
                "code": """
def main() -> dict:
   return {"result": "Hello World"}
print(main())
               """,
                "name": "simple_execution",
                "enable_network": False,
            },
            "cpu_intensive": {
                "code": """
def main() -> dict:
   # CPU負荷のかかる処理
   result = 0
   for i in range(1000):
       result += i
   return {"result": str(result)}
print(main())
               """,
                "name": "cpu_intensive",
                "enable_network": False,
            },
            "memory_intensive": {
                "code": """
def main() -> dict:
   # メモリを大量に使用する処理
   large_list = list(range(1000))
   return {"result": str(len(large_list))}
print(main())
               """,
                "name": "memory_intensive",
                "enable_network": False,
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
                "enable_network": True,
            },
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

    def _execute_code(self, test_case: Dict[str, Any]):
        """コード実行の共通処理"""
        payload = {
            "language": "python3",
            "code": test_case["code"].strip(),
            # "preload": test_case.get("preload", ""),
            "enable_network": test_case["enable_network"],
        }

        with self.client.post(
            "/sandbox/run",
            json=payload,
            headers=self.headers,
            name=f"/sandbox/run_{test_case['name']}",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                result = response.json()

                # エラーチェック
                if result.get("code") != 0:
                    response.failure(f"Execution failed: {result.get('message')}")
                    return

                # 実行結果の検証

                if result.get("data", {}).get("error", "") != "":
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

            # 時間がかかる処理のテスト
            self.execute_network_code()

        except Exception as e:
            print(f"Sandbox task error: {str(e)}")
