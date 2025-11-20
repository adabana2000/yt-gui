# YouTube Downloader

yt-dlpをベースとした高機能YouTubeダウンローダー

## 特徴

- **強力なダウンロード機能**: yt-dlpによる高速・高品質ダウンロード
- **PySide6 GUI**: 使いやすい日本語GUI
- **非同期処理**: asyncioによる効率的な並列ダウンロード
- **スケジューリング**: Cron式による自動ダウンロード
- **GPU対応**: NVIDIA NVENC、Intel QuickSync、AMD AMFによるハードウェアエンコーディング
- **データベース管理**: SQLiteによる履歴管理と検索
- **REST API**: FastAPIによるWeb API提供

## 必要要件

### システム要件
- Python 3.10以上
- FFmpeg
- yt-dlp

### 対応OS
- Windows 10/11
- macOS 10.15+
- Ubuntu 20.04+

## インストール

### 1. 必要なツールのインストール

#### FFmpegのインストール

**Windows:**
```bash
# Chocolateyを使用
choco install ffmpeg

# または公式サイトからダウンロード
# https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

#### yt-dlpのインストール
```bash
pip install yt-dlp
```

### 2. プロジェクトのセットアップ

```bash
# リポジトリをクローン
git clone <repository-url>
cd yt-gui

# 仮想環境を作成（推奨）
python -m venv venv

# 仮想環境を有効化
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 依存パッケージをインストール
pip install -r requirements.txt
```

### 3. 設定ファイルの作成

```bash
# .envファイルを作成
cp .env.example .env

# 必要に応じて.envファイルを編集
```

## 使用方法

### GUIモード（デフォルト）

```bash
python main.py
```

または

```bash
python main.py --mode gui
```

### APIサーバーモード

```bash
python main.py --mode api
```

API ドキュメント: http://localhost:8000/docs

### CLIモード

```bash
python main.py --mode cli --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

## プロジェクト構造

```
yt-gui/
├── core/               # コアシステム
│   ├── event_bus.py
│   └── service_manager.py
├── modules/            # 各種マネージャー
│   ├── download_manager.py
│   ├── schedule_manager.py
│   ├── auth_manager.py
│   ├── encode_manager.py
│   └── metadata_manager.py
├── database/           # データベース
│   ├── models.py
│   └── db_manager.py
├── api/                # REST API
│   └── main.py
├── gui/                # GUI
│   ├── main_window.py
│   ├── download_tab.py
│   ├── schedule_tab.py
│   ├── history_tab.py
│   └── settings_tab.py
├── config/             # 設定
│   └── settings.py
├── utils/              # ユーティリティ
│   └── logger.py
├── tests/              # テスト
├── downloads/          # ダウンロードフォルダ
├── data/               # データベースフォルダ
├── logs/               # ログフォルダ
├── requirements.txt
├── main.py
└── README.md
```

## 主要機能

### 1. ダウンロード機能

- 単一動画ダウンロード
- プレイリスト一括ダウンロード
- チャンネル動画ダウンロード
- 品質選択（最高品質、1080p、720p、480p、音声のみ）
- 優先度設定
- 一時停止・再開・キャンセル

### 2. スケジューリング機能

- Cron式による定期実行
- チャンネル更新チェック
- 新着動画の自動ダウンロード
- タスク管理（有効化・無効化・削除）

### 3. 履歴管理

- ダウンロード履歴の検索
- 統計情報表示
- ページネーション

### 4. 設定

- ダウンロード保存先設定
- 同時ダウンロード数設定
- GPU設定
- Google認証

## API エンドポイント

### ダウンロード

- `POST /api/downloads` - ダウンロード追加
- `GET /api/downloads` - アクティブなダウンロード取得
- `GET /api/downloads/{task_id}` - ダウンロード状態取得
- `POST /api/downloads/{task_id}/pause` - ダウンロード一時停止
- `POST /api/downloads/{task_id}/resume` - ダウンロード再開
- `DELETE /api/downloads/{task_id}` - ダウンロードキャンセル

### 履歴

- `GET /api/history` - ダウンロード履歴取得
- `GET /api/stats` - 統計情報取得

### スケジュール

- `POST /api/schedules` - スケジュール追加
- `GET /api/schedules` - スケジュール一覧取得
- `DELETE /api/schedules/{task_id}` - スケジュール削除

### エンコード

- `POST /api/encode/video` - 動画エンコード
- `POST /api/encode/audio` - 音声抽出

### WebSocket

- `WS /ws` - リアルタイム更新

## 開発

### テストの実行

```bash
pytest
```

### カバレッジレポート

```bash
pytest --cov=. --cov-report=html
```

## トラブルシューティング

### FFmpegが見つからない

FFmpegがPATHに追加されていることを確認してください。

```bash
ffmpeg -version
```

### yt-dlpが古い

最新版に更新してください。

```bash
pip install --upgrade yt-dlp
```

### データベースエラー

データベースファイルを削除して再起動してください。

```bash
rm data/youtube_downloader.db
```

## ライセンス

MIT License

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。

## 作成者

YouTube Downloader Project

## 謝辞

- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg](https://ffmpeg.org/)
- [PySide6](https://doc.qt.io/qtforpython/)
- [FastAPI](https://fastapi.tiangolo.com/)
