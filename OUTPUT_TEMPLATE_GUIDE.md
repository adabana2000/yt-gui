# 出力テンプレート設定ガイド

## 📁 概要

YouTube Downloaderでは、**yt-dlpの強力な出力テンプレート機能**を使用して、ダウンロードしたファイルの保存先ディレクトリとファイル名を自由にカスタマイズできます。

## 🚀 基本的な使い方

### GUI設定（推奨）

1. **設定タブを開く**
2. **「出力テンプレート」セクション**を探す
3. **プリセットを選択**するか、**カスタムテンプレート**を入力
4. **「設定を保存」**をクリック

### プリセット一覧

| プリセット | テンプレート | 出力例 |
|-----------|-------------|--------|
| **チャンネル別** | `%(uploader)s/%(title)s.%(ext)s` | `チャンネル名/動画タイトル.mp4` |
| **日付別** | `%(upload_date>%Y)s/%(upload_date>%m)s/%(title)s.%(ext)s` | `2025/01/動画タイトル.mp4` |
| **チャンネル+日付** | `%(uploader)s/%(upload_date>%Y-%m)s/%(title)s.%(ext)s` | `チャンネル名/2025-01/動画タイトル.mp4` |
| **チャンネル+種類** | `%(uploader)s/%(playlist_title\|)s/%(title)s.%(ext)s` | `チャンネル名/プレイリスト名/動画タイトル.mp4` |
| **フラット** | `%(title)s.%(ext)s` | `動画タイトル.mp4` |
| **詳細付き** | `%(uploader)s/[%(id)s] %(title)s - %(upload_date>%Y%m%d)s.%(ext)s` | `チャンネル名/[dQw4w9WgXcQ] 動画タイトル - 20250122.mp4` |
| **画質別** | `%(uploader)s/%(resolution)s/%(title)s.%(ext)s` | `チャンネル名/1080p/動画タイトル.mp4` |
| **カスタム** | *ユーザー定義* | *自由に設定* |

## 📝 利用可能な変数

### 基本情報

| 変数 | 説明 | 例 |
|------|------|-----|
| `%(title)s` | 動画のタイトル | `Rick Astley - Never Gonna Give You Up` |
| `%(uploader)s` | チャンネル名/アップローダー名 | `RickAstleyVEVO` |
| `%(uploader_id)s` | チャンネルID | `UCuAXFkgsw1L7xaCfnd5JJOw` |
| `%(channel)s` | チャンネル名（別名） | `RickAstleyVEVO` |
| `%(id)s` | 動画ID | `dQw4w9WgXcQ` |
| `%(ext)s` | ファイル拡張子 | `mp4`, `webm` |
| `%(description)s` | 動画の説明文 | `Official video for...` |

### 日付・時刻

| 変数 | 説明 | 例 |
|------|------|-----|
| `%(upload_date)s` | アップロード日（YYYYMMDD） | `20091025` |
| `%(upload_date>%Y)s` | アップロード年 | `2009` |
| `%(upload_date>%m)s` | アップロード月 | `10` |
| `%(upload_date>%d)s` | アップロード日 | `25` |
| `%(upload_date>%Y-%m)s` | 年-月 | `2009-10` |
| `%(upload_date>%Y%m%d)s` | YYYYMMDD形式 | `20091025` |
| `%(upload_date>%B)s` | 月名（英語） | `October` |
| `%(timestamp)s` | Unix timestamp | `1256428800` |

### 動画メタデータ

| 変数 | 説明 | 例 |
|------|------|-----|
| `%(duration)s` | 動画の長さ（秒） | `212` |
| `%(duration_string)s` | 動画の長さ（文字列） | `3:32` |
| `%(view_count)s` | 再生回数 | `1500000000` |
| `%(like_count)s` | いいね数 | `15000000` |
| `%(comment_count)s` | コメント数 | `500000` |
| `%(age_limit)s` | 年齢制限 | `0`, `18` |
| `%(is_live)s` | ライブ配信かどうか | `True`, `False` |

### 品質・フォーマット

| 変数 | 説明 | 例 |
|------|------|-----|
| `%(resolution)s` | 解像度 | `1080p`, `720p`, `480p` |
| `%(width)s` | 横幅（ピクセル） | `1920` |
| `%(height)s` | 縦幅（ピクセル） | `1080` |
| `%(fps)s` | フレームレート | `30`, `60` |
| `%(vcodec)s` | 動画コーデック | `h264`, `vp9` |
| `%(acodec)s` | 音声コーデック | `aac`, `opus` |
| `%(format)s` | フォーマット | `137 - 1080p (h264) + 140 - audio (aac)` |
| `%(format_id)s` | フォーマットID | `137+140` |

### プレイリスト

