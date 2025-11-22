# Chrome認証情報の暗号化ストレージ - セキュリティドキュメント

## 🔐 概要

本アプリケーションは、By Click Downloaderと同様に、Chromeブラウザからログイン情報を自動取得し、**暗号化して安全に保存**する機能を実装しています。

## 🛡️ セキュリティ設計

### 暗号化方式

#### 1. **Fernet対称暗号化**
- **アルゴリズム**: AES-128-CBC + HMAC-SHA256
- **ライブラリ**: `cryptography` (Pythonの標準的な暗号化ライブラリ)
- **認証**: HMAC により改ざん検出

#### 2. **鍵導出 (Key Derivation)**
- **方式**: PBKDF2-HMAC-SHA256
- **反復回数**: 100,000回
- **ソルト**: ランダムに生成された16バイト
- **鍵の長さ**: 256ビット

#### 3. **マシン固有の鍵**

暗号化鍵は**マシン固有のID**から導出されるため、以下の特性があります：

| プラットフォーム | 使用するID | ファイルパス |
|----------------|----------|-------------|
| Linux | /etc/machine-id | /etc/machine-id |
| macOS | IOPlatformUUID | システムレジストリ |
| Windows | WMIC UUID | WMIC コマンド出力 |
| フォールバック | ホスト名-ユーザー名 | - |

**重要な特性**:
- ✅ 暗号化されたファイルは**そのマシンでのみ**復号化可能
- ✅ 他のコンピュータにコピーしても復号化不可能
- ✅ キーファイルだけを盗まれても無意味（マシンIDが必要）

## 📁 保存されるデータ

### 抽出される情報

#### 1. **YouTube Cookie** (重要度: ⭐⭐⭐⭐⭐)
抽出されるCookie:
- `SID`, `HSID`, `SSID` - セッション識別子
- `APISID`, `SAPISID` - API認証
- `LOGIN_INFO` - ログイン情報
- `__Secure-1PSID`, `__Secure-3PSID` - セキュアセッション

**用途**: YouTubeへの認証済みアクセス、"not available on this app"エラーの回避

#### 2. **OAuth Token** (重要度: ⭐⭐⭐)
- `access_token` - アクセストークン（短期）
- `refresh_token` - リフレッシュトークン（長期）

**用途**: YouTube Data API へのアクセス

### 暗号化前のデータ構造

```json
{
  "cookies": {
    "SID": {
      "value": "actual_cookie_value",
      "domain": ".youtube.com",
      "path": "/",
      "expires": 1234567890,
      "secure": true,
      "httponly": true
    }
  },
  "tokens": {
    "access_token": "ya29.a0AfH6SMBx...",
    "refresh_token": "1//0gOW..."
  },
  "profile": "Default",
  "extracted_at": "2025-11-22T12:34:56"
}
```

### 暗号化後のデータ構造

```json
{
  "cookies": {
    "SID": {
      "value": "gAAAAABmXxYZ...[encrypted]",
      "domain": ".youtube.com",
      "path": "/",
      "expires": 1234567890,
      "secure": true,
      "httponly": true
    }
  },
  "tokens": {
    "access_token": "gAAAAABmXxYZ...[encrypted]",
    "refresh_token": "gAAAAABmXxYZ...[encrypted]"
  },
  "profile": "Default",
  "extracted_at": "2025-11-22T12:34:56",
  "_encrypted": true
}
```

**暗号化される項目**:
- ✅ Cookie の `value` フィールド
- ✅ すべてのOAuthトークン

**暗号化されない項目**:
- ❌ Cookie のメタデータ（domain, path, expires など）
- ❌ プロファイル名、抽出日時

**理由**: メタデータは暗号化の必要がなく、デバッグに有用

## 🔧 実装詳細

### ファイル構成

```
data/
├── .encryption_key          # 暗号化鍵のソルト (16 bytes)
├── chrome_auth.encrypted    # 暗号化された認証情報 (JSON)
└── youtube_cookies.txt      # 従来のCookieファイル (Netscape形式)
```

### ファイル権限

