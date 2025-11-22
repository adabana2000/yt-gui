# YouTube "Not Available on This App" エラー - 完全解決ガイド

## 🚨 問題の深刻さ

YouTubeは2024年後半から段階的にAPI制限を強化しており、以下のエラーが頻発するようになっています：

```
ERROR: [youtube] VIDEO_ID: The following content is not available on this app.
Watch on the latest version of YouTube.
```

このエラーは**非常に深刻**で、以下の動画で発生します：
- 年齢制限のある動画
- メンバー限定動画
- 一部の地域限定動画
- 特定のチャンネルの動画
- **最近は制限のない普通の動画でも発生**

## ✅ 解決策（優先度順）

### 1️⃣ **ブラウザCookieの使用（最重要・最も効果的）** ⭐⭐⭐⭐⭐

YouTubeにログインした状態のブラウザからCookieを取得し、yt-dlpに渡すことで、多くの制限を回避できます。

#### 自動Cookie取得（本アプリで実装済み）

**ChromeまたはFirefoxでYouTubeにログインしてください！**

1. ブラウザでYouTubeを開く
2. Googleアカウントでログイン
3. このアプリケーションを再起動

アプリケーションが自動的にブラウザからCookieを読み取ります。

#### 動作確認

ログに以下のメッセージが表示されれば成功：
```
[INFO] Loaded browser cookies from: /path/to/youtube_cookies.txt
```

以下のメッセージが表示される場合は失敗：
```
[WARNING] ⚠️  No browser cookies found!
```

#### トラブルシューティング: Cookie読み取りの失敗

**原因1: ブラウザがロックされている**
- ブラウザを完全に閉じてから、アプリを再起動

**原因2: ブラウザのプロファイルの問題**
```bash
# Chromeの場合、Default プロファイルが使用されます
# 別のプロファイルを使用している場合、そちらでログインしてください
```

**原因3: browser_cookie3の権限問題**
```bash
# Linux/Macの場合、ブラウザデータへのアクセス権限が必要
chmod +r ~/.config/google-chrome/Default/Cookies  # Chrome
chmod +r ~/.mozilla/firefox/*.default*/cookies.sqlite  # Firefox
```

### 2️⃣ **クライアント設定の最適化** ⭐⭐⭐⭐

本アプリケーションでは既に以下の設定を実装済み：

```python
'extractor_args': {
    'youtube': {
        'player_client': ['ios', 'mweb', 'android', 'tv_embedded'],
        'player_skip': ['webpage', 'configs'],
    }
}
```

これにより、複数のYouTubeクライアントを試行し、成功する可能性を高めています。

### 3️⃣ **po_token と visitor_data の使用（高度）** ⭐⭐⭐

YouTubeの最新の制限に対抗する最も強力な方法ですが、設定が複雑です。

#### po_tokenとvisitor_dataの取得方法

1. ブラウザの開発者ツールを開く（F12キー）
2. YouTubeの任意のページを開く
3. Consoleタブで以下を実行：

```javascript
// visitor_data の取得
(() => {
    const ytcfg = window.ytcfg || {};
    const visitorData = ytcfg.data_?.VISITOR_DATA;
    const poToken = ytcfg.data_?.PO_TOKEN;

    console.log('VISITOR_DATA:', visitorData);
    console.log('PO_TOKEN:', poToken);

    // クリップボードにコピー（Chrome/Edge）
    copy(JSON.stringify({
        visitor_data: visitorData,
        po_token: poToken
    }, null, 2));

    console.log('データをクリップボードにコピーしました');
})();
```

4. 取得したデータを設定ファイルに保存（実装予定）

**注意**: po_tokenは定期的に変更されるため、エラーが出たら再取得が必要です。

### 4️⃣ **yt-dlpの最新版を使用** ⭐⭐⭐

YouTubeは常にAPI仕様を変更しているため、yt-dlpも頻繁に更新されています。

```bash
# 最新版に更新
pip install --upgrade yt-dlp

# バージョン確認
yt-dlp --version
```

**推奨**: 少なくとも`2024.11.0`以降を使用

### 5️⃣ **リトライ設定の最適化** ⭐⭐

本アプリケーションでは既に以下を実装：

```python
'retries': 10,  # 10回リトライ
'fragment_retries': 10,
'sleep_interval': 1,  # リクエスト間に1秒待機
'max_sleep_interval': 5,  # 最大5秒のランダム待機
```

## 🔍 エラーの種類と対処法

### エラー1: "not available on this app"

```
ERROR: The following content is not available on this app.
```

**原因**: YouTubeがクライアントを制限している
**解決策**:
1. ブラウザCookieを使用（最優先）
2. po_token/visitor_dataを設定（高度）
3. yt-dlpを最新版に更新

### エラー2: "Requested format is not available"

```
ERROR: Requested format is not available. Use --list-formats
```

**原因**: 指定したフォーマットが存在しない
**解決策**: アプリは既に`bestvideo*+bestaudio/best`でフォールバックを実装済み

