"""Settings tab for YouTube Downloader GUI"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QGroupBox, QCheckBox,
    QSpinBox, QFileDialog, QComboBox, QMessageBox,
    QTextEdit, QToolButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from config.settings import settings
from utils.logger import logger


class SettingsTab(QWidget):
    """Settings tab widget"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.auth_manager = None
        self.encode_manager = None
        self.db_manager = None

        self._init_ui()

    def set_managers(self, auth_manager, encode_manager, db_manager):
        """Set managers"""
        self.auth_manager = auth_manager
        self.encode_manager = encode_manager
        self.db_manager = db_manager
        self._load_settings()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Download settings
        download_group = QGroupBox("ダウンロード設定")
        download_layout = QVBoxLayout()
        download_group.setLayout(download_layout)

        # Download directory
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("保存先:"))
        self.download_dir_input = QLineEdit()
        self.download_dir_input.setText(str(settings.DOWNLOAD_DIR))
        dir_layout.addWidget(self.download_dir_input)

        browse_button = QPushButton("参照")
        browse_button.clicked.connect(self._browse_directory)
        dir_layout.addWidget(browse_button)
        download_layout.addLayout(dir_layout)

        # Max concurrent downloads
        concurrent_layout = QHBoxLayout()
        concurrent_layout.addWidget(QLabel("同時ダウンロード数:"))
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setMinimum(1)
        self.concurrent_spin.setMaximum(10)
        self.concurrent_spin.setValue(settings.MAX_CONCURRENT_DOWNLOADS)
        concurrent_layout.addWidget(self.concurrent_spin)
        concurrent_layout.addStretch()
        download_layout.addLayout(concurrent_layout)

        # Output template settings
        template_layout = QVBoxLayout()
        template_layout.addWidget(QLabel("出力テンプレート:"))

        # Preset selector
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("プリセット:"))
        self.template_preset_combo = QComboBox()
        self.template_preset_combo.addItems([
            "チャンネル別 (channel)",
            "日付別 (date)",
            "チャンネル+日付 (channel_date)",
            "チャンネル+種類 (channel_type)",
            "フラット (flat)",
            "詳細付き (detailed)",
            "画質別 (quality)",
            "カスタム (custom)"
        ])
        self.template_preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self.template_preset_combo)
        preset_layout.addStretch()
        template_layout.addLayout(preset_layout)

        # Custom template input
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("カスタムテンプレート:"))
        self.custom_template_input = QLineEdit()
        self.custom_template_input.setText(settings.CUSTOM_OUTPUT_TEMPLATE)
        self.custom_template_input.setPlaceholderText("例: %(uploader)s/%(title)s.%(ext)s")
        custom_layout.addWidget(self.custom_template_input)

        # Help button
        help_button = QPushButton("?")
        help_button.setMaximumWidth(30)
        help_button.clicked.connect(self._show_template_help)
        custom_layout.addWidget(help_button)
        template_layout.addLayout(custom_layout)

        # Template preview
        self.template_preview_label = QLabel("プレビュー: チャンネル名/動画タイトル.mp4")
        self.template_preview_label.setWordWrap(True)
        self.template_preview_label.setStyleSheet("color: gray; font-style: italic;")
        template_layout.addWidget(self.template_preview_label)

        download_layout.addLayout(template_layout)

        layout.addWidget(download_group)

        # GPU settings
        gpu_group = QGroupBox("GPU設定")
        gpu_layout = QVBoxLayout()
        gpu_group.setLayout(gpu_layout)

        self.gpu_checkbox = QCheckBox("GPU アクセラレーションを有効にする")
        self.gpu_checkbox.setChecked(settings.ENABLE_GPU)
        gpu_layout.addWidget(self.gpu_checkbox)

        gpu_encoder_layout = QHBoxLayout()
        gpu_encoder_layout.addWidget(QLabel("GPU エンコーダー:"))
        self.gpu_encoder_combo = QComboBox()
        self.gpu_encoder_combo.addItems(["自動", "NVENC (NVIDIA)", "QuickSync (Intel)", "AMF (AMD)"])
        gpu_encoder_layout.addWidget(self.gpu_encoder_combo)
        gpu_encoder_layout.addStretch()
        gpu_layout.addLayout(gpu_encoder_layout)

        layout.addWidget(gpu_group)

        # Authentication
        auth_group = QGroupBox("認証")
        auth_layout = QVBoxLayout()
        auth_group.setLayout(auth_layout)

        self.auth_status_label = QLabel("認証状態: 未認証")
        auth_layout.addWidget(self.auth_status_label)

        auth_button_layout = QHBoxLayout()
        self.login_button = QPushButton("Google ログイン")
        self.login_button.clicked.connect(self._login)
        self.logout_button = QPushButton("ログアウト")
        self.logout_button.clicked.connect(self._logout)
        auth_button_layout.addWidget(self.login_button)
        auth_button_layout.addWidget(self.logout_button)
        auth_button_layout.addStretch()
        auth_layout.addLayout(auth_button_layout)

        layout.addWidget(auth_group)

        # Save button
        save_layout = QHBoxLayout()
        save_button = QPushButton("設定を保存")
        save_button.clicked.connect(self._save_settings)
        save_layout.addWidget(save_button)
        save_layout.addStretch()
        layout.addLayout(save_layout)

        layout.addStretch()

    def _browse_directory(self):
        """Browse for download directory"""
        directory = QFileDialog.getExistingDirectory(
            self,
            "ダウンロード保存先を選択",
            str(settings.DOWNLOAD_DIR)
        )

        if directory:
            self.download_dir_input.setText(directory)

    def _on_preset_changed(self, index):
        """Handle preset selection change"""
        preset_map = {
            0: "channel",
            1: "date",
            2: "channel_date",
            3: "channel_type",
            4: "flat",
            5: "detailed",
            6: "quality",
            7: "custom"
        }

        preset_key = preset_map.get(index, "channel")

        # Enable/disable custom template input
        self.custom_template_input.setEnabled(preset_key == "custom")

        # Update preview
        if preset_key == "custom":
            template = self.custom_template_input.text()
            self.template_preview_label.setText(f"プレビュー: {template.replace('%(uploader)s', 'チャンネル名').replace('%(title)s', '動画タイトル').replace('%(ext)s', 'mp4').replace('%(upload_date>%Y)s', '2025').replace('%(upload_date>%m)s', '01').replace('%(upload_date>%Y-%m)s', '2025-01').replace('%(id)s', 'dQw4w9WgXcQ').replace('%(resolution)s', '1080p')}")
        elif preset_key in settings.OUTPUT_TEMPLATE_PRESETS:
            template = settings.OUTPUT_TEMPLATE_PRESETS[preset_key]
            self.template_preview_label.setText(f"プレビュー: {template.replace('%(uploader)s', 'チャンネル名').replace('%(title)s', '動画タイトル').replace('%(ext)s', 'mp4').replace('%(upload_date>%Y)s', '2025').replace('%(upload_date>%m)s', '01').replace('%(upload_date>%Y-%m)s', '2025-01').replace('%(id)s', 'dQw4w9WgXcQ').replace('%(resolution)s', '1080p').replace('%(playlist_title|)s', 'プレイリスト名')}")

    def _show_template_help(self):
        """Show help dialog for output templates"""
        help_text = """
<h3>yt-dlp 出力テンプレート</h3>

<p>yt-dlpの強力な出力テンプレート機能を使用して、ダウンロードしたファイルの保存先とファイル名を自由にカスタマイズできます。</p>

<h4>📁 よく使う変数:</h4>
<ul>
<li><b>%(title)s</b> - 動画のタイトル</li>
<li><b>%(uploader)s</b> - チャンネル名/アップローダー名</li>
<li><b>%(id)s</b> - 動画ID（例: dQw4w9WgXcQ）</li>
<li><b>%(ext)s</b> - ファイル拡張子（mp4, webmなど）</li>
<li><b>%(upload_date)s</b> - アップロード日（YYYYMMDD形式）</li>
<li><b>%(upload_date>%Y)s</b> - アップロード年（例: 2025）</li>
<li><b>%(upload_date>%m)s</b> - アップロード月（例: 01）</li>
<li><b>%(upload_date>%Y-%m)s</b> - 年-月（例: 2025-01）</li>
<li><b>%(resolution)s</b> - 解像度（例: 1080p）</li>
<li><b>%(duration)s</b> - 動画の長さ（秒）</li>
<li><b>%(view_count)s</b> - 再生回数</li>
<li><b>%(like_count)s</b> - いいね数</li>
<li><b>%(playlist_title)s</b> - プレイリスト名</li>
<li><b>%(playlist_index)s</b> - プレイリスト内番号</li>
</ul>

<h4>📝 テンプレート例:</h4>
<ul>
<li><code>%(uploader)s/%(title)s.%(ext)s</code><br>
→ チャンネル名/動画タイトル.mp4</li>

<li><code>%(upload_date>%Y)s/%(upload_date>%m)s/%(title)s.%(ext)s</code><br>
→ 2025/01/動画タイトル.mp4</li>

<li><code>%(uploader)s/[%(id)s] %(title)s.%(ext)s</code><br>
→ チャンネル名/[dQw4w9WgXcQ] 動画タイトル.mp4</li>

<li><code>%(uploader)s/%(upload_date>%Y-%m)s/%(title)s.%(ext)s</code><br>
→ チャンネル名/2025-01/動画タイトル.mp4</li>

<li><code>%(resolution)s/%(uploader)s - %(title)s.%(ext)s</code><br>
→ 1080p/チャンネル名 - 動画タイトル.mp4</li>
</ul>

<h4>🔧 高度な機能:</h4>
<ul>
<li><b>|</b> - デフォルト値: <code>%(playlist_title|No Playlist)s</code></li>
<li><b>&amp;</b> - 複数値の結合</li>
<li><b>?</b> - 条件分岐</li>
</ul>

<p>詳細: <a href="https://github.com/yt-dlp/yt-dlp#output-template">yt-dlp Output Template Documentation</a></p>
"""

        msg = QMessageBox(self)
        msg.setWindowTitle("出力テンプレート ヘルプ")
        msg.setTextFormat(Qt.RichText)
        msg.setText(help_text)
        msg.setIcon(QMessageBox.Information)
        msg.exec()

    def _login(self):
        """Login with Google"""
        if not self.auth_manager:
            QMessageBox.warning(self, "エラー", "認証マネージャーが初期化されていません")
            return

        QMessageBox.information(
            self,
            "認証",
            "client_secrets.json ファイルを選択してください"
        )

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "client_secrets.json を選択",
            "",
            "JSON Files (*.json)"
        )

        if file_path:
            try:
                import asyncio
                from gui.main_window import MainWindow
                parent = self.window()
                if isinstance(parent, MainWindow) and parent.service_thread and parent.service_thread.loop:
                    future = asyncio.run_coroutine_threadsafe(
                        self.auth_manager.authenticate_google(file_path),
                        parent.service_thread.loop
                    )
                    success = future.result(timeout=60)

                    if success:
                        self.auth_status_label.setText("認証状態: 認証済み")
                        QMessageBox.information(self, "成功", "認証に成功しました")
                    else:
                        QMessageBox.warning(self, "エラー", "認証に失敗しました")
                else:
                    raise RuntimeError("イベントループが初期化されていません")

            except Exception as e:
                QMessageBox.critical(self, "エラー", f"認証中にエラーが発生しました:\n{str(e)}")
                logger.error(f"Login error: {e}", exc_info=True)

    def _logout(self):
        """Logout"""
        if not self.auth_manager:
            return

        self.auth_manager.logout()
        self.auth_status_label.setText("認証状態: 未認証")
        QMessageBox.information(self, "完了", "ログアウトしました")

    def _save_settings(self):
        """Save settings"""
        try:
            # Update settings
            settings.DOWNLOAD_DIR = self.download_dir_input.text()
            settings.MAX_CONCURRENT_DOWNLOADS = self.concurrent_spin.value()
            settings.ENABLE_GPU = self.gpu_checkbox.isChecked()

            # Get selected preset
            preset_map = {
                0: "channel",
                1: "date",
                2: "channel_date",
                3: "channel_type",
                4: "flat",
                5: "detailed",
                6: "quality",
                7: "custom"
            }
            preset_key = preset_map.get(self.template_preset_combo.currentIndex(), "channel")
            settings.DIRECTORY_STRUCTURE = preset_key
            settings.CUSTOM_OUTPUT_TEMPLATE = self.custom_template_input.text()

            # Save to database
            if self.db_manager:
                self.db_manager.set_setting('download_dir', str(settings.DOWNLOAD_DIR))
                self.db_manager.set_setting('max_concurrent_downloads', settings.MAX_CONCURRENT_DOWNLOADS)
                self.db_manager.set_setting('enable_gpu', settings.ENABLE_GPU)
                self.db_manager.set_setting('directory_structure', settings.DIRECTORY_STRUCTURE)
                self.db_manager.set_setting('custom_output_template', settings.CUSTOM_OUTPUT_TEMPLATE)

            QMessageBox.information(self, "成功", "設定を保存しました")

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"設定の保存に失敗しました:\n{str(e)}")
            logger.error(f"Failed to save settings: {e}")

    def _load_settings(self):
        """Load settings from database"""
        if not self.db_manager:
            return

        try:
            # Load from database
            download_dir = self.db_manager.get_setting('download_dir')
            if download_dir:
                self.download_dir_input.setText(download_dir)

            max_concurrent = self.db_manager.get_setting('max_concurrent_downloads')
            if max_concurrent:
                self.concurrent_spin.setValue(int(max_concurrent))

            enable_gpu = self.db_manager.get_setting('enable_gpu')
            if enable_gpu is not None:
                self.gpu_checkbox.setChecked(bool(enable_gpu))

            # Load output template settings
            directory_structure = self.db_manager.get_setting('directory_structure')
            if directory_structure:
                # Map structure to combo box index
                preset_index_map = {
                    "channel": 0,
                    "date": 1,
                    "channel_date": 2,
                    "channel_type": 3,
                    "flat": 4,
                    "detailed": 5,
                    "quality": 6,
                    "custom": 7
                }
                index = preset_index_map.get(directory_structure, 0)
                self.template_preset_combo.setCurrentIndex(index)

            custom_template = self.db_manager.get_setting('custom_output_template')
            if custom_template:
                self.custom_template_input.setText(custom_template)

            # Update auth status
            if self.auth_manager and self.auth_manager.is_authenticated():
                self.auth_status_label.setText("認証状態: 認証済み")

        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
