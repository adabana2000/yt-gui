# GUI履歴タブ問題 - 修正サマリー

## 問題の症状

履歴タブにデータが何も表示されない
- エラーメッセージは表示されない
- レイアウトは正常
- データベースにはデータが保存されているはず

## 根本原因

**SQLAlchemy DetachedInstanceError**

データベースマネージャー（`db_manager.py`）のセッション設定に問題がありました：

```python
# 問題のあったコード
self.SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=self.engine
)
```

### 何が起きていたか

1. `get_download_history()` メソッドが `with self.get_session()` コンテキストマネージャーを使用
2. コンテキストマネージャーを抜けると、セッションが自動的にクローズ
3. セッションがクローズされると、取得したオブジェクトが**detached**状態になる
4. detached状態のオブジェクトの属性にアクセスしようとすると `DetachedInstanceError` が発生
5. GUIの履歴タブでデータを表示しようとすると、エラーで失敗（例外は内部でキャッチされるため、ユーザーには見えない）

## 解決策

`sessionmaker` に `expire_on_commit=False` オプションを追加：

```python
# 修正後のコード
self.SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=self.engine,
    expire_on_commit=False  # セッションクローズ後もオブジェクトにアクセス可能
)
```

### `expire_on_commit=False` の効果

- セッションがコミット/クローズされても、オブジェクトの属性が有効なまま
- GUIなど、非同期的にデータにアクセスする場合に必須
- パフォーマンス上の懸念はほとんどない（読み取り専用の使用が中心のため）

## 修正ファイル

### database/db_manager.py
- `SessionLocal` の初期化に `expire_on_commit=False` を追加（36行目）

## テストスクリプト

修正を検証するために、2つのテストスクリプトを追加しました：

### 1. test_db_history.py
データベースからの履歴取得をテストするスクリプト：

```bash
python test_db_history.py
```

**機能:**
- データベースに保存された履歴レコードを取得
- 統計情報を表示
- データが空の場合、テストデータを1件追加

### 2. add_test_history.py
テストデータを複数追加するスクリプト：

```bash
python add_test_history.py
```

**機能:**
- 5つのサンプル動画データを追加
- 日本語タイトル、チャンネル名を含むリアルなデータ
- すべての履歴レコードと統計を表示

## 動作確認方法

### 1. コマンドラインでテスト

```bash
# データベースに履歴データがあるか確認
python test_db_history.py

# テストデータを追加（初回のみ）
python add_test_history.py
```

### 2. GUIで確認

```bash
# GUIを起動
python main.py --mode gui
```

1. 「履歴」タブを開く
2. テストデータが表示されることを確認
3. 以下が表示されるはず：
   - タイトル列：動画のタイトル
   - チャンネル列：チャンネル名
   - ダウンロード日時列：日時
   - ファイルパス列：ファイルのパス
   - サイズ列：ファイルサイズ（MB単位）
4. 統計セクションに以下が表示される：
   - 総ダウンロード数
   - 総ダウンロードサイズ（GB単位）
   - 過去7日間のダウンロード数

### 3. 実際のダウンロードでテスト

```bash
# 実際に動画をダウンロード
python main.py --mode cli --url "https://www.youtube.com/watch?v=jNQXAC9IVRw"

# GUIで履歴を確認
python main.py --mode gui
```

## 期待される結果

✅ 履歴タブにダウンロード履歴が表示される
✅ タイトル、チャンネル名、日時、ファイルパス、サイズが正しく表示される
✅ ページネーション（前へ/次へボタン）が動作する
✅ 検索機能が動作する
✅ 統計情報が正しく表示される

## 技術的な詳細

### SQLAlchemyのセッション管理

**expire_on_commit=True（デフォルト）の動作:**
```python
with session:
    obj = session.query(Model).first()
    session.commit()
# ここでobj.attributeにアクセスすると、データベースに再クエリが発生
# セッションが閉じられている場合、DetachedInstanceError
```

**expire_on_commit=False の動作:**
```python
with session:
    obj = session.query(Model).first()
    session.commit()
# ここでobj.attributeに自由にアクセス可能（キャッシュされた値を使用）
```

### なぜGUIアプリで必要か

- GUIアプリでは、データ取得とUI表示が非同期
- データベースセッションはできるだけ短く保つべき（ベストプラクティス）
- セッションを閉じた後にUI側でオブジェクトの属性にアクセスする必要がある
- `expire_on_commit=False` により、この問題を解決

### 代替案との比較

| 方法 | メリット | デメリット |
|------|---------|-----------|
| `expire_on_commit=False` | シンプル、コード変更最小 | オブジェクトが古いデータを持つ可能性 |
| オブジェクトをdictに変換 | データの一貫性が保証される | 追加のコード、型安全性の低下 |
| DTOクラス使用 | 明確な境界、型安全 | ボイラープレートコード増加 |

本アプリケーションでは、読み取り専用の履歴データを扱うため、`expire_on_commit=False` が最適です。

## 関連する変更

この修正により、以下のすべての機能が正常に動作するようになります：

1. **履歴タブ** - ダウンロード履歴の表示
2. **統計表示** - 総ダウンロード数、サイズ、期間別統計
3. **検索機能** - タイトル・チャンネル名での検索
4. **ページネーション** - 大量の履歴を効率的に表示
5. **重複チェック** - すでにダウンロードした動画の検出

## トラブルシューティング

### 履歴タブが空のまま

1. データベースに実際にデータがあるか確認：
   ```bash
   python test_db_history.py
   ```

2. テストデータを追加：
   ```bash
   python add_test_history.py
   ```

3. データベースファイルの場所を確認：
   ```bash
   ls -la data/youtube_downloader.db
   ```

### エラーが表示される

ログファイルを確認：
```bash
cat logs/*.log | tail -100
```

### データベースをリセットしたい

```bash
rm data/youtube_downloader.db
python test_db_history.py  # 新しいDBを作成してテストデータ追加
```

## まとめ

**問題**: 履歴タブにデータが表示されない（SQLAlchemy DetachedInstanceError）

**原因**: セッションクローズ後のオブジェクトアクセス

**解決**: `expire_on_commit=False` を追加

**影響**: すべてのデータベース読み取り操作が正常に動作

**テスト**: test_db_history.py と add_test_history.py で検証可能