**Linux/macOS**:
```bash
-rw------- (600)  .encryption_key
-rw------- (600)  chrome_auth.encrypted
-rw-r--r-- (644)  youtube_cookies.txt
```

**Windows**:
- NTFS権限により、所有者のみアクセス可能

### 暗号化フロー

```
1. Chrome Cookie DB を読み取り
   ↓
2. 重要なCookieを抽出
   ↓
3. マシンIDを取得
   ↓
4. PBKDF2でマシンID → 暗号化鍵
   ↓
5. Fernetで各値を暗号化
   ↓
6. JSONに保存 (600パーミッション)
```

### 復号化フロー

```
1. 暗号化ファイルを読み込み
   ↓
2. マシンIDを取得
   ↓
3. ソルトを読み込み
   ↓
4. PBKDF2で暗号化鍵を再生成
   ↓
5. Fernetで各値を復号化
   ↓
6. メモリ上で使用
```

## 🚀 使用方法

### 初回セットアップ

```python
from modules.auth_manager import AuthManager
from core.service_manager import ServiceConfig

# 初期化
config = ServiceConfig()
auth_manager = AuthManager(config)

# Chrome認証情報を抽出・暗号化して保存
success = auth_manager.extract_and_save_chrome_auth('Default')

if success:
    print("✅ Chrome authentication extracted and encrypted")
```

### 自動ロード

アプリケーション起動時に自動的にロードされます：

```python
# AuthManager.start() で自動実行
auth_manager._load_encrypted_chrome_auth()

# Cookie取得
cookies = auth_manager.get_decrypted_chrome_cookies()
```

### 手動リフレッシュ

```python
# 最新のChrome認証情報で更新
auth_manager.refresh_chrome_auth('Default')
```

## 🧪 テスト方法

```bash
# テストスクリプトを実行
python test_chrome_auth.py
```

**テスト内容**:
1. Chromeプロファイルの検出
2. 認証情報の抽出
3. 暗号化と保存
4. 復号化と検証
5. ファイル権限のチェック

**期待される出力**:
```
================================================================================
Chrome Authentication Extraction Test
================================================================================

[1] Checking Chrome profiles...
✓ Found 1 Chrome profile(s): ['Default']

[2] Extracting authentication from Chrome...
🔐 Extracting authentication from Chrome profile: Default
✅ Extracted 8 important cookies from Chrome
🔒 Encrypted 8 cookies
✅ Successfully saved encrypted Chrome authentication
📁 Saved to: /path/to/data/chrome_auth.encrypted
✓ Successfully extracted and encrypted Chrome authentication

[3] Verifying encrypted storage...
✓ Encrypted file exists: /path/to/data/chrome_auth.encrypted
✓ File permissions: 600 (should be 600)
✓ Successfully loaded and decrypted credentials
✓ Cookies available: 8
  Cookie names: ['SID', 'HSID', 'SSID', 'APISID', 'SAPISID', 'LOGIN_INFO', '__Secure-1PSID', '__Secure-3PSID']

================================================================================
✅ All tests PASSED!
================================================================================
```

## ⚠️ セキュリティ上の注意事項

### 脅威モデル

#### ✅ 保護されている脅威

1. **ファイルの盗難**
   - 暗号化ファイルだけを盗まれても、マシンIDが異なるため復号化不可能

2. **ネットワーク傍受**
   - ファイルは暗号化されているため、ネットワーク経由で盗まれても安全

3. **他のユーザーによるアクセス**
   - ファイル権限により、他のユーザーは読み取り不可

4. **データの改ざん**
   - HMAC により改ざんを検出

#### ❌ 保護されていない脅威

1. **マルウェアによるメモリスキャン**
   - 復号化後のデータはメモリ上に平文で存在
   - 対策: アプリケーション実行中のみ有効

2. **root/Admin権限を持つ攻撃者**
   - システム管理者権限があれば、マシンIDも読み取り可能
   - 対策: OSレベルのセキュリティに依存

3. **物理アクセス**
   - マシンへの物理アクセスがあれば、メモリダンプ等で取得可能
   - 対策: ディスク暗号化（BitLocker, FileVault）の併用

