# YouTube動画ダウンロード問題 - 修正サマリー

## 問題の原因

元のブランチ（`claude/youtube-downloader-dev-01FPfahvYev1rUvNrtgikNyd`）では、以下の問題が発生していました：

1. **"このアプリでは利用できません"エラー**
   - YouTubeの最近のAPI変更により、特定のクライアント設定でアクセスが制限される
   - Androidクライアントのみでは不十分

2. **レート制限エラー**
   - 連続リクエストによるYouTube側のレート制限
   - スリープ設定が不十分

3. **古いyt-dlpバージョン**
   - 最新のYouTube API変更に対応していない

## 実施した修正

### 1. YouTubeクライアント設定の最適化

**変更前:**
```python
'extractor_args': {
    'youtube': {
        'player_client': ['android', 'web'],
    }
}
```

**変更後:**
```python
'extractor_args': {
    'youtube': {
        'player_client': ['ios', 'android', 'web'],  # iOSを最優先に
        'player_skip': ['webpage', 'configs'],       # 不要なリクエストをスキップ
    }
}
```

**理由:**
- iOSクライアントは現在最も安定してYouTubeにアクセス可能
- `player_skip`により不要なウェブページリクエストを削減し、レート制限を回避

### 2. レート制限対策の強化

**変更前:**
```python
'sleep_interval': 1,
'max_sleep_interval': 3,
'sleep_interval_requests': 1,
```

**変更後:**
```python
'sleep_interval': 1,
'max_sleep_interval': 5,              # 3秒→5秒に延長
'sleep_interval_requests': 1,
'sleep_interval_subtitles': 1,        # 新規追加
```

**理由:**
- より長いランダムスリープでレート制限を回避
- 字幕ダウンロード時にもスリープを入れることで、さらなる制限回避

### 3. yt-dlpバージョンの更新

**変更前:**
```
yt-dlp>=2023.11.0
```

**変更後:**
```
yt-dlp>=2024.11.0
```

**理由:**
- 最新バージョンでは、YouTubeのAPI変更に対応
- 新しいクライアント設定のサポートが改善されている

## 修正対象ファイル

### modules/download_manager.py

以下の4つのメソッドで設定を統一して修正：

1. **`_get_default_ydl_opts()`** (lines 199-210)
   - メインのダウンロード設定

2. **`get_video_info()`** (lines 648-653)
   - 動画情報取得時の設定

3. **`add_channel_download()`** (lines 759-765)
   - チャンネル一括ダウンロード時の設定

4. **`add_playlist_download()`** (lines 888-894)
   - プレイリスト一括ダウンロード時の設定

### requirements.txt

yt-dlpの最小バージョンを更新

## 期待される効果

1. **エラー率の大幅な低減**
   - "このアプリでは利用できません"エラーの解消
   - 403 Forbiddenエラーの減少

2. **ダウンロード成功率の向上**
   - iOSクライアントの使用により、より多くの動画にアクセス可能
   - レート制限による失敗の減少

3. **安定性の向上**
   - 適切なスリープ間隔によるサーバー負荷の軽減
   - 長期的な安定動作

## 検証方法（ユーザー環境で）

実際の環境では以下の方法で動作確認してください：

### 1. 単一動画のダウンロード
```bash
python main.py --mode cli --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

### 2. GUIでの動画ダウンロード
```bash
python main.py --mode gui
```
- URLを入力して「ダウンロード」をクリック
- 進捗が正常に表示されることを確認

### 3. チャンネル一括ダウンロード
- GUIのチャンネルURLフィールドにチャンネルURLを入力
- 複数の動画が正常にキューに追加されることを確認

## 追加の推奨事項

より安定した動作のために、以下も検討してください：

1. **User-Agent設定**
   - 必要に応じて、より一般的なUser-Agentを設定

2. **Cookie利用**
   - ブラウザからのCookieインポート機能を活用
   - 年齢制限やメンバー限定コンテンツへのアクセスが可能に

3. **プロキシ設定**
   - 特定の地域から制限されている場合、プロキシの利用を検討

4. **定期的なyt-dlp更新**
   - `pip install --upgrade yt-dlp` で定期的に最新版に更新

## トラブルシューティング

もしまだ問題が発生する場合：

1. **yt-dlpを最新版に更新**
   ```bash
   pip install --upgrade yt-dlp
   ```

2. **キャッシュをクリア**
   ```bash
   rm -rf ~/.cache/yt-dlp/
   ```

3. **ブラウザCookieを再取得**
   - AuthManagerを通じてCookieを再度取得

4. **ログを確認**
   - `logs/`ディレクトリ内のログファイルで詳細なエラーを確認

## 参考リンク

- [yt-dlp GitHub](https://github.com/yt-dlp/yt-dlp)
- [yt-dlp 最新リリース](https://github.com/yt-dlp/yt-dlp/releases)
- [YouTube API変更情報](https://github.com/yt-dlp/yt-dlp/issues)
