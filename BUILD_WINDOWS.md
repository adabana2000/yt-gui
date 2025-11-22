# Windows Native Application Build Guide

## 概要

このガイドでは、YouTube Downloaderアプリケーションを **Windows単体実行ファイル（.exe）** としてビルドする方法を説明します。

ビルドされた.exeファイルは：
- ✅ Pythonのインストール不要で実行可能
- ✅ すべての依存関係が組み込み済み
- ✅ ダブルクリックで起動
- ✅ 他のWindowsコンピュータに配布可能

## 必要な環境

### オプション1: Windowsマシンでビルド（推奨）

**必要なもの:**
- Windows 10/11 (64-bit)
- Python 3.10 以上
- 4GB以上の空きディスク容量
- インターネット接続（初回のみ）

### オプション2: Linux/macOSでクロスコンパイル

**必要なもの:**
- Linux または macOS
- Python 3.10 以上
- Wine（テスト用、オプション）
- 4GB以上の空きディスク容量

**注意:** クロスコンパイルした実行ファイルは、Windows Defenderなどのアンチウイルスソフトで誤検知される可能性があります。配布用には、ネイティブWindowsマシンでのビルドを推奨します。

## クイックスタート

### Windowsマシンの場合

1. **必要なパッケージをインストール:**
   ```cmd
   pip install -r requirements.txt
   ```

2. **ビルドスクリプトを実行:**
   ```cmd
   build_windows.bat
   ```

3. **完成！**
   ```
   dist/YouTubeDownloader.exe
   ```
   このファイルをダブルクリックして起動できます。

### Linux/macOSの場合

1. **必要なパッケージをインストール:**
   ```bash
   pip3 install -r requirements.txt
   ```

2. **ビルドスクリプトを実行:**
   ```bash
   chmod +x build_windows.sh
   ./build_windows.sh
   ```

3. **完成！**
   ```
   dist/YouTubeDownloader.exe
   ```
   このファイルをWindowsマシンに転送して使用します。

## 詳細な手順

### ステップ1: 環境準備

#### Python 3.10以上のインストール

**Windows:**
1. https://www.python.org/downloads/ からPythonをダウンロード
2. インストール時に「Add Python to PATH」にチェック
3. インストール完了後、コマンドプロンプトで確認:
   ```cmd
   python --version
   ```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip
```

**macOS:**
```bash
brew install python@3.10
```

#### 依存関係のインストール

プロジェクトディレクトリで：
```bash
# Windows
pip install -r requirements.txt

