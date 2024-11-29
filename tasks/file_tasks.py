from locust import TaskSet, task
import os
from mimetypes import guess_type
from ..config import Config

class FileTasks(TaskSet):
   """ファイル操作関連APIのテストタスク"""
   
   def __init__(self, parent):
       super().__init__(parent)
       self.api = parent.api
       self.test_files = {
           "document": {
               "path": "test_files/sample.txt",
               "type": "document",
               "mime_type": "text/plain"
           },
           "image": {
               "path": "test_files/sample.jpg", 
               "type": "image",
               "mime_type": "image/jpeg"
           },
           "audio": {
               "path": "test_files/sample.mp3",
               "type": "audio",
               "mime_type": "audio/mpeg"
           }
       }
       self.uploaded_file_ids = {}

   @task(3)
   def upload_document(self):
       """ドキュメントファイルのアップロード"""
       self._upload_file("document")

   @task(2)
   def upload_image(self):
       """画像ファイルのアップロード"""
       self._upload_file("image")

   @task(1)
   def upload_audio(self):
       """音声ファイルのアップロード"""
       self._upload_file("audio")

   @task(2)
   def audio_to_text(self):
       """音声からテキストへの変換テスト"""
       if not self.test_files["audio"]["path"]:
           return

       with open(self.test_files["audio"]["path"], 'rb') as f:
           files = {
               'file': ('audio.mp3', f, 'audio/mpeg')
           }
           data = {
               'user': self.api.user_id
           }
           
           with self.client.post(
               "/audio-to-text",
               files=files,
               data=data,
               headers={"Authorization": self.api.headers["Authorization"]},
               name="/audio-to-text"
           ) as response:
               self.api.handle_response(response, "audio_to_text")

   @task(2)
   def text_to_audio(self):
       """テキストから音声への変換テスト"""
       payload = {
           "text": "Hello, this is a test message for text to speech conversion.",
           "user": self.api.user_id
       }
       
       with self.client.post(
           "/text-to-audio",
           json=payload,
           headers=self.api.headers,
           name="/text-to-audio"
       ) as response:
           self.api.handle_response(response, "text_to_audio")

   def _upload_file(self, file_type: str):
       """ファイルアップロードの共通処理"""
       file_info = self.test_files.get(file_type)
       if not file_info or not os.path.exists(file_info["path"]):
           return

       with open(file_info["path"], 'rb') as f:
           files = {
               'file': (
                   os.path.basename(file_info["path"]),
                   f,
                   file_info["mime_type"]
               )
           }
           data = {
               'user': self.api.user_id,
               'type': file_info["type"]
           }
           
           with self.client.post(
               "/files/upload",
               files=files,
               data=data,
               headers={"Authorization": self.api.headers["Authorization"]},
               name=f"/files/upload-{file_type}"
           ) as response:
               if response.status_code == 201:
                   file_id = response.json().get('id')
                   if file_id:
                       self.uploaded_file_ids[file_type] = file_id
               else:
                   self.api.log_error(f"file_upload_{file_type}", 
                                    Exception(f"Upload failed: {response.status_code}"))

   def _validate_file_size(self, file_path: str) -> bool:
       """ファイルサイズの検証"""
       try:
           size = os.path.getsize(file_path)
           # ファイルタイプに応じたサイズ制限を確認
           file_type = guess_type(file_path)[0]
           if file_type:
               if file_type.startswith('image/'):
                   return size <= 10 * 1024 * 1024  # 10MB
               elif file_type.startswith('audio/'):
                   return size <= 50 * 1024 * 1024  # 50MB
               elif file_type.startswith('video/'):
                   return size <= 100 * 1024 * 1024  # 100MB
               else:
                   return size <= 15 * 1024 * 1024  # 15MB
           return False
       except OSError:
           return False

   def perform_file_tasks(self):
       """ファイル操作タスクの一連の実行"""
       try:
           # ドキュメントアップロード
           self.upload_document()
           
           # 画像アップロード
           self.upload_image()
           
           # 音声ファイルの処理
           self.upload_audio()
           if self.uploaded_file_ids.get("audio"):
               self.audio_to_text()
           
           # テキスト→音声変換
           self.text_to_audio()
           
       except Exception as e:
           self.api.log_error("file_tasks", e)