| 変数 | 説明 | 例 |
|------|------|-----|
| `%(playlist)s` | プレイリスト名 | `Best of 80s` |
| `%(playlist_title)s` | プレイリストタイトル | `Best of 80s` |
| `%(playlist_id)s` | プレイリストID | `PLrAXtmErZgOei...` |
| `%(playlist_index)s` | プレイリスト内番号 | `1`, `2`, `3` |
| `%(playlist_count)s` | プレイリスト総数 | `50` |
| `%(playlist_uploader)s` | プレイリスト作成者 | `MusicChannel` |

### その他

| 変数 | 説明 | 例 |
|------|------|-----|
| `%(webpage_url)s` | 動画のURL | `https://www.youtube.com/watch?v=...` |
| `%(original_url)s` | 元のURL | `https://youtu.be/...` |
| `%(categories)s` | カテゴリ | `Music` |
| `%(tags)s` | タグ | `music, 80s, pop` |
| `%(creator)s` | 作成者 | `Rick Astley` |
| `%(artist)s` | アーティスト | `Rick Astley` |
| `%(album)s` | アルバム | `Whenever You Need Somebody` |

## 🎨 テンプレート例

### 基本的なテンプレート

#### 1. チャンネル別に整理

```
%(uploader)s/%(title)s.%(ext)s
```

**出力:**
```
RickAstleyVEVO/Rick Astley - Never Gonna Give You Up.mp4
```

#### 2. 日付別フォルダ（年/月）

```
%(upload_date>%Y)s/%(upload_date>%m)s/%(title)s.%(ext)s
```

**出力:**
```
2009/10/Rick Astley - Never Gonna Give You Up.mp4
```

#### 3. 動画IDを含める

```
%(uploader)s/[%(id)s] %(title)s.%(ext)s
```

**出力:**
```
RickAstleyVEVO/[dQw4w9WgXcQ] Rick Astley - Never Gonna Give You Up.mp4
```

### 高度なテンプレート

#### 4. チャンネル + 年月 + 画質

```
%(uploader)s/%(upload_date>%Y-%m)s/[%(resolution)s] %(title)s.%(ext)s
```

**出力:**
```
RickAstleyVEVO/2009-10/[1080p] Rick Astley - Never Gonna Give You Up.mp4
```

#### 5. プレイリスト番号付き

```
%(uploader)s/%(playlist_title)s/%(playlist_index)02d - %(title)s.%(ext)s
```

**出力:**
```
RickAstleyVEVO/Best of Rick Astley/01 - Rick Astley - Never Gonna Give You Up.mp4
```

#### 6. 詳細情報付き

```
%(uploader)s/%(title)s - %(upload_date>%Y%m%d)s - [%(id)s] - %(resolution)s.%(ext)s
```

**出力:**
```
RickAstleyVEVO/Rick Astley - Never Gonna Give You Up - 20091025 - [dQw4w9WgXcQ] - 1080p.mp4
```

#### 7. カテゴリ別整理

```
%(categories)s/%(uploader)s/%(title)s.%(ext)s
```

**出力:**
```
Music/RickAstleyVEVO/Rick Astley - Never Gonna Give You Up.mp4
```

#### 8. 年齢制限別

```
%(age_limit>0&Adult|General)s/%(uploader)s/%(title)s.%(ext)s
```

**出力:**
```
General/RickAstleyVEVO/Rick Astley - Never Gonna Give You Up.mp4
```

## 🔧 高度な機能

### デフォルト値（`|`）

変数が存在しない場合のデフォルト値を指定できます。

```
%(playlist_title|No Playlist)s/%(title)s.%(ext)s
```

- プレイリストの一部: `Best of 80s/動画タイトル.mp4`
- 単独動画: `No Playlist/動画タイトル.mp4`

### 条件分岐（`?`）

条件に応じて出力を変更できます。

```
%(is_live&[LIVE]|[VOD])s %(title)s.%(ext)s
```

- ライブ配信: `[LIVE] 動画タイトル.mp4`
- 通常動画: `[VOD] 動画タイトル.mp4`

### 文字列置換

特定の文字を置換できます。

```
%(title)s.%(ext)s
```

yt-dlpが自動的に以下の文字を置換します：
- `/` → `_`
- `:` → `-`
- その他の不正な文字 → 安全な文字

### 日付フォーマット

strftime形式で日付をフォーマットできます。

| フォーマット | 説明 | 例 |
|-------------|------|-----|
| `%Y` | 4桁の年 | `2025` |
| `%y` | 2桁の年 | `25` |
| `%m` | 2桁の月 | `01` |
| `%d` | 2桁の日 | `22` |
| `%B` | 月名（完全） | `January` |
| `%b` | 月名（略） | `Jan` |
| `%A` | 曜日（完全） | `Wednesday` |
| `%a` | 曜日（略） | `Wed` |
| `%H` | 時（24時間） | `14` |
| `%I` | 時（12時間） | `02` |
| `%M` | 分 | `30` |
| `%S` | 秒 | `45` |

**例:**
```
%(upload_date>%Y年%m月%d日)s/%(title)s.%(ext)s
```

