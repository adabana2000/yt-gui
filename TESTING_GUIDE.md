# 新機能テストガイド

## 🧪 概要

このガイドでは、新しく実装された全10機能のテスト方法を説明します。

## 📋 テスト前の準備

### 1. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 2. データベースの初期化

アプリケーションを一度起動してデータベースを初期化：

```bash
python main.py --mode gui
```

## 🎯 機能別テスト

### 1. フォーマット/画質選択

#### テスト方法A: 設定ファイル編集

`config/settings.py` の設定を変更：

```python
VIDEO_QUALITY = "1080p"  # 1080p画質に変更
# または
VIDEO_QUALITY = "audio_only"  # 音声のみ
```

#### テスト方法B: CLIで直接ダウンロード

```bash
python main.py --mode cli --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

#### 確認項目
- [ ] 指定した画質でダウンロードされる
- [ ] `logs/` フォルダで使用されたフォーマット文字列を確認
- [ ] ファイルサイズが期待通りか

---

### 2. 字幕ダウンロード

#### 設定変更

```python
DOWNLOAD_SUBTITLES = True
SUBTITLE_LANGUAGES = ["ja", "en"]
EMBED_SUBTITLES = False  # 別ファイルとして保存
```

#### テスト実行

```bash
python main.py --mode cli --url "https://www.youtube.com/watch?v=<字幕付き動画ID>"
```

#### 確認項目
- [ ] `.ja.srt` ファイルが生成される
- [ ] `.en.srt` ファイルが生成される（ある場合）
- [ ] `EMBED_SUBTITLES=True` の場合、動画ファイルに埋め込まれる

---

### 3. 通知機能

#### 3-1. デスクトップ通知

#### 設定変更

```python
ENABLE_NOTIFICATIONS = True
DESKTOP_NOTIFICATION = True
NOTIFICATION_SOUND = True
```

#### テスト実行

```bash
# CLIモードでダウンロード
python main.py --mode cli --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

#### 確認項目
- [ ] ダウンロード完了時にWindows通知が表示される
- [ ] 通知音が鳴る
- [ ] エラー時に通知が表示される

#### 3-2. メール通知

#### 設定変更

```python
EMAIL_NOTIFICATION = True
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USERNAME = "your-email@gmail.com"
EMAIL_PASSWORD = "your-app-password"  # Gmailアプリパスワード
EMAIL_FROM = "your-email@gmail.com"
EMAIL_TO = "recipient@gmail.com"
```

