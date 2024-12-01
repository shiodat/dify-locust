from locust import HttpUser, task, between, events
from tasks.api_tasks import APITasks
from tasks.chat_tasks import ChatTasks
from tasks.knowledge_tasks import KnowledgeTasks
from tasks.workflow_tasks import WorkflowTasks
from tasks.sandbox_tasks import SandboxTasks
from tasks.file_tasks import FileTasks
from config import Config


class BaseUser(HttpUser):
    """基本ユーザークラス"""

    abstract = True  # これは直接インスタンス化されないクラス

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api = None  # APITasksのインスタンスを保持


class DifyChatUser(BaseUser):
    """Dify Chat テスト用ユーザークラス"""

    host = Config.API_HOST
    wait_time = between(1, 3)

    def on_start(self):
        """初期化処理"""
        self.api = APITasks(self)
        self.chat = ChatTasks(self, Config.CHATFLOW_API_KEY)

    @task(1)
    def chat_operations(self):
        """チャット機能のテスト"""
        self.chat.perform_chat_tasks()


class DifyWorkflowUser(BaseUser):
    """Dify Workflow テスト用ユーザークラス"""

    host = Config.API_HOST
    wait_time = between(1, 3)

    def on_start(self):
        """初期化処理"""
        self.api = APITasks(self)
        self.workflow = WorkflowTasks(self, Config.WORKFLOW_API_KEY)

    @task(1)
    def workflow_operations(self):
        """ワークフロー機能のテスト"""
        self.workflow.perform_workflow_tasks()


class DifyFileUser(BaseUser):
    """Dify File テスト用ユーザークラス"""

    host = Config.API_HOST
    wait_time = between(1, 3)

    def on_start(self):
        """初期化処理"""
        self.api = APITasks(self)
        self.file = FileTasks(self, Config.CHATFLOW_API_KEY)

    @task(1)
    def file_operations(self):
        """ファイル操作のテスト"""
        self.file.perform_file_tasks()


class DifyKnowledgeUser(BaseUser):
    """Dify Knowledge テスト用ユーザークラス"""

    host = Config.API_HOST
    wait_time = between(1, 3)

    def on_start(self):
        """初期化処理"""
        self.api = APITasks(self)
        self.knowledge = KnowledgeTasks(self, Config.KNOWLEDGE_API_KEY)

    @task(1)
    def knowledge_operations(self):
        """ナレッジベース機能のテスト"""
        self.knowledge.perform_knowledge_tasks()


class DifySandboxUser(BaseUser):
    """Sandbox テスト用ユーザークラス"""

    host = Config.SANDBOX_HOST
    wait_time = between(1, 2)

    def on_start(self):
        """初期化処理"""
        self.sandbox = SandboxTasks(self, Config.SANDBOX_API_KEY)

    @task(1)
    def sandbox_operations(self):
        """Sandbox機能のテスト"""
        self.sandbox.perform_sandbox_tasks()


class DifyChatflowSandboxUser(BaseUser):
    """Dify Chat テスト用ユーザークラス"""

    host = Config.API_HOST
    wait_time = between(1, 3)

    def on_start(self):
        """初期化処理"""
        self.api = APITasks(self)
        self.chat = ChatTasks(self, Config.CHATFLOW_SANDBOX_API_KEY)

    @task(1)
    def chat_operations(self):
        """チャット機能のテスト"""
        self.chat.perform_only_chat_message()


def run_test(testcase="all"):
    """テストの実行"""
    from locust.env import Environment
    import logging

    # テストケースに応じてユーザークラスを選択
    if testcase == "chatflow":
        user_classes = [DifyChatUser]
    elif testcase == "workflow":
        user_classes = [DifyWorkflowUser]
    elif testcase == "file":
        user_classes = [DifyFileUser]
    elif testcase == "knowledge":
        user_classes = [DifyKnowledgeUser]
    elif testcase == "sandbox":
        user_classes = [DifySandboxUser]
    elif testcase == "chatflow_sandbox":
        user_classes = [DifyChatflowSandboxUser]
    else:
        user_classes = [DifyChatUser, DifyWorkflowUser, DifyFileUser, DifyKnowledgeUser, DifySandboxUser]

    # 環境設定
    env = Environment(user_classes=user_classes, events=events)

    # 統計情報の設定
    env.create_local_runner()

    # テスト実行
    try:
        env.runner.start(user_count=Config.LOAD_TEST["users"], spawn_rate=Config.LOAD_TEST["spawn_rate"])
        env.runner.greenlet.join()
    except KeyboardInterrupt:
        logging.info("Test interrupted by user")
    finally:
        env.runner.quit()


if __name__ == "__main__":
    import sys

    # コマンドライン引数からテストケースを取得
    testcase = sys.argv[1] if len(sys.argv) > 1 else "all"
    run_test(testcase)