4. **キーロガー**
   - キーストロークを記録されると、入力内容が漏洩
   - 対策: アンチウイルス、エンドポイント保護

### 推奨されるセキュリティ対策

#### レベル1: 基本（すべてのユーザー）
- ✅ OSを最新に保つ
- ✅ アンチウイルスを使用
- ✅ Chromeを常に最新版に保つ

#### レベル2: 中級（セキュリティ意識の高いユーザー）
- ✅ ディスク全体の暗号化（BitLocker/FileVault）
- ✅ ファイアウォールの有効化
- ✅ 定期的な認証情報のリフレッシュ

#### レベル3: 高度（企業/組織）
- ✅ EDR (Endpoint Detection and Response)
- ✅ アプリケーションホワイトリスティング
- ✅ ネットワーク分離
- ✅ ログ監視

## 🔄 認証情報のライフサイクル

### 1. 抽出 (Extract)
```bash
# 手動実行
python test_chrome_auth.py

# またはGUI/APIから
auth_manager.extract_and_save_chrome_auth()
```

### 2. 使用 (Use)
```bash
# アプリケーション起動時に自動ロード
# yt-dlpにCookieとして渡される
```

### 3. リフレッシュ (Refresh)
```bash
# 推奨: 週に1回
auth_manager.refresh_chrome_auth()
```

### 4. 削除 (Delete)
```bash
# ログアウト時
auth_manager.logout()
rm data/chrome_auth.encrypted
```

## 📊 セキュリティ比較

| 方式 | 安全性 | 利便性 | 転送可能性 |
|------|--------|--------|-----------|
| **本実装（暗号化）** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ |
| 平文Cookie保存 | ⭐ | ⭐⭐⭐⭐⭐ | ✅ |
| Chromeから都度読み取り | ⭐⭐⭐ | ⭐⭐ | ❌ |
| OAuth のみ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ (要設定) |
| By Click Downloader方式 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ |

**本実装の利点**:
- 🔐 認証情報が暗号化されている
- 🚀 自動的にChromeから取得
- 🔄 簡単にリフレッシュ可能
- 🎯 YouTube専用に最適化

## 🆚 By Click Downloaderとの比較

| 機能 | By Click Downloader | 本実装 |
|------|---------------------|--------|
| Chrome認証取得 | ✅ | ✅ |
| 暗号化保存 | ✅ | ✅ |
| マシン固有鍵 | ✅ | ✅ |
| OAuth Token | ❌ | ✅ (ベストエフォート) |
| オープンソース | ❌ | ✅ |
| クロスプラットフォーム | Windows のみ | Windows/Mac/Linux |

## 🛠️ トラブルシューティング

### エラー1: "No Chrome profiles found"

**原因**: Chromeがインストールされていない、または非標準の場所にインストールされている

**解決策**:
```bash
# Chromeのインストール確認
# Linux
ls ~/.config/google-chrome

# macOS
ls ~/Library/Application\ Support/Google/Chrome

# Windows
dir %LOCALAPPDATA%\Google\Chrome
```

### エラー2: "Failed to decrypt cookie"

**原因**: 暗号化鍵が変更された、または別のマシンで作成されたファイル

**解決策**:
```bash
# 暗号化ファイルを削除して再作成
rm data/chrome_auth.encrypted
rm data/.encryption_key
python test_chrome_auth.py
```

### エラー3: "Chrome is currently running"

**原因**: ChromeがCookieデータベースをロックしている

**解決策**:
```bash
# Chromeを完全に閉じる
# タスクマネージャー/Activity Monitorで確認
# その後、再試行
```

## 📚 参考文献

- [Cryptography Library](https://cryptography.io/)
- [Fernet Specification](https://github.com/fernet/spec/)
- [PBKDF2 RFC 2898](https://tools.ietf.org/html/rfc2898)
- [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)

---

**免責事項**: この機能は個人利用を想定しています。企業環境で使用する場合は、組織のセキュリティポリシーを確認してください。
