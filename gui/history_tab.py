"""History tab for YouTube Downloader GUI"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QGroupBox
)
from PySide6.QtCore import Qt, QTimer

from utils.logger import logger


class HistoryTab(QWidget):
    """History tab widget"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.db_manager = None
        self.current_page = 0
        self.page_size = 50

        self._init_ui()

    def set_managers(self, db_manager):
        """Set managers"""
        self.db_manager = db_manager
        self._load_history()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Search and controls
        controls_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("タイトルまたはチャンネルで検索...")
        self.search_input.returnPressed.connect(self._search)
        controls_layout.addWidget(QLabel("検索:"))
        controls_layout.addWidget(self.search_input)

        self.search_button = QPushButton("検索")
        self.search_button.clicked.connect(self._search)
        controls_layout.addWidget(self.search_button)

        self.refresh_button = QPushButton("更新")
        self.refresh_button.clicked.connect(self._load_history)
        controls_layout.addWidget(self.refresh_button)

        layout.addLayout(controls_layout)

        # History table
        history_group = QGroupBox("ダウンロード履歴")
        history_layout = QVBoxLayout()
        history_group.setLayout(history_layout)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "タイトル", "チャンネル", "ダウンロード日時", "ファイルパス", "サイズ"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        history_layout.addWidget(self.history_table)

        # Pagination
        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("前へ")
        self.prev_button.clicked.connect(self._prev_page)
        self.next_button = QPushButton("次へ")
        self.next_button.clicked.connect(self._next_page)
        self.page_label = QLabel("Page 1")

        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_button)
        pagination_layout.addStretch()
        history_layout.addLayout(pagination_layout)

        layout.addWidget(history_group)

        # Stats
        stats_group = QGroupBox("統計")
        stats_layout = QVBoxLayout()
        stats_group.setLayout(stats_layout)

        self.stats_label = QLabel("統計を読み込み中...")
        stats_layout.addWidget(self.stats_label)

        layout.addWidget(stats_group)

    def _load_history(self):
        """Load download history"""
        if not self.db_manager:
            return

        try:
            skip = self.current_page * self.page_size
            history = self.db_manager.get_download_history(
                skip=skip,
                limit=self.page_size
            )

            self.history_table.setRowCount(len(history))

            for row, item in enumerate(history):
                # Title
                self.history_table.setItem(row, 0, QTableWidgetItem(item.title or 'N/A'))

                # Channel
                self.history_table.setItem(row, 1, QTableWidgetItem(item.channel_name or 'N/A'))

                # Date
                date_str = item.download_date.strftime('%Y-%m-%d %H:%M:%S') if item.download_date else 'N/A'
                self.history_table.setItem(row, 2, QTableWidgetItem(date_str))

                # File path
                self.history_table.setItem(row, 3, QTableWidgetItem(item.file_path or 'N/A'))

                # Size
                size = item.file_size or 0
                size_str = f"{size / 1024 / 1024:.2f} MB" if size else 'N/A'
                self.history_table.setItem(row, 4, QTableWidgetItem(size_str))

            # Update page label
            self.page_label.setText(f"Page {self.current_page + 1}")

            # Update buttons
            self.prev_button.setEnabled(self.current_page > 0)
            self.next_button.setEnabled(len(history) == self.page_size)

            # Load stats
            self._load_stats()

        except Exception as e:
            logger.error(f"Error loading history: {e}")

    def _search(self):
        """Search history"""
        if not self.db_manager:
            return

        search_query = self.search_input.text().strip()

        try:
            history = self.db_manager.get_download_history(
                skip=0,
                limit=self.page_size,
                search_query=search_query if search_query else None
            )

            self.history_table.setRowCount(len(history))

            for row, item in enumerate(history):
                self.history_table.setItem(row, 0, QTableWidgetItem(item.title or 'N/A'))
                self.history_table.setItem(row, 1, QTableWidgetItem(item.channel_name or 'N/A'))

                date_str = item.download_date.strftime('%Y-%m-%d %H:%M:%S') if item.download_date else 'N/A'
                self.history_table.setItem(row, 2, QTableWidgetItem(date_str))

                self.history_table.setItem(row, 3, QTableWidgetItem(item.file_path or 'N/A'))

                size = item.file_size or 0
                size_str = f"{size / 1024 / 1024:.2f} MB" if size else 'N/A'
                self.history_table.setItem(row, 4, QTableWidgetItem(size_str))

        except Exception as e:
            logger.error(f"Error searching history: {e}")

    def _load_stats(self):
        """Load statistics"""
        if not self.db_manager:
            return

        try:
            stats = self.db_manager.get_download_stats()

            total = stats.get('total_downloads', 0)
            total_size = stats.get('total_size_bytes', 0)
            week_count = stats.get('downloads_last_week', 0)

            size_gb = total_size / 1024 / 1024 / 1024

            stats_text = f"""
            総ダウンロード数: {total}
            総ダウンロードサイズ: {size_gb:.2f} GB
            過去7日間: {week_count} 件
            """

            self.stats_label.setText(stats_text)

        except Exception as e:
            logger.error(f"Error loading stats: {e}")
            self.stats_label.setText("統計の読み込みに失敗しました")

    def _prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self._load_history()

    def _next_page(self):
        """Go to next page"""
        self.current_page += 1
        self._load_history()
