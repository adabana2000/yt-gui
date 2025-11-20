# チャンネル・プレイリスト一括ダウンロード機能

## 概要
YouTubeチャンネルまたはプレイリストの全動画を一括でダウンロードキューに追加する機能を実装しました。

## 新機能

### 1. チャンネル全動画ダウンロード

#### 機能
- チャンネルURLを入力すると、そのチャンネルの全動画をダウンロードキューに追加
- 既にダウンロード済みの動画は自動的にスキップ
- 非同期処理による高速な動画情報取得

#### 使用方法

**GUIから:**
1. ダウンロードタブでチャンネルURLを入力
2. 品質と優先度を設定
3. 「チャンネル全動画」ボタンをクリック
4. 確認ダイアログで「はい」を選択

**APIから:**
```bash
curl -X POST "http://localhost:8000/api/downloads/channel" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/@channelname",
    "quality": "1080p",
    "priority": 5
  }'
```

**Pythonコードから:**
```python
tasks = await download_manager.add_channel_download(
    channel_url="https://www.youtube.com/@channelname",
    quality="1080p",
    priority=5
)
print(f"Added {len(tasks)} videos to queue")
```

### 2. プレイリスト一括ダウンロード

#### 機能
- プレイリストURLを入力すると、全動画をダウンロードキューに追加
- 既にダウンロード済みの動画は自動的にスキップ
- プレイリストアイテムの範囲指定可能（例: "1-10,15,20-25"）

#### 使用方法

**GUIから:**
1. ダウンロードタブでプレイリストURLを入力
2. 品質と優先度を設定
3. 「プレイリスト」ボタンをクリック
4. 確認ダイアログで「はい」を選択

**APIから:**
```bash
curl -X POST "http://localhost:8000/api/downloads/playlist" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/playlist?list=PLXXXXXXXX",
    "quality": "720p",
    "priority": 5
  }'
```

**Pythonコードから:**
```python
tasks = await download_manager.add_playlist_download(
    playlist_url="https://www.youtube.com/playlist?list=PLXXXXXXXX",
    quality="720p",
    priority=5,
    playlist_items="1-10"  # オプション: 最初の10本のみ
)
print(f"Added {len(tasks)} videos to queue")
```

## 主な特徴

### 1. 重複チェック
- ダウンロード履歴DBを参照し、既にダウンロード済みの動画を自動スキップ
- 同じ動画を複数回ダウンロードすることを防止

### 2. 非同期処理
- asyncio/ThreadPoolExecutorによる高速な動画情報取得
- UIをブロックせずにバックグラウンドで処理

### 3. エラーハンドリング
- 個別の動画でエラーが発生しても、他の動画は正常に処理を継続
- エラーログに詳細を記録

### 4. イベント通知
- `channel:added` イベント: チャンネル動画追加完了時
- `playlist:added` イベント: プレイリスト動画追加完了時

### 5. 進捗表示
- GUIでは進捗ダイアログを表示
- APIではレスポンスに追加された動画数を返却

## API エンドポイント

### POST /api/downloads/channel
チャンネル全動画をダウンロードキューに追加

**リクエスト:**
```json
{
  "url": "https://www.youtube.com/@channelname",
  "output_path": "/path/to/downloads",
  "format_id": "bestvideo+bestaudio",
  "quality": "1080p",
  "priority": 5
}
```

**レスポンス:**
```json
{
  "success": true,
  "added_count": 42,
  "tasks": [
    {
      "id": "task-uuid-1",
      "url": "https://www.youtube.com/watch?v=VIDEO_ID",
      "status": "pending",
      "priority": 5
    },
    ...
  ]
}
```

### POST /api/downloads/playlist
プレイリスト全動画をダウンロードキューに追加

**リクエスト:**
```json
{
  "url": "https://www.youtube.com/playlist?list=PLXXXXXXXX",
  "output_path": "/path/to/downloads",
  "quality": "720p",
  "priority": 5
}
```

**レスポンス:**
```json
{
  "success": true,
  "added_count": 25,
  "tasks": [...]
}
```

## 技術詳細

### 実装ファイル
- `modules/download_manager.py`: コア機能実装
  - `add_channel_download()`: チャンネル全動画追加
  - `add_playlist_download()`: プレイリスト全動画追加
- `gui/download_tab.py`: GUI実装
  - チャンネル・プレイリストボタン
  - 進捗ダイアログ
- `api/main.py`: REST APIエンドポイント

### パフォーマンス
- チャンネル情報取得: 約1-5秒（動画数による）
- 重複チェック: O(n) - nは動画数
- メモリ使用量: 最小限（`extract_flat=True`により動画本体は取得しない）

## 使用例

### 例1: お気に入りチャンネルの全動画をダウンロード
```python
# URLを取得
channel_url = "https://www.youtube.com/@myfavoritechannel"

# GUIで「チャンネル全動画」ボタンをクリック
# → 全動画がキューに追加され、順次ダウンロード開始
```

### 例2: プレイリストの特定範囲をダウンロード
```python
tasks = await download_manager.add_playlist_download(
    playlist_url="https://www.youtube.com/playlist?list=PLxxxxxx",
    quality="720p",
    playlist_items="1-20"  # 最初の20本のみ
)
```

### 例3: 複数チャンネルを一括処理
```python
channels = [
    "https://www.youtube.com/@channel1",
    "https://www.youtube.com/@channel2",
    "https://www.youtube.com/@channel3"
]

for channel in channels:
    tasks = await download_manager.add_channel_download(
        channel_url=channel,
        priority=5
    )
    print(f"Added {len(tasks)} videos from {channel}")
```

## 注意事項

1. **大量のダウンロード**
   - チャンネルに数百本以上の動画がある場合、ダウンロードに長時間かかります
   - ディスク容量を確認してください

2. **YouTube利用規約**
   - 個人利用、教育・研究目的での使用を想定しています
   - 商用利用は禁止されています

3. **レート制限**
   - YouTube側のレート制限により、エラーが発生する可能性があります
   - その場合は時間をおいて再試行してください

## トラブルシューティング

### エラー: "No videos found in channel"
- チャンネルURLが正しいか確認
- チャンネルが動画を公開しているか確認

### エラー: "Failed to fetch channel information"
- インターネット接続を確認
- YouTube側の一時的な問題の可能性があります（時間をおいて再試行）

### 重複スキップが動作しない
- データベースが正常に初期化されているか確認
- `data/youtube_downloader.db` が存在するか確認

## 今後の予定

- [ ] チャンネル登録機能（自動更新チェック）
- [ ] フィルター機能（日付範囲、タイトル検索など）
- [ ] 並列取得の最適化
- [ ] キャンセル機能
