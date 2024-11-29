# Dify Load Test Suite

## 概要
DifyのAPIサーバーとSandbox環境の包括的な負荷テストスイート

## 機能
- APIサーバーの負荷テスト
  - チャット機能
  - ナレッジベース操作
  - ワークフロー実行
  - ファイル操作
- Sandboxの負荷テスト
  - コード実行
  - リソース使用状況
  - セキュリティ境界

## セットアップ
```bash
# 環境構築
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 環境変数設定
export DIFY_API_KEY="your-api-key"
```

## テスト実行
```bash
# API全体のテスト
locust -f locustfile.py DifyAPIUser

# Sandbox単体のテスト
locust -f locustfile.py DifySandboxUser

# 特定のタスクのみテスト
locust -f locustfile.py DifyAPIUser --tags chat,knowledge
```

## モニタリング
- Locust Web UI: http://localhost:8089
- リアルタイムメトリクス
- システムリソース使用状況

## テスト結果
- CSV形式のレポート
- グラフによる可視化
- エラー分析