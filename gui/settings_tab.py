"""Settings tab for YouTube Downloader GUI"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QGroupBox, QCheckBox,
    QSpinBox, QFileDialog, QComboBox, QMessageBox
)
from PySide6.QtCore import Qt

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

            # Save to database
            if self.db_manager:
                self.db_manager.set_setting('download_dir', str(settings.DOWNLOAD_DIR))
                self.db_manager.set_setting('max_concurrent_downloads', settings.MAX_CONCURRENT_DOWNLOADS)
                self.db_manager.set_setting('enable_gpu', settings.ENABLE_GPU)

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

            # Update auth status
            if self.auth_manager and self.auth_manager.is_authenticated():
                self.auth_status_label.setText("認証状態: 認証済み")

        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