**出力:**
```
2009年10月25日/Rick Astley - Never Gonna Give You Up.mp4
```

### 数値フォーマット

ゼロパディングなど、数値のフォーマットを指定できます。

```
%(playlist_index)02d - %(title)s.%(ext)s
```

**出力:**
```
01 - 動画タイトル1.mp4
02 - 動画タイトル2.mp4
...
10 - 動画タイトル10.mp4
```

## ⚠️ 注意事項

### ファイル名の制限

#### Windows
- 使用できない文字: `< > : " / \ | ? *`
- 予約語: `CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`
- 最大パス長: 260文字（拡張パス有効時は32,767文字）

#### macOS/Linux
- 使用できない文字: `/`（macOSでは `:` も推奨されない）
- 最大ファイル名長: 255バイト

**解決策:**
yt-dlpは自動的に不正な文字を安全な文字に置換します。`windowsfilenames: True`オプションが有効になっています。

### 長いファイル名

タイトルが長すぎる場合、ファイル名が制限を超える可能性があります。

**対策:**
```python
# download_manager.pyで設定済み
'restrictfilenames': False,  # Unicode文字を許可
'windowsfilenames': True,    # Windows安全なファイル名
```

### 存在しない変数

テンプレートに存在しない変数を使用した場合：
- デフォルト値が指定されていれば、それを使用
- 指定されていなければ、`NA`が使用される

## 🛠️ トラブルシューティング

### Q: テンプレートが反映されない

**A:** 設定を保存した後、アプリケーションを再起動してください。

### Q: ファイル名に特殊文字が含まれてエラーになる

**A:** `windowsfilenames: True`が有効になっているため、自動的に安全な文字に置換されます。それでもエラーが出る場合は、テンプレートをシンプルにしてください。

### Q: 日付フォーマットが間違っている

**A:** strftime形式を確認してください。例: `%(upload_date>%Y-%m-%d)s`

### Q: プレビューと実際の出力が異なる

**A:** 実際の動画メタデータによって異なります。プレビューはサンプルデータを使用しています。

### Q: プレイリストの動画がすべて同じフォルダに保存される

**A:** `%(playlist_title)s`変数を含むテンプレートを使用してください：
```
%(uploader)s/%(playlist_title)s/%(title)s.%(ext)s
```

## 📚 実用例

### YouTube チャンネルアーカイブ

```
%(uploader)s/%(upload_date>%Y)s/%(upload_date>%m-%d)s - %(title)s [%(id)s].%(ext)s
```

**出力:**
```
RickAstleyVEVO/
├── 2009/
│   └── 10-25 - Rick Astley - Never Gonna Give You Up [dQw4w9WgXcQ].mp4
└── 2010/
    └── 03-15 - Rick Astley - Together Forever [yPYZpwSpKmA].mp4
```

### 音楽コレクション

```
Music/%(artist|%(uploader))s/%(album|%(playlist_title)|Unknown Album)s/%(playlist_index)02d - %(title)s.%(ext)s
```

**出力:**
```
Music/
└── Rick Astley/
    └── Whenever You Need Somebody/
        ├── 01 - Never Gonna Give You Up.mp4
        ├── 02 - Together Forever.mp4
        └── 03 - Whenever You Need Somebody.mp4
```

### 教育コンテンツ

```
Education/%(uploader)s/%(playlist_title|Single Videos)s/%(playlist_index)02d - %(title)s.%(ext)s
```

**出力:**
```
Education/
└── CrashCourse/
    ├── World History/
    │   ├── 01 - The Agricultural Revolution.mp4
    │   └── 02 - Indus Valley Civilization.mp4
    └── Single Videos/
        └── Special Episode.mp4
```

### ライブ配信アーカイブ

```
%(uploader)s/%(is_live&[LIVE]|[VOD])s/%(upload_date>%Y-%m)s/%(title)s - %(upload_date>%Y%m%d_%H%M)s.%(ext)s
```

**出力:**
```
GameChannel/
├── [LIVE]/
│   └── 2025-01/
│       └── Gaming Stream - 20250122_1430.mp4
└── [VOD]/
    └── 2025-01/
        └── Highlight Compilation - 20250123_1000.mp4
```

## 🔗 参考リンク

- [yt-dlp 公式ドキュメント - Output Template](https://github.com/yt-dlp/yt-dlp#output-template)
- [Python strftime フォーマット](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes)
- [YouTube Downloader設定ガイド](./BUILD_WINDOWS.md)

## 💡 ヒント

1. **テストモード**: 新しいテンプレートを試す前に、1つの動画でテストしてください
2. **バックアップ**: 設定を変更する前に、現在の設定をメモしておいてください
3. **シンプルに**: 複雑すぎるテンプレートは避け、必要な情報だけを含めてください
4. **整理**: ディレクトリ構造を計画的に設計し、後で見つけやすくしてください

---

**最終更新:** 2025-11-22