**注意:** Gmailの場合、2段階認証を有効にして[アプリパスワード](https://support.google.com/accounts/answer/185833)を生成してください。

#### テスト実行

```bash
python main.py --mode cli --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

#### 確認項目
- [ ] 完了時にHTMLメールが届く
- [ ] メールに動画情報が含まれる
- [ ] エラー時にもメールが届く

---

### 4. プレイリスト/チャンネル一括ダウンロード

#### 設定変更

```python
PLAYLIST_DOWNLOAD = True
PLAYLIST_START = 1
PLAYLIST_END = 5  # 最初の5本だけ
# または
PLAYLIST_ITEMS = "1-3,5,7"  # 1,2,3,5,7番目
```

#### テスト実行

```bash
# プレイリストURL
python main.py --mode cli --url "https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxx"
```

#### 確認項目
- [ ] 指定した範囲の動画がダウンロードされる
- [ ] `download_archive.txt` にダウンロード済みIDが記録される
- [ ] 2回目の実行時、既にダウンロード済みをスキップする

---

### 5. 重複チェック

#### 設定変更

```python
SKIP_DUPLICATES = True
CHECK_BY_VIDEO_ID = True
DOWNLOAD_ARCHIVE = True
```

#### テスト実行

```bash
# 同じ動画を2回ダウンロード
python main.py --mode cli --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
# 再度実行
python main.py --mode cli --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

#### 確認項目
- [ ] 2回目の実行時、スキップメッセージが表示される
- [ ] `data/download_archive.txt` に動画IDが記録される
- [ ] データベースに履歴が保存される

---

### 6. サムネイルダウンロード

#### 設定変更

```python
DOWNLOAD_THUMBNAIL = True
EMBED_THUMBNAIL = False  # 別ファイルとして保存
WRITE_ALL_THUMBNAILS = False  # 最高画質のみ
```

#### テスト実行

```bash
python main.py --mode cli --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

#### 確認項目
- [ ] `.jpg` サムネイルファイルが生成される
- [ ] `EMBED_THUMBNAIL=True` の場合、動画ファイルに埋め込まれる
- [ ] `WRITE_ALL_THUMBNAILS=True` の場合、複数サイズが保存される

---

### 7. ダウンロード速度制限

#### 設定変更

```python
LIMIT_DOWNLOAD_SPEED = True
MAX_DOWNLOAD_SPEED = 1024  # 1MB/s (1024 KB/s)
```

#### テスト実行

```bash
python main.py --mode cli --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

#### 確認項目
- [ ] ダウンロード速度が約1MB/s以下に制限される
- [ ] ログで速度を確認

---

### 8. yt-dlp自動アップデート

#### テスト方法A: テストスクリプト

```bash
python -c "
import asyncio
from core.service_manager import ServiceConfig
from database.db_manager import DatabaseManager
from modules.updater_manager import UpdaterManager

async def test():
    config = ServiceConfig()
    db = DatabaseManager()
    updater = UpdaterManager(config, db)
    await updater.start()

    # バージョン確認
    version = await updater.get_current_version()
    print(f'Current version: {version}')

    # システム情報
    info = await updater.get_system_info()
    for k, v in info.items():
        print(f'{k}: {v}')

    # 更新チェック
    success, msg = await updater.check_and_update(force=True)
    print(f'Update result: {msg}')

    await updater.stop()

asyncio.run(test())
"
```

#### 確認項目
- [ ] 現在のyt-dlpバージョンが表示される
- [ ] システム情報が表示される
- [ ] 更新が必要な場合、自動的に更新される

---

### 9. プロキシ設定

#### 設定変更

```python
ENABLE_PROXY = True
PROXY_TYPE = "http"
HTTP_PROXY = "http://proxy.example.com:8080"
# 認証が必要な場合
PROXY_USERNAME = "username"
PROXY_PASSWORD = "password"
```

#### テスト実行

```bash
python main.py --mode cli --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

#### 確認項目
- [ ] プロキシ経由でダウンロードされる
- [ ] ログでプロキシ使用が確認できる

---

### 10. ダウンロード履歴管理

#### GUI起動

```bash
python main.py --mode gui
```

#### 確認項目
- [ ] 履歴タブにダウンロード済み動画が表示される
- [ ] 検索機能が動作する
- [ ] データベースに情報が保存されている

---

## 🔧 統合テスト

### 全機能を有効にしてテスト

```python
# config/settings.py で全機能を有効化
VIDEO_QUALITY = "1080p"
DOWNLOAD_SUBTITLES = True
SUBTITLE_LANGUAGES = ["ja", "en"]
DOWNLOAD_THUMBNAIL = True
SKIP_DUPLICATES = True
DESKTOP_NOTIFICATION = True
LIMIT_DOWNLOAD_SPEED = True
MAX_DOWNLOAD_SPEED = 2048  # 2MB/s
```

```bash
python main.py --mode cli --url "https://www.youtube.com/watch?v=<test-video-id>"
```

### 確認項目
- [ ] 1080pで動画がダウンロードされる
- [ ] 字幕ファイルが生成される
- [ ] サムネイルが保存される
- [ ] 速度が2MB/s以下に制限される
- [ ] 完了時に通知が表示される
- [ ] download_archive.txtに記録される
- [ ] データベースに履歴が保存される

---

## 📊 テスト結果の確認

### ログファイル

```bash
# ログ確認
tail -f logs/youtube_downloader.log
```

### ダウンロードアーカイブ

```bash
# アーカイブ確認
cat data/download_archive.txt
```

### データベース

```bash
# SQLiteで確認
sqlite3 data/youtube_downloader.db
> SELECT * FROM download_history ORDER BY created_at DESC LIMIT 5;
> .exit
```

---

## ❓ トラブルシューティング

### 通知が表示されない

**Windows:**
- Windows 10/11の通知設定を確認
- `win10toast` がインストールされているか確認: `pip install win10toast`

**Linux:**
- `libnotify` がインストールされているか確認
- `plyer` がインストールされているか確認: `pip install plyer`

**macOS:**
- システム環境設定 > 通知 で Python/Terminal の通知を許可

### メール通知が送信されない

1. SMTPサーバー設定を確認
2. Gmailの場合、2段階認証とアプリパスワードを使用
3. ファイアウォールでSMTPポート（587）が開いているか確認
4. ログファイルでエラーメッセージを確認

### yt-dlp更新が失敗する

```bash
# 手動で更新
pip install --upgrade yt-dlp

# または pip自体を更新
python -m pip install --upgrade pip
pip install --upgrade yt-dlp
```

### プロキシ接続エラー

1. プロキシURLの形式を確認: `http://host:port`
2. 認証情報が正しいか確認
3. プロキシが実際に動作しているか確認

---

## 📝 テストチェックリスト

全機能のテストが完了したら、以下にチェックを入れてください：

- [ ] フォーマット/画質選択
- [ ] 字幕ダウンロード
- [ ] デスクトップ通知
- [ ] メール通知（オプション）
- [ ] プレイリスト一括ダウンロード
- [ ] 重複チェック
- [ ] サムネイルダウンロード
- [ ] ダウンロード速度制限
- [ ] yt-dlp自動アップデート
- [ ] プロキシ設定（オプション）

---

## 🎉 テスト完了後

全てのテストが成功したら：

1. ✅ バックエンド実装が正しく動作している
2. 🎨 GUIの実装に進む準備が整った
3. 📚 ユーザー向けドキュメントの作成が可能

---

**最終更新:** 2025-11-22