# Linux/macOS
pip3 install -r requirements.txt
```

### ステップ2: ビルド実行

#### Windowsの場合

**方法1: バッチファイル実行（簡単）**
```cmd
build_windows.bat
```

**方法2: PyInstallerを直接実行**
```cmd
pyinstaller --clean --noconfirm youtube-downloader.spec
```

#### Linux/macOSの場合

**方法1: シェルスクリプト実行（簡単）**
```bash
./build_windows.sh
```

**方法2: PyInstallerを直接実行**
```bash
pyinstaller --clean --noconfirm youtube-downloader.spec
```

### ステップ3: 実行ファイルの確認

ビルドが成功すると、以下の場所に実行ファイルが生成されます：
```
dist/YouTubeDownloader.exe
```

**ファイルサイズ:** 約80-150MB（すべての依存関係を含む）

### ステップ4: 動作確認

**Windowsマシンで:**
1. `dist/YouTubeDownloader.exe` をダブルクリック
2. GUIウィンドウが開くことを確認
3. 初回起動時は、Windows Defenderがスキャンするため起動が遅い場合があります

**Wineでテスト（Linux/macOS）:**
```bash
wine dist/YouTubeDownloader.exe
```

## ビルド設定のカスタマイズ

### アイコンの変更

1. `.ico`形式のアイコンファイルを用意
2. `youtube-downloader.spec` の以下の行をアンコメント:
   ```python
   # icon='resources/icon.ico',
   ```
3. パスを実際のアイコンファイルに変更:
   ```python
   icon='path/to/your/icon.ico',
   ```

### バージョン情報の追加

Windowsの実行ファイルに製品情報を埋め込むには：

1. バージョンファイルを作成:
   ```python
   # file_version_info.txt
   VSVersionInfo(
     ffi=FixedFileInfo(
       filevers=(1, 0, 0, 0),
       prodvers=(1, 0, 0, 0),
       mask=0x3f,
       flags=0x0,
       OS=0x40004,
       fileType=0x1,
       subtype=0x0,
       date=(0, 0)
     ),
     kids=[
       StringFileInfo([
         StringTable(
           '040904B0',
           [StringStruct('CompanyName', 'Your Company'),
            StringStruct('FileDescription', 'YouTube Downloader'),
            StringStruct('FileVersion', '1.0.0.0'),
            StringStruct('ProductName', 'YouTube Downloader'),
            StringStruct('ProductVersion', '1.0.0.0')])
       ]),
       VarFileInfo([VarStruct('Translation', [1033, 1200])])
     ]
   )
   ```

2. `youtube-downloader.spec` で指定:
   ```python
   version_file='file_version_info.txt',
   ```

### ビルドサイズの削減

実行ファイルのサイズを小さくしたい場合：

1. **UPX圧縮を有効化（既定で有効）:**
   ```python
   upx=True,
   ```

2. **不要なモジュールを除外:**
   `youtube-downloader.spec` の `excludes` リストに追加:
   ```python
   excludes=[
       'tkinter',
       'matplotlib',
       'IPython',
       'jupyter',
   ],
   ```

3. **フォルダベース配布（単一ファイルの代わり）:**
   `youtube-downloader.spec` の最後のCOLLECTセクションをアンコメント

### コンソールウィンドウの表示

デバッグ用にコンソールウィンドウを表示したい場合：

`youtube-downloader.spec` で：
```python
console=True,  # コンソールウィンドウを表示
```

## トラブルシューティング

### ビルドエラー

#### エラー: "ModuleNotFoundError: No module named 'xxx'"

**原因:** 必要なモジュールがインストールされていない

**解決策:**
```bash
pip install -r requirements.txt
```

#### エラー: "UnicodeDecodeError"

**原因:** ファイルのエンコーディング問題

**解決策:**
```bash
# クリーンビルド
rmdir /s /q build dist
pyinstaller --clean youtube-downloader.spec
```

#### エラー: "RecursionError: maximum recursion depth exceeded"

**原因:** 複雑な依存関係

**解決策:**
`youtube-downloader.spec` に追加:
```python
import sys
sys.setrecursionlimit(5000)
```

### 実行時エラー

#### 起動しない / すぐにクラッシュする

**デバッグ方法:**
1. コンソールモードでビルド:
   ```python
   console=True,
   ```
2. エラーメッセージを確認
3. 不足しているモジュールを `hiddenimports` に追加

#### "Failed to execute script"エラー

**原因:** 必要なデータファイルや依存関係が含まれていない

**解決策:**
1. `youtube-downloader.spec` の `datas` にファイルを追加
2. `hiddenimports` に不足しているモジュールを追加

#### Windows Defenderが警告を出す

**原因:** PyInstallerで作成された実行ファイルは、署名がないため警告が出ることがある

**解決策:**
1. 「詳細情報」→「実行」で起動可能
2. コード署名証明書で署名（有料）
3. VirusTotalにアップロードして誤検知を報告

### パフォーマンス問題

#### 起動が遅い

**原因:**
- 初回起動時にWindows Defenderがスキャン
- すべての依存関係を展開する必要がある

**対策:**
- 2回目以降は高速化される
- SSDを使用
- Windows Defenderの除外リストに追加

#### ファイルサイズが大きい

**対策:**
1. UPX圧縮を有効化（既定で有効）
2. 不要なモジュールを除外
3. フォルダベース配布に変更（COLLECT使用）

## 配布方法

### 単一ファイル配布

**最も簡単:**
```
YouTubeDownloader.exe
```
をそのまま配布。受信者はダブルクリックで実行可能。

### インストーラー作成

より専門的な配布には、Inno SetupやNSISを使用してインストーラーを作成できます。

**Inno Setupの例:**
```iss
[Setup]
AppName=YouTube Downloader
AppVersion=1.0
DefaultDirName={pf}\YouTubeDownloader
DefaultGroupName=YouTube Downloader
OutputDir=installer
OutputBaseFilename=YouTubeDownloader_Setup

[Files]
Source: "dist\YouTubeDownloader.exe"; DestDir: "{app}"

[Icons]
Name: "{group}\YouTube Downloader"; Filename: "{app}\YouTubeDownloader.exe"
Name: "{commondesktop}\YouTube Downloader"; Filename: "{app}\YouTubeDownloader.exe"
```

### 配布時の注意事項

1. **ライセンス:**
   - yt-dlpのライセンス（Unlicense）を確認
   - 依存ライブラリのライセンスを確認

2. **YouTube利用規約:**
   - 個人利用、教育・研究目的での使用を推奨
   - 商用利用時は規約を確認

3. **アンチウイルス:**
   - VirusTotalでスキャン
   - 誤検知が出る場合は、アンチウイルスベンダーに報告

4. **サポート:**
   - README.mdを含める
   - 連絡先を明記
   - 既知の問題を文書化

## 高度な設定

### マルチプラットフォームビルド

GitHub Actionsを使用した自動ビルド例:

```yaml
name: Build Executables

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pyinstaller youtube-downloader.spec
      - uses: actions/upload-artifact@v3
        with:
          name: YouTubeDownloader-Windows
          path: dist/YouTubeDownloader.exe
```

### デジタル署名

Windowsコード署名証明書を使用して署名:

```bash
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist/YouTubeDownloader.exe
```

## まとめ

### ビルドの流れ

```
1. 依存関係をインストール
   ↓
2. ビルドスクリプト実行
   ↓
3. PyInstallerが実行ファイル生成
   ↓
4. dist/YouTubeDownloader.exe 完成
   ↓
5. 配布・実行
```

### よく使うコマンド

```bash
# 通常のビルド
build_windows.bat

# クリーンビルド
pyinstaller --clean youtube-downloader.spec

# デバッグビルド（コンソール表示）
# youtube-downloader.spec で console=True に変更してから
pyinstaller youtube-downloader.spec

# ビルドファイルのクリーンアップ
rmdir /s /q build dist
```

### サポート

問題が発生した場合：
1. このドキュメントのトラブルシューティングを確認
2. PyInstallerのドキュメント: https://pyinstaller.org/
3. GitHubのIssuesで報告

---

**最終更新:** 2025-11-22