このエラーが出る場合、その動画自体が削除されているか、地域制限がかかっている可能性があります。

### エラー3: HTTP 403 Forbidden

```
ERROR: Unable to download API page: HTTP Error 403: Forbidden
```

**原因**: YouTube側からのアクセス拒否（レート制限またはbot検出）
**解決策**:
1. Cookieを使用
2. スリープ間隔を長くする
3. VPNを使用（地域制限の場合）

## 📊 成功率の比較

| 対策 | 成功率（推定） | 実装難易度 |
|------|--------------|----------|
| Cookieなし + デフォルト設定 | ~30% | - |
| 改善されたクライアント設定 | ~60% | 易（実装済み） |
| **Cookie使用** | **~90%** | **易（実装済み）** |
| Cookie + po_token | ~98% | 難（手動設定） |

## ⚙️ 本アプリケーションでの実装状況

### ✅ 実装済み

1. **複数クライアントフォールバック**
   - iOS → mweb → Android → TV Embedded

2. **改善されたHTTPヘッダー**
   - User-Agent: 最新Chrome
   - Accept headers
   - Sec-Fetch-Mode

3. **ロバストなリトライ**
   - 10回のリトライ
   - 指数バックオフ
   - スリープ間隔

4. **ブラウザCookie自動取得**
   - Chrome/Firefox/Edgeから自動取得
   - Netscape形式で保存
   - yt-dlpに自動適用

5. **フォーマット選択の改善**
   - `bestvideo*+bestaudio/best`
   - ワイルドカードで柔軟なマッチング

### 🚧 今後の実装予定

1. **po_token / visitor_data サポート**
   - 設定UIの追加
   - 自動更新機構

2. **Cookie定期リフレッシュ**
   - 1時間ごとにCookie再読み込み

3. **エラーごとの詳細ガイダンス**
   - GUIでエラーの原因と解決策を表示

## 🎯 推奨される使用方法

### 初回セットアップ

1. ChromeまたはFirefoxでYouTubeにログイン
2. アプリケーションを起動
3. ログで"Loaded browser cookies"を確認

### 定期的なメンテナンス

1. 週に1回はブラウザのYouTubeセッションを更新
2. アプリケーションを再起動してCookieをリフレッシュ
3. エラー率が高くなってきたらyt-dlpを更新

### エラーが多発する場合

1. ブラウザで一度YouTubeを開き、ログイン状態を確認
2. ブラウザを完全に閉じる
3. アプリケーションを再起動
4. それでもダメなら：
   ```bash
   pip install --upgrade yt-dlp
   rm data/youtube_cookies.txt  # Cookieファイルを削除
   # アプリを再起動してCookie再取得
   ```

## 📝 チャンネル一括ダウンロード時の注意

チャンネルから400本ダウンロードして一部が失敗する場合：

1. **正常な動作です**
   - すべての動画がダウンロード可能とは限りません
   - 削除済み、非公開、地域制限の動画は失敗します

2. **成功率の目安**
   - Cookieあり: 80-95%成功
   - Cookieなし: 30-60%成功

3. **失敗した動画の再試行**
   - ログを確認してビデオIDを特定
   - 個別に手動でダウンロードを試す
   - YouTubeで該当動画が視聴可能か確認

## 🔧 デバッグ方法

### ログの確認

```bash
# ログファイルの場所
tail -f logs/youtube_downloader.log

# Cookieが読み込まれたか確認
grep "cookie" logs/youtube_downloader.log

# エラーパターンの確認
grep "ERROR" logs/youtube_downloader.log | sort | uniq -c
```

### テストダウンロード

```bash
# 単一動画でテスト
python main.py --mode cli --url "https://www.youtube.com/watch?v=VIDEO_ID"

# デバッグモードで実行
DEBUG=true python main.py --mode cli --url "VIDEO_URL"
```

## 🆘 それでも解決しない場合

1. **yt-dlpの公式Issue**を確認
   - https://github.com/yt-dlp/yt-dlp/issues
   - 同じエラーが報告されているか検索

2. **YouTubeのステータス**を確認
   - 大規模な仕様変更が行われている可能性

3. **VPNを使用**
   - 地域制限が原因の可能性

4. **プレミアムアカウント**
   - YouTube Premium会員のCookieを使用すると成功率が上がる

## 📚 参考リンク

- [yt-dlp公式ドキュメント](https://github.com/yt-dlp/yt-dlp)
- [yt-dlp YouTube Extractor](https://github.com/yt-dlp/yt-dlp/blob/master/yt_dlp/extractor/youtube.py)
- [YouTube po_token/visitor_data解説](https://github.com/yt-dlp/yt-dlp/issues/10085)
- [browser-cookie3](https://github.com/borisbabic/browser_cookie3)

---

**重要**: この問題はYouTube側の制限であり、完全に回避することは困難です。上記の対策を組み合わせることで、成功率を最大化できます。
