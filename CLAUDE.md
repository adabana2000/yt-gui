# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

yt-dlpをベースとした高機能YouTubeダウンローダーの開発プロジェクト。現在は仕様書と実装案のドキュメント段階で、実際のコード実装はまだ開始されていません。

## ドキュメント構成

- **youtube_downloader_specification.md**: 詳細な仕様書（機能要件、UI/UX、技術要件）
- **youtube_downloader_implementation.md**: 実装案（アーキテクチャ、モジュール設計、コード例）

## 想定される技術スタック

### バックエンド
- **言語**: Python 3.10+
- **フレームワーク**: FastAPI (Web API), asyncio (非同期処理)
- **タスクキュー**: Celery + Redis
- **データベース**: SQLite (ローカル), PostgreSQL (オプション)
- **外部ツール**: yt-dlp, FFmpeg

### フロントエンド
- **デスクトップGUI**: Electron + React + TypeScript または PyQt6/PySide6
- **Web UI**: React + TypeScript + Material-UI
- **状態管理**: Redux Toolkit

## アーキテクチャ構成

3層アーキテクチャ:

1. **ユーザーインターフェース層**: Desktop GUI, Web UI, CLI, API Client
2. **アプリケーション層**: Core Service Manager配下の各種マネージャー
   - Download Manager: ダウンロード処理、キュー管理
   - Schedule Manager: 定期実行、スケジュール管理
   - Encode Manager: 動画エンコード、GPU処理
   - Metadata Manager: メタデータ管理
   - Auth Manager: 認証、Cookie管理
3. **インフラ層**: yt-dlp Wrapper, FFmpeg Wrapper, SQLite DB, Redis Cache

## 主要モジュール

### Download Manager
- 非同期ダウンロード処理（asyncio + ThreadPoolExecutor）
- マルチスレッドダウンロード（同時1-10接続）
- キュー管理とタスク優先度制御
- 進捗フック、リトライ機能

### Schedule Manager
- APSchedulerによるCronベースのスケジューリング
- チャンネル更新チェック、自動ダウンロード
- 新着動画検出とRSS/Atomフィード監視

### Auth Manager
- Google OAuth 2.0認証
- ブラウザからのCookie自動インポート
- プロキシ設定（HTTP/HTTPS/SOCKS5）

### Database Manager
- SQLAlchemyによるORM
- ダウンロード履歴管理
- 重複チェック機能

## 開発フェーズ（計画）

### Phase 1 (MVP) - 2週間
- 基本的なダウンロード機能
- シンプルなGUI
- ローカルデータベース

### Phase 2 - 1ヶ月
- スケジューリング機能
- 認証システム
- エンコード機能

### Phase 3 - 2ヶ月
- 完全なGUI
- プラグインシステム
- パフォーマンス最適化

## 実装時の重要事項

### 設計原則
- 非同期処理を最大限活用（asyncio, aiohttp）
- モジュール設計で保守性確保（BaseServiceクラスの継承）
- イベント駆動アーキテクチャ（EventBus）

### データフロー
1. ユーザーがURLを入力
2. Download Managerがタスクをキューに追加
3. ワーカーがyt-dlpでダウンロード実行
4. 進捗をWebSocket経由でフロントエンドに通知
5. 完了後にメタデータをDBに保存

### GPU処理
- NVIDIA NVENC、Intel QuickSync、AMD AMF対応
- GPUアクセラレーション検出機能
- エンコード時の自動GPU選択

### セキュリティ
- JWT認証
- 暗号化されたクレデンシャル保存
- Cookie管理とキーチェーン連携

## 主要依存パッケージ（想定）

```
yt-dlp
ffmpeg-python
fastapi
uvicorn
celery
redis
sqlalchemy
apscheduler
google-auth
browser-cookie3
prometheus-client
```

## ディレクトリ構造（予定）

```
yt-gui/
├── core/                 # コアサービス
│   └── service_manager.py
├── modules/              # 各種マネージャー
│   ├── download_manager.py
│   ├── schedule_manager.py
│   ├── auth_manager.py
│   └── encode_manager.py
├── database/             # データベース
│   ├── models.py
│   └── db_manager.py
├── api/                  # REST API
│   └── main.py
├── frontend/             # フロントエンド
│   ├── src/
│   │   ├── main/        # Electron メインプロセス
│   │   └── renderer/    # React UI
│   └── package.json
├── tests/                # テスト
├── config/               # 設定
└── requirements.txt
```

## 注意事項

- 現在はドキュメントのみが存在し、実装コードはまだありません
- 実装開始時は仕様書と実装案ドキュメントを参照してください
- YouTube利用規約の遵守が必須（個人利用、教育・研究目的を想定）
