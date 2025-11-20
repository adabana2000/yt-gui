"""Download tab for YouTube Downloader GUI"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QLabel, QProgressBar,
    QMessageBox, QGroupBox, QSpinBox
)
from PySide6.QtCore import Qt, QTimer
import asyncio

from utils.logger import logger


class DownloadTab(QWidget):
    """Download tab widget"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.download_manager = None
        self.db_manager = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_downloads)

        self._init_ui()

    def set_managers(self, download_manager, db_manager):
        """Set managers and start updates"""
        self.download_manager = download_manager
        self.db_manager = db_manager
        self.timer.start(1000)  # Update every second

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # URL input section
        input_group = QGroupBox("ダウンロード追加")
        input_layout = QVBoxLayout()
        input_group.setLayout(input_layout)

        # URL input
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("YouTube URL を入力してください...")
        self.url_input.returnPressed.connect(self._add_download)
        url_layout.addWidget(QLabel("URL:"))
        url_layout.addWidget(self.url_input)
        input_layout.addLayout(url_layout)

        # Options
        options_layout = QHBoxLayout()

        # Quality selection
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["最高品質", "1080p", "720p", "480p", "360p", "音声のみ"])
        options_layout.addWidget(QLabel("品質:"))
        options_layout.addWidget(self.quality_combo)

        # Priority
        self.priority_spin = QSpinBox()
        self.priority_spin.setMinimum(1)
        self.priority_spin.setMaximum(10)
        self.priority_spin.setValue(5)
        options_layout.addWidget(QLabel("優先度:"))
        options_layout.addWidget(self.priority_spin)

        options_layout.addStretch()
        input_layout.addLayout(options_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("動画ダウンロード")
        self.add_button.clicked.connect(self._add_download)
        self.channel_button = QPushButton("チャンネル全動画")
        self.channel_button.clicked.connect(self._add_channel_download)
        self.playlist_button = QPushButton("プレイリスト")
        self.playlist_button.clicked.connect(self._add_playlist_download)
        self.info_button = QPushButton("動画情報取得")
        self.info_button.clicked.connect(self._get_video_info)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.channel_button)
        button_layout.addWidget(self.playlist_button)
        button_layout.addWidget(self.info_button)
        button_layout.addStretch()
        input_layout.addLayout(button_layout)

        layout.addWidget(input_group)

        # Active downloads table
        downloads_group = QGroupBox("ダウンロード中")
        downloads_layout = QVBoxLayout()
        downloads_group.setLayout(downloads_layout)

        self.downloads_table = QTableWidget()
        self.downloads_table.setColumnCount(6)
        self.downloads_table.setHorizontalHeaderLabels([
            "タイトル", "進捗", "速度", "残り時間", "ステータス", "操作"
        ])
        self.downloads_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        downloads_layout.addWidget(self.downloads_table)

        layout.addWidget(downloads_group)

    def _add_download(self):
        """Add download to queue"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "エラー", "URLを入力してください")
            return

        if not self.download_manager:
            QMessageBox.warning(self, "エラー", "ダウンロードマネージャーが初期化されていません")
            return

        quality_map = {
            "最高品質": None,  # Will use default: bestvideo+bestaudio/best
            "1080p": "bestvideo[height<=1080]+bestaudio/bestvideo[height<=1080]/best[height<=1080]",
            "720p": "bestvideo[height<=720]+bestaudio/bestvideo[height<=720]/best[height<=720]",
            "480p": "bestvideo[height<=480]+bestaudio/bestvideo[height<=480]/best[height<=480]",
            "360p": "bestvideo[height<=360]+bestaudio/bestvideo[height<=360]/best[height<=360]",
            "音声のみ": "bestaudio/best"
        }

        quality = self.quality_combo.currentText()
        format_id = quality_map.get(quality)
        priority = self.priority_spin.value()

        try:
            # Get the event loop from the parent window's service thread
            from gui.main_window import MainWindow
            parent = self.window()
            if isinstance(parent, MainWindow) and parent.service_thread and parent.service_thread.loop:
                # Add download (async) in the correct event loop
                future = asyncio.run_coroutine_threadsafe(
                    self.download_manager.add_download(
                        url=url,
                        format_id=format_id,
                        priority=priority
                    ),
                    parent.service_thread.loop
                )

                # Wait for result (with timeout)
                try:
                    task = future.result(timeout=5)
                    self.url_input.clear()
                    QMessageBox.information(self, "成功", "ダウンロードを追加しました")
                    logger.info(f"Added download: {url}")
                except Exception as e:
                    raise e
            else:
                raise RuntimeError("イベントループが初期化されていません")

        except ValueError as e:
            QMessageBox.warning(self, "警告", str(e))
            logger.warning(f"Duplicate download: {url}")
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"ダウンロードの追加に失敗しました:\n{str(e)}")
            logger.error(f"Failed to add download: {e}", exc_info=True)

    def _get_video_info(self):
        """Get video information"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "エラー", "URLを入力してください")
            return

        if not self.download_manager:
            QMessageBox.warning(self, "エラー", "ダウンロードマネージャーが初期化されていません")
            return

        try:
            # Get the event loop from the parent window's service thread
            from gui.main_window import MainWindow
            parent = self.window()
            if isinstance(parent, MainWindow) and parent.service_thread and parent.service_thread.loop:
                # Get info (async) in the correct event loop
                future = asyncio.run_coroutine_threadsafe(
                    self.download_manager.get_video_info(url),
                    parent.service_thread.loop
                )
                info = future.result(timeout=30)

                if info:
                    title = info.get('title', 'N/A')
                    channel = info.get('uploader', 'N/A')
                    duration = info.get('duration', 0)
                    views = info.get('view_count', 0)

                    msg = f"""タイトル: {title}
チャンネル: {channel}
再生時間: {duration // 60}分{duration % 60}秒
再生回数: {views:,}"""

                    QMessageBox.information(self, "動画情報", msg)
                else:
                    QMessageBox.warning(self, "エラー", "動画情報の取得に失敗しました")
            else:
                raise RuntimeError("イベントループが初期化されていません")

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"動画情報の取得に失敗しました:\n{str(e)}")
            logger.error(f"Failed to get video info: {e}", exc_info=True)

    def _add_channel_download(self):
        """Add channel download to queue"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "エラー", "チャンネルURLを入力してください")
            return

        if not self.download_manager:
            QMessageBox.warning(self, "エラー", "ダウンロードマネージャーが初期化されていません")
            return

        # Confirm with user
        reply = QMessageBox.question(
            self,
            "確認",
            "チャンネルの全動画をダウンロードキューに追加しますか？\n"
            "※既にダウンロード済みの動画はスキップされます",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        quality_map = {
            "最高品質": None,
            "1080p": "bestvideo[height<=1080]+bestaudio/bestvideo[height<=1080]/best[height<=1080]",
            "720p": "bestvideo[height<=720]+bestaudio/bestvideo[height<=720]/best[height<=720]",
            "480p": "bestvideo[height<=480]+bestaudio/bestvideo[height<=480]/best[height<=480]",
            "360p": "bestvideo[height<=360]+bestaudio/bestvideo[height<=360]/best[height<=360]",
            "音声のみ": "bestaudio/best"
        }

        quality = self.quality_combo.currentText()
        format_id = quality_map.get(quality)
        priority = self.priority_spin.value()

        try:
            # Get the event loop from the parent window's service thread
            from gui.main_window import MainWindow
            parent = self.window()
            if isinstance(parent, MainWindow) and parent.service_thread and parent.service_thread.loop:
                # Show progress dialog
                from PySide6.QtWidgets import QProgressDialog
                progress = QProgressDialog("チャンネル動画を取得中...", "キャンセル", 0, 0, self)
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.setAutoClose(False)
                progress.show()

                # Add channel download (async) in the correct event loop
                future = asyncio.run_coroutine_threadsafe(
                    self.download_manager.add_channel_download(
                        channel_url=url,
                        format_id=format_id,
                        priority=priority
                    ),
                    parent.service_thread.loop
                )

                # Wait for result (with timeout)
                try:
                    tasks = future.result(timeout=60)
                    progress.close()

                    if tasks:
                        self.url_input.clear()
                        QMessageBox.information(
                            self,
                            "成功",
                            f"チャンネルから {len(tasks)} 本の動画をキューに追加しました"
                        )
                        logger.info(f"Added {len(tasks)} videos from channel: {url}")
                    else:
                        QMessageBox.information(
                            self,
                            "情報",
                            "新しくダウンロードする動画がありませんでした\n（全て既にダウンロード済み）"
                        )
                except Exception as e:
                    progress.close()
                    raise e
            else:
                raise RuntimeError("イベントループが初期化されていません")

        except ValueError as e:
            QMessageBox.warning(self, "警告", str(e))
            logger.warning(f"Channel download error: {url} - {e}")
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"チャンネルダウンロードの追加に失敗しました:\n{str(e)}")
            logger.error(f"Failed to add channel download: {e}", exc_info=True)

    def _add_playlist_download(self):
        """Add playlist download to queue"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "エラー", "プレイリストURLを入力してください")
            return

        if not self.download_manager:
            QMessageBox.warning(self, "エラー", "ダウンロードマネージャーが初期化されていません")
            return

        # Confirm with user
        reply = QMessageBox.question(
            self,
            "確認",
            "プレイリストの全動画をダウンロードキューに追加しますか？\n"
            "※既にダウンロード済みの動画はスキップされます",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        quality_map = {
            "最高品質": None,
            "1080p": "bestvideo[height<=1080]+bestaudio/bestvideo[height<=1080]/best[height<=1080]",
            "720p": "bestvideo[height<=720]+bestaudio/bestvideo[height<=720]/best[height<=720]",
            "480p": "bestvideo[height<=480]+bestaudio/bestvideo[height<=480]/best[height<=480]",
            "360p": "bestvideo[height<=360]+bestaudio/bestvideo[height<=360]/best[height<=360]",
            "音声のみ": "bestaudio/best"
        }

        quality = self.quality_combo.currentText()
        format_id = quality_map.get(quality)
        priority = self.priority_spin.value()

        try:
            # Get the event loop from the parent window's service thread
            from gui.main_window import MainWindow
            parent = self.window()
            if isinstance(parent, MainWindow) and parent.service_thread and parent.service_thread.loop:
                # Show progress dialog
                from PySide6.QtWidgets import QProgressDialog
                progress = QProgressDialog("プレイリスト動画を取得中...", "キャンセル", 0, 0, self)
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.setAutoClose(False)
                progress.show()

                # Add playlist download (async) in the correct event loop
                future = asyncio.run_coroutine_threadsafe(
                    self.download_manager.add_playlist_download(
                        playlist_url=url,
                        format_id=format_id,
                        priority=priority
                    ),
                    parent.service_thread.loop
                )

                # Wait for result (with timeout)
                try:
                    tasks = future.result(timeout=60)
                    progress.close()

                    if tasks:
                        self.url_input.clear()
                        QMessageBox.information(
                            self,
                            "成功",
                            f"プレイリストから {len(tasks)} 本の動画をキューに追加しました"
                        )
                        logger.info(f"Added {len(tasks)} videos from playlist: {url}")
                    else:
                        QMessageBox.information(
                            self,
                            "情報",
                            "新しくダウンロードする動画がありませんでした\n（全て既にダウンロード済み）"
                        )
                except Exception as e:
                    progress.close()
                    raise e
            else:
                raise RuntimeError("イベントループが初期化されていません")

        except ValueError as e:
            QMessageBox.warning(self, "警告", str(e))
            logger.warning(f"Playlist download error: {url} - {e}")
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"プレイリストダウンロードの追加に失敗しました:\n{str(e)}")
            logger.error(f"Failed to add playlist download: {e}", exc_info=True)

    def _update_downloads(self):
        """Update downloads table"""
        if not self.download_manager:
            return

        try:
            downloads = self.download_manager.get_active_downloads()

            # Update table row count
            self.downloads_table.setRowCount(len(downloads))

            for row, download in enumerate(downloads):
                # Title
                title = download.get('metadata', {}).get('title', download.get('url', 'Unknown'))
                self.downloads_table.setItem(row, 0, QTableWidgetItem(title))

                # Progress bar
                progress = download.get('progress', 0)
                progress_widget = QProgressBar()
                progress_widget.setValue(int(progress))
                self.downloads_table.setCellWidget(row, 1, progress_widget)

                # Speed
                speed = download.get('speed', 0)
                speed_text = f"{speed / 1024 / 1024:.2f} MB/s" if speed else "N/A"
                self.downloads_table.setItem(row, 2, QTableWidgetItem(speed_text))

                # ETA
                eta = download.get('eta')
                eta_text = f"{eta}s" if eta else "N/A"
                self.downloads_table.setItem(row, 3, QTableWidgetItem(eta_text))

                # Status
                status = download.get('status', 'unknown')
                self.downloads_table.setItem(row, 4, QTableWidgetItem(status))

                # Action buttons
                action_widget = QWidget()
                action_layout = QHBoxLayout()
                action_layout.setContentsMargins(0, 0, 0, 0)

                pause_btn = QPushButton("一時停止")
                cancel_btn = QPushButton("キャンセル")

                task_id = download.get('id')
                pause_btn.clicked.connect(lambda checked, tid=task_id: self._pause_download(tid))
                cancel_btn.clicked.connect(lambda checked, tid=task_id: self._cancel_download(tid))

                action_layout.addWidget(pause_btn)
                action_layout.addWidget(cancel_btn)
                action_widget.setLayout(action_layout)

                self.downloads_table.setCellWidget(row, 5, action_widget)

        except Exception as e:
            logger.error(f"Error updating downloads: {e}")

    def _pause_download(self, task_id):
        """Pause download"""
        if not self.download_manager:
            return

        try:
            from gui.main_window import MainWindow
            parent = self.window()
            if isinstance(parent, MainWindow) and parent.service_thread and parent.service_thread.loop:
                future = asyncio.run_coroutine_threadsafe(
                    self.download_manager.pause_download(task_id),
                    parent.service_thread.loop
                )
                future.result(timeout=2)
                logger.info(f"Paused download: {task_id}")
        except Exception as e:
            logger.error(f"Failed to pause download: {e}", exc_info=True)

    def _cancel_download(self, task_id):
        """Cancel download"""
        if not self.download_manager:
            return

        reply = QMessageBox.question(
            self,
            "確認",
            "このダウンロードをキャンセルしますか?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                from gui.main_window import MainWindow
                parent = self.window()
                if isinstance(parent, MainWindow) and parent.service_thread and parent.service_thread.loop:
                    future = asyncio.run_coroutine_threadsafe(
                        self.download_manager.cancel_download(task_id),
                        parent.service_thread.loop
                    )
                    future.result(timeout=2)
                    logger.info(f"Cancelled download: {task_id}")
            except Exception as e:
                logger.error(f"Failed to cancel download: {e}", exc_info=True)
