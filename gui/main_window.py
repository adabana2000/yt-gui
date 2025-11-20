"""Main window for YouTube Downloader GUI"""
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QSystemTrayIcon, QMenu, QApplication
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QIcon, QAction
import asyncio
import sys

from gui.download_tab import DownloadTab
from gui.schedule_tab import ScheduleTab
from gui.history_tab import HistoryTab
from gui.settings_tab import SettingsTab
from core.service_manager import service_manager, ServiceConfig
from database.db_manager import DatabaseManager
from modules.download_manager import DownloadManager
from modules.schedule_manager import ScheduleManager
from modules.auth_manager import AuthManager
from modules.encode_manager import EncodeManager
from modules.metadata_manager import MetadataManager
from config.settings import settings
from utils.logger import logger


class ServiceThread(QThread):
    """Thread for running async services"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.loop = None

    def run(self):
        """Run event loop"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def stop(self):
        """Stop event loop"""
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"{settings.APP_NAME} v{settings.APP_VERSION}")
        self.setGeometry(100, 100, 1200, 800)

        # Initialize managers
        self.db_manager = None
        self.download_manager = None
        self.schedule_manager = None
        self.auth_manager = None
        self.encode_manager = None
        self.metadata_manager = None

        # Service thread
        self.service_thread = None

        # UI components
        self.tabs = None
        self.download_tab = None
        self.schedule_tab = None
        self.history_tab = None
        self.settings_tab = None
        self.tray_icon = None

        self._init_ui()
        self._check_system_requirements()
        self._init_services()
        self._init_system_tray()

    def _init_ui(self):
        """Initialize UI components"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Create tabs (managers will be set later)
        self.download_tab = DownloadTab()
        self.schedule_tab = ScheduleTab()
        self.history_tab = HistoryTab()
        self.settings_tab = SettingsTab()

        # Add tabs
        self.tabs.addTab(self.download_tab, "ダウンロード")
        self.tabs.addTab(self.schedule_tab, "スケジュール")
        self.tabs.addTab(self.history_tab, "履歴")
        self.tabs.addTab(self.settings_tab, "設定")

        # Menu bar
        self._create_menu_bar()

        logger.info("UI initialized")

    def _create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("ファイル(&F)")

        exit_action = QAction("終了(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("表示(&V)")

        # Help menu
        help_menu = menubar.addMenu("ヘルプ(&H)")

        check_system_action = QAction("システムチェック", self)
        check_system_action.triggered.connect(self._show_system_check)
        help_menu.addAction(check_system_action)

        help_menu.addSeparator()

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _check_system_requirements(self):
        """Check system requirements on startup"""
        from utils.system_check import check_all_requirements
        from PySide6.QtWidgets import QMessageBox

        checks = check_all_requirements()

        missing = []
        for name, (installed, info) in checks.items():
            if not installed:
                missing.append(f"• {name}: {info}")

        if missing:
            msg = "以下のシステム要件が満たされていません:\n\n"
            msg += "\n".join(missing)
            msg += "\n\n一部の機能が正常に動作しない可能性があります。"

            QMessageBox.warning(self, "システム要件の警告", msg)

    def _show_system_check(self):
        """Show system check dialog"""
        from utils.system_check import check_all_requirements
        from PySide6.QtWidgets import QMessageBox

        checks = check_all_requirements()

        msg = "システム要件チェック:\n\n"
        for name, (installed, info) in checks.items():
            status = "✓" if installed else "✗"
            msg += f"{status} {name}\n  {info}\n\n"

        QMessageBox.information(self, "システムチェック", msg)

    def _init_services(self):
        """Initialize backend services"""
        logger.info("Initializing services...")

        # Start service thread
        self.service_thread = ServiceThread()
        self.service_thread.start()

        # Initialize managers
        self.db_manager = DatabaseManager()

        config = ServiceConfig(
            max_workers=settings.MAX_WORKERS,
            retry_count=settings.RETRY_COUNT,
            timeout=settings.TIMEOUT
        )

        self.auth_manager = AuthManager(config)
        self.download_manager = DownloadManager(config, self.db_manager, self.auth_manager)
        self.schedule_manager = ScheduleManager(config, self.db_manager, self.download_manager)
        self.encode_manager = EncodeManager(config)
        self.metadata_manager = MetadataManager(config, self.db_manager)

        # Set managers in tabs
        self.download_tab.set_managers(self.download_manager, self.db_manager)
        self.schedule_tab.set_managers(self.schedule_manager, self.db_manager)
        self.history_tab.set_managers(self.db_manager)
        self.settings_tab.set_managers(
            self.auth_manager,
            self.encode_manager,
            self.db_manager
        )

        # Register services
        service_manager.register_service("download", self.download_manager)
        service_manager.register_service("schedule", self.schedule_manager)
        service_manager.register_service("auth", self.auth_manager)
        service_manager.register_service("encode", self.encode_manager)
        service_manager.register_service("metadata", self.metadata_manager)

        # Start services
        asyncio.run_coroutine_threadsafe(
            service_manager.start_all(),
            self.service_thread.loop
        )

        logger.info("Services initialized")

    def _init_system_tray(self):
        """Initialize system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)
        # self.tray_icon.setIcon(QIcon("icon.png"))  # Set icon if available

        # Tray menu
        tray_menu = QMenu()

        show_action = QAction("表示", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        quit_action = QAction("終了", self)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # Double click to show
        self.tray_icon.activated.connect(self._tray_activated)

    def _tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.activateWindow()

    def _show_about(self):
        """Show about dialog"""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(
            self,
            "About",
            f"{settings.APP_NAME} v{settings.APP_VERSION}\n\n"
            "YouTube Downloader with yt-dlp"
        )

    def closeEvent(self, event):
        """Handle window close event"""
        # Stop services
        if self.service_thread:
            asyncio.run_coroutine_threadsafe(
                service_manager.stop_all(),
                self.service_thread.loop
            )
            self.service_thread.stop()
            self.service_thread.wait()

        logger.info("Application closed")
        event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName(settings.APP_NAME)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
