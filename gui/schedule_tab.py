"""Schedule tab for YouTube Downloader GUI"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QComboBox, QLabel, QGroupBox,
    QMessageBox, QDialog, QFormLayout, QDialogButtonBox
)
from PySide6.QtCore import Qt, QTimer

from utils.logger import logger


class AddScheduleDialog(QDialog):
    """Dialog for adding scheduled task"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("スケジュールタスク追加")
        self._init_ui()

    def _init_ui(self):
        """Initialize UI"""
        layout = QFormLayout()

        # Name
        self.name_input = QLineEdit()
        layout.addRow("名前:", self.name_input)

        # Task type
        self.task_type_combo = QComboBox()
        self.task_type_combo.addItems([
            "チャンネル更新チェック",
            "プレイリストダウンロード"
        ])
        layout.addRow("タスク種類:", self.task_type_combo)

        # URL
        self.url_input = QLineEdit()
        layout.addRow("URL:", self.url_input)

        # Schedule
        self.schedule_input = QLineEdit()
        self.schedule_input.setPlaceholderText("例: 0 */6 * * * (6時間ごと)")
        layout.addRow("スケジュール (Cron):", self.schedule_input)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.setLayout(layout)

    def get_data(self):
        """Get form data"""
        task_type_map = {
            "チャンネル更新チェック": "channel_download",
            "プレイリストダウンロード": "playlist_download"
        }

        return {
            'name': self.name_input.text(),
            'task_type': task_type_map[self.task_type_combo.currentText()],
            'cron_expression': self.schedule_input.text(),
            'parameters': {
                'channel_url' if 'チャンネル' in self.task_type_combo.currentText() else 'playlist_url': self.url_input.text()
            }
        }


class ScheduleTab(QWidget):
    """Schedule tab widget"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.schedule_manager = None
        self.db_manager = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_schedules)

        self._init_ui()

    def set_managers(self, schedule_manager, db_manager):
        """Set managers and start updates"""
        self.schedule_manager = schedule_manager
        self.db_manager = db_manager
        self.timer.start(5000)  # Update every 5 seconds
        self._update_schedules()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Controls
        controls_layout = QHBoxLayout()
        self.add_button = QPushButton("スケジュール追加")
        self.add_button.clicked.connect(self._add_schedule)
        self.refresh_button = QPushButton("更新")
        self.refresh_button.clicked.connect(self._update_schedules)
        controls_layout.addWidget(self.add_button)
        controls_layout.addWidget(self.refresh_button)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Schedules table
        schedules_group = QGroupBox("スケジュール一覧")
        schedules_layout = QVBoxLayout()
        schedules_group.setLayout(schedules_layout)

        self.schedules_table = QTableWidget()
        self.schedules_table.setColumnCount(7)
        self.schedules_table.setHorizontalHeaderLabels([
            "名前", "種類", "スケジュール", "有効", "最終実行", "次回実行", "操作"
        ])
        self.schedules_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        schedules_layout.addWidget(self.schedules_table)

        layout.addWidget(schedules_group)

    def _add_schedule(self):
        """Show add schedule dialog"""
        dialog = AddScheduleDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()

            if not data['name'] or not data['cron_expression']:
                QMessageBox.warning(self, "エラー", "名前とスケジュールは必須です")
                return

            try:
                import asyncio
                from gui.main_window import MainWindow
                parent = self.window()
                if isinstance(parent, MainWindow) and parent.service_thread and parent.service_thread.loop:
                    future = asyncio.run_coroutine_threadsafe(
                        self.schedule_manager.add_scheduled_task(
                            name=data['name'],
                            cron_expression=data['cron_expression'],
                            task_type=data['task_type'],
                            parameters=data['parameters']
                        ),
                        parent.service_thread.loop
                    )
                    future.result(timeout=5)

                    QMessageBox.information(self, "成功", "スケジュールを追加しました")
                    self._update_schedules()
                else:
                    raise RuntimeError("イベントループが初期化されていません")

            except Exception as e:
                QMessageBox.critical(self, "エラー", f"スケジュールの追加に失敗しました:\n{str(e)}")
                logger.error(f"Failed to add schedule: {e}", exc_info=True)

    def _update_schedules(self):
        """Update schedules table"""
        if not self.schedule_manager:
            return

        try:
            tasks = self.schedule_manager.get_tasks()

            self.schedules_table.setRowCount(len(tasks))

            task_type_map = {
                'channel_download': 'チャンネル',
                'playlist_download': 'プレイリスト'
            }

            for row, task in enumerate(tasks):
                # Name
                self.schedules_table.setItem(row, 0, QTableWidgetItem(task.get('name', '')))

                # Type
                task_type = task_type_map.get(task.get('task_type', ''), 'Unknown')
                self.schedules_table.setItem(row, 1, QTableWidgetItem(task_type))

                # Cron expression
                self.schedules_table.setItem(row, 2, QTableWidgetItem(task.get('cron_expression', '')))

                # Enabled
                enabled = "有効" if task.get('enabled') else "無効"
                self.schedules_table.setItem(row, 3, QTableWidgetItem(enabled))

                # Last run
                last_run = task.get('last_run', 'N/A')
                self.schedules_table.setItem(row, 4, QTableWidgetItem(str(last_run)))

                # Next run
                next_run = task.get('next_run', 'N/A')
                self.schedules_table.setItem(row, 5, QTableWidgetItem(str(next_run)))

                # Actions
                action_widget = QWidget()
                action_layout = QHBoxLayout()
                action_layout.setContentsMargins(0, 0, 0, 0)

                delete_btn = QPushButton("削除")
                task_id = task.get('id')
                delete_btn.clicked.connect(lambda checked, tid=task_id: self._delete_schedule(tid))

                action_layout.addWidget(delete_btn)
                action_widget.setLayout(action_layout)

                self.schedules_table.setCellWidget(row, 6, action_widget)

        except Exception as e:
            logger.error(f"Error updating schedules: {e}")

    def _delete_schedule(self, task_id):
        """Delete schedule"""
        reply = QMessageBox.question(
            self,
            "確認",
            "このスケジュールを削除しますか?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                import asyncio
                from gui.main_window import MainWindow
                parent = self.window()
                if isinstance(parent, MainWindow) and parent.service_thread and parent.service_thread.loop:
                    future = asyncio.run_coroutine_threadsafe(
                        self.schedule_manager.remove_task(task_id),
                        parent.service_thread.loop
                    )
                    future.result(timeout=5)

                    QMessageBox.information(self, "成功", "スケジュールを削除しました")
                    self._update_schedules()
                else:
                    raise RuntimeError("イベントループが初期化されていません")

            except Exception as e:
                QMessageBox.critical(self, "エラー", f"スケジュールの削除に失敗しました:\n{str(e)}")
                logger.error(f"Failed to delete schedule: {e}", exc_info=True)
