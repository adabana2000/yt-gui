"""Settings tab for YouTube Downloader GUI"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QPushButton, QLabel, QGroupBox, QCheckBox,
    QSpinBox, QFileDialog, QComboBox, QMessageBox,
    QTextEdit, QToolButton, QTabWidget, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from config.settings import settings
from utils.logger import logger


class SettingsTab(QWidget):
    """Settings tab widget with comprehensive configuration options"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.auth_manager = None
        self.encode_manager = None
        self.db_manager = None
        self.notification_manager = None
        self.updater_manager = None

        self._init_ui()

    def set_managers(self, auth_manager=None, encode_manager=None, db_manager=None,
                     notification_manager=None, updater_manager=None):
        """Set managers"""
        self.auth_manager = auth_manager
        self.encode_manager = encode_manager
        self.db_manager = db_manager
        self.notification_manager = notification_manager
        self.updater_manager = updater_manager
        self._load_settings()

    def _init_ui(self):
        """Initialize UI"""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Create tab widget for organized settings
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Add tabs
        self.tabs.addTab(self._create_download_tab(), "ダウンロード")
        self.tabs.addTab(self._create_quality_tab(), "画質/フォーマット")
        self.tabs.addTab(self._create_subtitle_tab(), "字幕")
        self.tabs.addTab(self._create_playlist_tab(), "プレイリスト")
        self.tabs.addTab(self._create_notification_tab(), "通知")
        self.tabs.addTab(self._create_advanced_tab(), "詳細設定")
        self.tabs.addTab(self._create_auth_tab(), "認証")

        # Save button at bottom
        save_layout = QHBoxLayout()
        save_button = QPushButton("設定を保存")
        save_button.setMinimumHeight(40)
        save_button.clicked.connect(self._save_settings)
        save_layout.addWidget(save_button)
        main_layout.addLayout(save_layout)

    def _create_download_tab(self):
        """Create download settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Download directory
        dir_group = QGroupBox("保存先設定")
        dir_layout = QVBoxLayout()
        dir_group.setLayout(dir_layout)

        dir_path_layout = QHBoxLayout()
        dir_path_layout.addWidget(QLabel("保存先:"))
        self.download_dir_input = QLineEdit()
        self.download_dir_input.setText(str(settings.DOWNLOAD_DIR))
        dir_path_layout.addWidget(self.download_dir_input)

        browse_button = QPushButton("参照")
        browse_button.clicked.connect(self._browse_directory)
        dir_path_layout.addWidget(browse_button)
        dir_layout.addLayout(dir_path_layout)

        # Output template
        template_layout = QVBoxLayout()
        template_layout.addWidget(QLabel("出力テンプレート:"))

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

        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("カスタムテンプレート:"))
        self.custom_template_input = QLineEdit()
        self.custom_template_input.setText(settings.CUSTOM_OUTPUT_TEMPLATE)
        self.custom_template_input.setPlaceholderText("例: %(uploader)s/%(title)s.%(ext)s")
        custom_layout.addWidget(self.custom_template_input)

        help_button = QPushButton("?")
        help_button.setMaximumWidth(30)
        help_button.clicked.connect(self._show_template_help)
        custom_layout.addWidget(help_button)
        template_layout.addLayout(custom_layout)

        self.template_preview_label = QLabel("プレビュー: チャンネル名/動画タイトル.mp4")
        self.template_preview_label.setWordWrap(True)
        self.template_preview_label.setStyleSheet("color: gray; font-style: italic;")
        template_layout.addWidget(self.template_preview_label)

        dir_layout.addLayout(template_layout)
        layout.addWidget(dir_group)

        # Download options
        options_group = QGroupBox("ダウンロードオプション")
        options_layout = QVBoxLayout()
        options_group.setLayout(options_layout)

        # Concurrent downloads
        concurrent_layout = QHBoxLayout()
        concurrent_layout.addWidget(QLabel("同時ダウンロード数:"))
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setMinimum(1)
        self.concurrent_spin.setMaximum(10)
        self.concurrent_spin.setValue(settings.MAX_CONCURRENT_DOWNLOADS)
        concurrent_layout.addWidget(self.concurrent_spin)
        concurrent_layout.addStretch()
        options_layout.addLayout(concurrent_layout)

        # Duplicate check
        self.skip_duplicates_checkbox = QCheckBox("重複をスキップする")
        self.skip_duplicates_checkbox.setChecked(settings.SKIP_DUPLICATES)
        options_layout.addWidget(self.skip_duplicates_checkbox)

        self.check_by_video_id_checkbox = QCheckBox("動画IDでチェック")
        self.check_by_video_id_checkbox.setChecked(settings.CHECK_BY_VIDEO_ID)
        options_layout.addWidget(self.check_by_video_id_checkbox)

        self.check_by_filename_checkbox = QCheckBox("ファイル名でチェック")
        self.check_by_filename_checkbox.setChecked(settings.CHECK_BY_FILENAME)
        options_layout.addWidget(self.check_by_filename_checkbox)

        layout.addWidget(options_group)

        # Thumbnail and metadata
        metadata_group = QGroupBox("サムネイル・メタデータ")
        metadata_layout = QVBoxLayout()
        metadata_group.setLayout(metadata_layout)

        self.download_thumbnail_checkbox = QCheckBox("サムネイルをダウンロード")
        self.download_thumbnail_checkbox.setChecked(settings.DOWNLOAD_THUMBNAIL)
        metadata_layout.addWidget(self.download_thumbnail_checkbox)

        self.embed_thumbnail_checkbox = QCheckBox("サムネイルを動画に埋め込む")
        self.embed_thumbnail_checkbox.setChecked(settings.EMBED_THUMBNAIL)
        metadata_layout.addWidget(self.embed_thumbnail_checkbox)

        self.write_info_json_checkbox = QCheckBox("info.jsonを保存")
        self.write_info_json_checkbox.setChecked(settings.WRITE_INFO_JSON)
        metadata_layout.addWidget(self.write_info_json_checkbox)

        self.write_description_checkbox = QCheckBox("説明文を保存")
        self.write_description_checkbox.setChecked(settings.WRITE_DESCRIPTION)
        metadata_layout.addWidget(self.write_description_checkbox)

        layout.addWidget(metadata_group)
        layout.addStretch()

        return widget

    def _create_quality_tab(self):
        """Create quality/format settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Video quality
        video_group = QGroupBox("動画画質")
        video_layout = QVBoxLayout()
        video_group.setLayout(video_layout)

        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("画質プリセット:"))
        self.quality_combo = QComboBox()
        self.quality_combo.addItems([
            "最高画質 (best)",
            "4K 2160p",
            "2K 1440p",
            "Full HD 1080p",
            "HD 720p",
            "SD 480p",
            "低画質 360p",
            "最低画質 (worst)",
            "音声のみ (audio only)"
        ])

        # Map current quality to combo index
        quality_map = {"best": 0, "2160p": 1, "1440p": 2, "1080p": 3,
                      "720p": 4, "480p": 5, "360p": 6, "worst": 7, "audio_only": 8}
        current_index = quality_map.get(settings.VIDEO_QUALITY, 0)
        self.quality_combo.setCurrentIndex(current_index)

        quality_layout.addWidget(self.quality_combo)
        quality_layout.addStretch()
        video_layout.addLayout(quality_layout)

        # Video format
        video_format_layout = QHBoxLayout()
        video_format_layout.addWidget(QLabel("動画フォーマット:"))
        self.video_format_combo = QComboBox()
        self.video_format_combo.addItems(["MP4", "WebM", "MKV", "Any"])
        self.video_format_combo.setCurrentText(settings.VIDEO_FORMAT.upper())
        video_format_layout.addWidget(self.video_format_combo)
        video_format_layout.addStretch()
        video_layout.addLayout(video_format_layout)

        self.download_video_checkbox = QCheckBox("動画をダウンロード")
        self.download_video_checkbox.setChecked(settings.DOWNLOAD_VIDEO)
        video_layout.addWidget(self.download_video_checkbox)

        layout.addWidget(video_group)

        # Audio settings
        audio_group = QGroupBox("音声設定")
        audio_layout = QVBoxLayout()
        audio_group.setLayout(audio_layout)

        audio_quality_layout = QHBoxLayout()
        audio_quality_layout.addWidget(QLabel("音声品質:"))
        self.audio_quality_combo = QComboBox()
        self.audio_quality_combo.addItems(["最高 (best)", "320k", "256k", "192k", "128k", "最低 (worst)"])
        audio_quality_map = {"best": 0, "320k": 1, "256k": 2, "192k": 3, "128k": 4, "worst": 5}
        audio_index = audio_quality_map.get(settings.AUDIO_QUALITY, 0)
        self.audio_quality_combo.setCurrentIndex(audio_index)
        audio_quality_layout.addWidget(self.audio_quality_combo)
        audio_quality_layout.addStretch()
        audio_layout.addLayout(audio_quality_layout)

        audio_format_layout = QHBoxLayout()
        audio_format_layout.addWidget(QLabel("音声フォーマット:"))
        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(["M4A", "MP3", "Opus", "WAV", "Best"])
        self.audio_format_combo.setCurrentText(settings.AUDIO_FORMAT.upper())
        audio_format_layout.addWidget(self.audio_format_combo)
        audio_format_layout.addStretch()
        audio_layout.addLayout(audio_format_layout)

        self.download_audio_checkbox = QCheckBox("音声をダウンロード")
        self.download_audio_checkbox.setChecked(settings.DOWNLOAD_AUDIO)
        audio_layout.addWidget(self.download_audio_checkbox)

        layout.addWidget(audio_group)

        # GPU encoding
        gpu_group = QGroupBox("GPU エンコーディング")
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
        layout.addStretch()

        return widget

    def _create_subtitle_tab(self):
        """Create subtitle settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Subtitle settings
        subtitle_group = QGroupBox("字幕設定")
        subtitle_layout = QVBoxLayout()
        subtitle_group.setLayout(subtitle_layout)

        self.download_subtitles_checkbox = QCheckBox("字幕をダウンロード")
        self.download_subtitles_checkbox.setChecked(settings.DOWNLOAD_SUBTITLES)
        subtitle_layout.addWidget(self.download_subtitles_checkbox)

        self.download_auto_subtitles_checkbox = QCheckBox("自動生成字幕もダウンロード")
        self.download_auto_subtitles_checkbox.setChecked(settings.DOWNLOAD_AUTO_SUBTITLES)
        subtitle_layout.addWidget(self.download_auto_subtitles_checkbox)

        # Subtitle languages
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("字幕言語 (優先順):"))
        self.subtitle_languages_input = QLineEdit()
        self.subtitle_languages_input.setText(", ".join(settings.SUBTITLE_LANGUAGES))
        self.subtitle_languages_input.setPlaceholderText("例: ja, en, ko")
        lang_layout.addWidget(self.subtitle_languages_input)
        subtitle_layout.addLayout(lang_layout)

        # Subtitle format
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("字幕フォーマット:"))
        self.subtitle_format_combo = QComboBox()
        self.subtitle_format_combo.addItems(["SRT", "VTT", "ASS", "Best"])
        self.subtitle_format_combo.setCurrentText(settings.SUBTITLE_FORMAT.upper())
        format_layout.addWidget(self.subtitle_format_combo)
        format_layout.addStretch()
        subtitle_layout.addLayout(format_layout)

        self.embed_subtitles_checkbox = QCheckBox("字幕を動画ファイルに埋め込む")
        self.embed_subtitles_checkbox.setChecked(settings.EMBED_SUBTITLES)
        subtitle_layout.addWidget(self.embed_subtitles_checkbox)

        layout.addWidget(subtitle_group)

        # Future features
        future_group = QGroupBox("将来実装予定の機能")
        future_layout = QVBoxLayout()
        future_group.setLayout(future_layout)

        future_info = QLabel(
            "以下の機能は将来のバージョンで実装予定です：\n\n"
            "• Whisperによる自動文字起こし\n"
            "• AI翻訳による多言語字幕生成\n"
            "• 字幕編集・タイミング調整"
        )
        future_info.setWordWrap(True)
        future_info.setStyleSheet("color: gray;")
        future_layout.addWidget(future_info)

        self.enable_transcription_checkbox = QCheckBox("文字起こし機能を有効化 (未実装)")
        self.enable_transcription_checkbox.setEnabled(False)
        future_layout.addWidget(self.enable_transcription_checkbox)

        self.enable_translation_checkbox = QCheckBox("字幕翻訳機能を有効化 (未実装)")
        self.enable_translation_checkbox.setEnabled(False)
        future_layout.addWidget(self.enable_translation_checkbox)

        layout.addWidget(future_group)
        layout.addStretch()

        return widget

    def _create_playlist_tab(self):
        """Create playlist/channel download settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Playlist settings
        playlist_group = QGroupBox("プレイリスト設定")
        playlist_layout = QVBoxLayout()
        playlist_group.setLayout(playlist_layout)

        self.playlist_download_checkbox = QCheckBox("プレイリスト全体をダウンロード")
        self.playlist_download_checkbox.setChecked(settings.PLAYLIST_DOWNLOAD)
        playlist_layout.addWidget(self.playlist_download_checkbox)

        # Playlist range
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("範囲:"))
        range_layout.addWidget(QLabel("開始:"))
        self.playlist_start_spin = QSpinBox()
        self.playlist_start_spin.setMinimum(1)
        self.playlist_start_spin.setMaximum(999999)
        self.playlist_start_spin.setValue(settings.PLAYLIST_START)
        range_layout.addWidget(self.playlist_start_spin)

        range_layout.addWidget(QLabel("終了:"))
        self.playlist_end_spin = QSpinBox()
        self.playlist_end_spin.setMinimum(0)
        self.playlist_end_spin.setMaximum(999999)
        self.playlist_end_spin.setValue(settings.PLAYLIST_END if settings.PLAYLIST_END else 0)
        self.playlist_end_spin.setSpecialValueText("最後まで")
        range_layout.addWidget(self.playlist_end_spin)
        range_layout.addStretch()
        playlist_layout.addLayout(range_layout)

        # Playlist items
        items_layout = QHBoxLayout()
        items_layout.addWidget(QLabel("個別指定:"))
        self.playlist_items_input = QLineEdit()
        self.playlist_items_input.setText(settings.PLAYLIST_ITEMS or "")
        self.playlist_items_input.setPlaceholderText("例: 1-5,7,10-15")
        items_layout.addWidget(self.playlist_items_input)
        playlist_layout.addLayout(items_layout)

        # Max downloads
        max_layout = QHBoxLayout()
        max_layout.addWidget(QLabel("最大ダウンロード数:"))
        self.max_downloads_spin = QSpinBox()
        self.max_downloads_spin.setMinimum(0)
        self.max_downloads_spin.setMaximum(999999)
        self.max_downloads_spin.setValue(settings.MAX_DOWNLOADS if settings.MAX_DOWNLOADS else 0)
        self.max_downloads_spin.setSpecialValueText("制限なし")
        max_layout.addWidget(self.max_downloads_spin)
        max_layout.addStretch()
        playlist_layout.addLayout(max_layout)

        layout.addWidget(playlist_group)

        # Archive settings
        archive_group = QGroupBox("アーカイブ設定")
        archive_layout = QVBoxLayout()
        archive_group.setLayout(archive_layout)

        self.download_archive_checkbox = QCheckBox("ダウンロード済みを記録（重複防止）")
        self.download_archive_checkbox.setChecked(settings.DOWNLOAD_ARCHIVE)
        archive_layout.addWidget(self.download_archive_checkbox)

        archive_file_layout = QHBoxLayout()
        archive_file_layout.addWidget(QLabel("アーカイブファイル:"))
        self.archive_file_input = QLineEdit()
        self.archive_file_input.setText(str(settings.ARCHIVE_FILE))
        self.archive_file_input.setReadOnly(True)
        archive_file_layout.addWidget(self.archive_file_input)
        archive_layout.addLayout(archive_file_layout)

        layout.addWidget(archive_group)

        # Filters
        filter_group = QGroupBox("フィルター")
        filter_layout = QVBoxLayout()
        filter_group.setLayout(filter_layout)

        # Date filters
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("日付範囲:"))
        date_layout.addWidget(QLabel("開始:"))
        self.date_after_input = QLineEdit()
        self.date_after_input.setText(settings.DATE_AFTER or "")
        self.date_after_input.setPlaceholderText("YYYYMMDD")
        date_layout.addWidget(self.date_after_input)
        date_layout.addWidget(QLabel("終了:"))
        self.date_before_input = QLineEdit()
        self.date_before_input.setText(settings.DATE_BEFORE or "")
        self.date_before_input.setPlaceholderText("YYYYMMDD")
        date_layout.addWidget(self.date_before_input)
        date_layout.addStretch()
        filter_layout.addLayout(date_layout)

        # View count filters
        views_layout = QHBoxLayout()
        views_layout.addWidget(QLabel("再生回数:"))
        views_layout.addWidget(QLabel("最小:"))
        self.min_views_spin = QSpinBox()
        self.min_views_spin.setMinimum(0)
        self.min_views_spin.setMaximum(999999999)
        self.min_views_spin.setValue(settings.MIN_VIEWS if settings.MIN_VIEWS else 0)
        self.min_views_spin.setSpecialValueText("制限なし")
        views_layout.addWidget(self.min_views_spin)
        views_layout.addWidget(QLabel("最大:"))
        self.max_views_spin = QSpinBox()
        self.max_views_spin.setMinimum(0)
        self.max_views_spin.setMaximum(999999999)
        self.max_views_spin.setValue(settings.MAX_VIEWS if settings.MAX_VIEWS else 0)
        self.max_views_spin.setSpecialValueText("制限なし")
        views_layout.addWidget(self.max_views_spin)
        views_layout.addStretch()
        filter_layout.addLayout(views_layout)

        # Duration filters
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("動画長(秒):"))
        duration_layout.addWidget(QLabel("最小:"))
        self.min_duration_spin = QSpinBox()
        self.min_duration_spin.setMinimum(0)
        self.min_duration_spin.setMaximum(999999)
        self.min_duration_spin.setValue(settings.MIN_DURATION if settings.MIN_DURATION else 0)
        self.min_duration_spin.setSpecialValueText("制限なし")
        duration_layout.addWidget(self.min_duration_spin)
        duration_layout.addWidget(QLabel("最大:"))
        self.max_duration_spin = QSpinBox()
        self.max_duration_spin.setMinimum(0)
        self.max_duration_spin.setMaximum(999999)
        self.max_duration_spin.setValue(settings.MAX_DURATION if settings.MAX_DURATION else 0)
        self.max_duration_spin.setSpecialValueText("制限なし")
        duration_layout.addWidget(self.max_duration_spin)
        duration_layout.addStretch()
        filter_layout.addLayout(duration_layout)

        layout.addWidget(filter_group)
        layout.addStretch()

        return widget

    def _create_notification_tab(self):
        """Create notification settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Desktop notifications
        desktop_group = QGroupBox("デスクトップ通知")
        desktop_layout = QVBoxLayout()
        desktop_group.setLayout(desktop_layout)

        self.enable_notifications_checkbox = QCheckBox("通知を有効にする")
        self.enable_notifications_checkbox.setChecked(settings.ENABLE_NOTIFICATIONS)
        desktop_layout.addWidget(self.enable_notifications_checkbox)

        self.desktop_notification_checkbox = QCheckBox("デスクトップ通知を表示")
        self.desktop_notification_checkbox.setChecked(settings.DESKTOP_NOTIFICATION)
        desktop_layout.addWidget(self.desktop_notification_checkbox)

        self.notification_sound_checkbox = QCheckBox("通知音を鳴らす")
        self.notification_sound_checkbox.setChecked(settings.NOTIFICATION_SOUND)
        desktop_layout.addWidget(self.notification_sound_checkbox)

        # Notification triggers
        desktop_layout.addWidget(QLabel("通知タイミング:"))
        self.notify_on_start_checkbox = QCheckBox("ダウンロード開始時")
        self.notify_on_start_checkbox.setChecked(settings.NOTIFY_ON_START)
        desktop_layout.addWidget(self.notify_on_start_checkbox)

        self.notify_on_complete_checkbox = QCheckBox("ダウンロード完了時")
        self.notify_on_complete_checkbox.setChecked(settings.NOTIFY_ON_COMPLETE)
        desktop_layout.addWidget(self.notify_on_complete_checkbox)

        self.notify_on_error_checkbox = QCheckBox("エラー発生時")
        self.notify_on_error_checkbox.setChecked(settings.NOTIFY_ON_ERROR)
        desktop_layout.addWidget(self.notify_on_error_checkbox)

        # Test button
        test_notification_button = QPushButton("通知をテスト")
        test_notification_button.clicked.connect(self._test_notification)
        desktop_layout.addWidget(test_notification_button)

        layout.addWidget(desktop_group)

        # Email notifications
        email_group = QGroupBox("メール通知")
        email_layout = QVBoxLayout()
        email_group.setLayout(email_layout)

        self.email_notification_checkbox = QCheckBox("メール通知を有効にする")
        self.email_notification_checkbox.setChecked(settings.EMAIL_NOTIFICATION)
        email_layout.addWidget(self.email_notification_checkbox)

        # SMTP settings
        smtp_layout = QHBoxLayout()
        smtp_layout.addWidget(QLabel("SMTPサーバー:"))
        self.smtp_server_input = QLineEdit()
        self.smtp_server_input.setText(settings.EMAIL_SMTP_SERVER or "")
        self.smtp_server_input.setPlaceholderText("smtp.gmail.com")
        smtp_layout.addWidget(self.smtp_server_input)
        smtp_layout.addWidget(QLabel("ポート:"))
        self.smtp_port_spin = QSpinBox()
        self.smtp_port_spin.setMinimum(1)
        self.smtp_port_spin.setMaximum(65535)
        self.smtp_port_spin.setValue(settings.EMAIL_SMTP_PORT)
        smtp_layout.addWidget(self.smtp_port_spin)
        email_layout.addLayout(smtp_layout)

        self.smtp_use_tls_checkbox = QCheckBox("TLS/STARTTLSを使用")
        self.smtp_use_tls_checkbox.setChecked(settings.EMAIL_USE_TLS)
        email_layout.addWidget(self.smtp_use_tls_checkbox)

        # Email credentials
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("ユーザー名:"))
        self.email_username_input = QLineEdit()
        self.email_username_input.setText(settings.EMAIL_USERNAME or "")
        username_layout.addWidget(self.email_username_input)
        email_layout.addLayout(username_layout)

        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("パスワード:"))
        self.email_password_input = QLineEdit()
        self.email_password_input.setEchoMode(QLineEdit.Password)
        self.email_password_input.setText(settings.EMAIL_PASSWORD or "")
        self.email_password_input.setPlaceholderText("アプリパスワードを使用")
        password_layout.addWidget(self.email_password_input)
        email_layout.addLayout(password_layout)

        # Email addresses
        from_layout = QHBoxLayout()
        from_layout.addWidget(QLabel("送信元:"))
        self.email_from_input = QLineEdit()
        self.email_from_input.setText(settings.EMAIL_FROM or "")
        from_layout.addWidget(self.email_from_input)
        email_layout.addLayout(from_layout)

        to_layout = QHBoxLayout()
        to_layout.addWidget(QLabel("送信先:"))
        self.email_to_input = QLineEdit()
        self.email_to_input.setText(settings.EMAIL_TO or "")
        to_layout.addWidget(self.email_to_input)
        email_layout.addLayout(to_layout)

        # Gmail help
        gmail_help = QLabel(
            "💡 Gmailの場合: 2段階認証を有効にして"
            "<a href='https://support.google.com/accounts/answer/185833'>アプリパスワード</a>を使用してください"
        )
        gmail_help.setOpenExternalLinks(True)
        gmail_help.setWordWrap(True)
        gmail_help.setStyleSheet("color: #666; font-size: 10pt;")
        email_layout.addWidget(gmail_help)

        layout.addWidget(email_group)
        layout.addStretch()

        return widget

    def _create_advanced_tab(self):
        """Create advanced settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Speed limiting
        speed_group = QGroupBox("ダウンロード速度制限")
        speed_layout = QVBoxLayout()
        speed_group.setLayout(speed_layout)

        self.limit_speed_checkbox = QCheckBox("ダウンロード速度を制限する")
        self.limit_speed_checkbox.setChecked(settings.LIMIT_DOWNLOAD_SPEED)
        speed_layout.addWidget(self.limit_speed_checkbox)

        speed_value_layout = QHBoxLayout()
        speed_value_layout.addWidget(QLabel("最大速度:"))
        self.max_speed_spin = QSpinBox()
        self.max_speed_spin.setMinimum(0)
        self.max_speed_spin.setMaximum(999999)
        self.max_speed_spin.setValue(settings.MAX_DOWNLOAD_SPEED if settings.MAX_DOWNLOAD_SPEED else 1024)
        self.max_speed_spin.setSuffix(" KB/s")
        speed_value_layout.addWidget(self.max_speed_spin)
        speed_value_layout.addWidget(QLabel("(1024 KB/s = 1 MB/s)"))
        speed_value_layout.addStretch()
        speed_layout.addLayout(speed_value_layout)

        layout.addWidget(speed_group)

        # Auto-update
        update_group = QGroupBox("自動アップデート")
        update_layout = QVBoxLayout()
        update_group.setLayout(update_layout)

        self.auto_update_checkbox = QCheckBox("yt-dlpを自動アップデート")
        self.auto_update_checkbox.setChecked(settings.AUTO_UPDATE_YTDLP)
        update_layout.addWidget(self.auto_update_checkbox)

        self.check_update_on_start_checkbox = QCheckBox("起動時に更新をチェック")
        self.check_update_on_start_checkbox.setChecked(settings.CHECK_UPDATE_ON_START)
        update_layout.addWidget(self.check_update_on_start_checkbox)

        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("更新チェック間隔:"))
        self.update_interval_spin = QSpinBox()
        self.update_interval_spin.setMinimum(1)
        self.update_interval_spin.setMaximum(365)
        self.update_interval_spin.setValue(settings.UPDATE_INTERVAL_DAYS)
        self.update_interval_spin.setSuffix(" 日")
        interval_layout.addWidget(self.update_interval_spin)
        interval_layout.addStretch()
        update_layout.addLayout(interval_layout)

        # Update status and button
        self.update_status_label = QLabel("状態: 確認中...")
        update_layout.addWidget(self.update_status_label)

        check_update_button = QPushButton("今すぐ更新をチェック")
        check_update_button.clicked.connect(self._check_updates)
        update_layout.addWidget(check_update_button)

        layout.addWidget(update_group)

        # Proxy settings
        proxy_group = QGroupBox("プロキシ設定")
        proxy_layout = QVBoxLayout()
        proxy_group.setLayout(proxy_layout)

        self.enable_proxy_checkbox = QCheckBox("プロキシを使用する")
        self.enable_proxy_checkbox.setChecked(settings.ENABLE_PROXY)
        proxy_layout.addWidget(self.enable_proxy_checkbox)

        proxy_type_layout = QHBoxLayout()
        proxy_type_layout.addWidget(QLabel("プロキシタイプ:"))
        self.proxy_type_combo = QComboBox()
        self.proxy_type_combo.addItems(["HTTP", "HTTPS", "SOCKS5"])
        self.proxy_type_combo.setCurrentText(settings.PROXY_TYPE.upper())
        proxy_type_layout.addWidget(self.proxy_type_combo)
        proxy_type_layout.addStretch()
        proxy_layout.addLayout(proxy_type_layout)

        # HTTP proxy
        http_proxy_layout = QHBoxLayout()
        http_proxy_layout.addWidget(QLabel("HTTPプロキシ:"))
        self.http_proxy_input = QLineEdit()
        self.http_proxy_input.setText(settings.HTTP_PROXY or "")
        self.http_proxy_input.setPlaceholderText("http://proxy.example.com:8080")
        http_proxy_layout.addWidget(self.http_proxy_input)
        proxy_layout.addLayout(http_proxy_layout)

        # HTTPS proxy
        https_proxy_layout = QHBoxLayout()
        https_proxy_layout.addWidget(QLabel("HTTPSプロキシ:"))
        self.https_proxy_input = QLineEdit()
        self.https_proxy_input.setText(settings.HTTPS_PROXY or "")
        self.https_proxy_input.setPlaceholderText("http://proxy.example.com:8080")
        https_proxy_layout.addWidget(self.https_proxy_input)
        proxy_layout.addLayout(https_proxy_layout)

        # SOCKS proxy
        socks_proxy_layout = QHBoxLayout()
        socks_proxy_layout.addWidget(QLabel("SOCKSプロキシ:"))
        self.socks_proxy_input = QLineEdit()
        self.socks_proxy_input.setText(settings.SOCKS_PROXY or "")
        self.socks_proxy_input.setPlaceholderText("socks5://proxy.example.com:1080")
        socks_proxy_layout.addWidget(self.socks_proxy_input)
        proxy_layout.addLayout(socks_proxy_layout)

        # Proxy auth
        proxy_auth_label = QLabel("認証（オプション）:")
        proxy_layout.addWidget(proxy_auth_label)

        proxy_username_layout = QHBoxLayout()
        proxy_username_layout.addWidget(QLabel("ユーザー名:"))
        self.proxy_username_input = QLineEdit()
        self.proxy_username_input.setText(settings.PROXY_USERNAME or "")
        proxy_username_layout.addWidget(self.proxy_username_input)
        proxy_layout.addLayout(proxy_username_layout)

        proxy_password_layout = QHBoxLayout()
        proxy_password_layout.addWidget(QLabel("パスワード:"))
        self.proxy_password_input = QLineEdit()
        self.proxy_password_input.setEchoMode(QLineEdit.Password)
        self.proxy_password_input.setText(settings.PROXY_PASSWORD or "")
        proxy_password_layout.addWidget(self.proxy_password_input)
        proxy_layout.addLayout(proxy_password_layout)

        layout.addWidget(proxy_group)
        layout.addStretch()

        return widget

    def _create_auth_tab(self):
        """Create authentication settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Authentication
        auth_group = QGroupBox("認証")
        auth_layout = QVBoxLayout()
        auth_group.setLayout(auth_layout)

        auth_info = QLabel(
            "YouTubeの年齢制限付き動画や会員限定動画をダウンロードするには、"
            "ブラウザから自動的にログイン情報（Cookie）を取得します。\n\n"
            "または、Google OAuth 2.0で認証することもできます。"
        )
        auth_info.setWordWrap(True)
        auth_layout.addWidget(auth_info)

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

        # Cookie info
        cookie_info = QLabel(
            "💡 ブラウザのCookieは自動的に検出されます。\n"
            "Chrome、Firefox、Edgeなどでログインしていれば、追加の設定は不要です。"
        )
        cookie_info.setWordWrap(True)
        cookie_info.setStyleSheet("color: #666; margin-top: 10px;")
        auth_layout.addWidget(cookie_info)

        layout.addWidget(auth_group)
        layout.addStretch()

        return widget

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
        elif preset_key in settings.OUTPUT_TEMPLATE_PRESETS:
            template = settings.OUTPUT_TEMPLATE_PRESETS[preset_key]
        else:
            template = "%(uploader)s/%(title)s.%(ext)s"

        # Generate preview
        preview = template.replace('%(uploader)s', 'チャンネル名')
        preview = preview.replace('%(title)s', '動画タイトル')
        preview = preview.replace('%(ext)s', 'mp4')
        preview = preview.replace('%(upload_date>%Y)s', '2025')
        preview = preview.replace('%(upload_date>%m)s', '01')
        preview = preview.replace('%(upload_date>%Y-%m)s', '2025-01')
        preview = preview.replace('%(id)s', 'dQw4w9WgXcQ')
        preview = preview.replace('%(resolution)s', '1080p')
        preview = preview.replace('%(playlist_title|)s', 'プレイリスト名')

        self.template_preview_label.setText(f"プレビュー: {preview}")

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
<li><b>%(playlist_title)s</b> - プレイリスト名</li>
</ul>

<h4>📝 テンプレート例:</h4>
<ul>
<li><code>%(uploader)s/%(title)s.%(ext)s</code><br>
→ チャンネル名/動画タイトル.mp4</li>

<li><code>%(upload_date>%Y)s/%(upload_date>%m)s/%(title)s.%(ext)s</code><br>
→ 2025/01/動画タイトル.mp4</li>

<li><code>%(uploader)s/[%(id)s] %(title)s.%(ext)s</code><br>
→ チャンネル名/[dQw4w9WgXcQ] 動画タイトル.mp4</li>
</ul>

<p>詳細: <a href="https://github.com/yt-dlp/yt-dlp#output-template">yt-dlp Output Template Documentation</a></p>
"""

        msg = QMessageBox(self)
        msg.setWindowTitle("出力テンプレート ヘルプ")
        msg.setTextFormat(Qt.RichText)
        msg.setText(help_text)
        msg.setIcon(QMessageBox.Information)
        msg.exec()

    def _test_notification(self):
        """Test desktop notification"""
        if not self.notification_manager:
            QMessageBox.warning(self, "警告", "通知マネージャーが初期化されていません")
            return

        try:
            self.notification_manager.test_notification()
            QMessageBox.information(
                self,
                "テスト完了",
                "テスト通知を送信しました。システムトレイを確認してください。"
            )
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"通知テストに失敗しました:\n{str(e)}")
            logger.error(f"Notification test failed: {e}", exc_info=True)

    def _check_updates(self):
        """Check for yt-dlp updates"""
        if not self.updater_manager:
            QMessageBox.warning(self, "警告", "アップデートマネージャーが初期化されていません")
            return

        try:
            import asyncio
            from gui.main_window import MainWindow
            parent = self.window()

            if isinstance(parent, MainWindow) and parent.service_thread and parent.service_thread.loop:
                # Show checking message
                self.update_status_label.setText("状態: 確認中...")

                # Check for updates asynchronously
                future = asyncio.run_coroutine_threadsafe(
                    self.updater_manager.check_and_update(force=True),
                    parent.service_thread.loop
                )
                success, message = future.result(timeout=60)

                self.update_status_label.setText(f"状態: {message}")

                if success:
                    QMessageBox.information(self, "アップデート", message)
                else:
                    QMessageBox.warning(self, "アップデート", message)
            else:
                raise RuntimeError("イベントループが初期化されていません")

        except Exception as e:
            self.update_status_label.setText("状態: エラー")
            QMessageBox.critical(self, "エラー", f"更新チェックに失敗しました:\n{str(e)}")
            logger.error(f"Update check failed: {e}", exc_info=True)

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
        """Save all settings"""
        try:
            # Download settings
            settings.DOWNLOAD_DIR = self.download_dir_input.text()
            settings.MAX_CONCURRENT_DOWNLOADS = self.concurrent_spin.value()
            settings.SKIP_DUPLICATES = self.skip_duplicates_checkbox.isChecked()
            settings.CHECK_BY_VIDEO_ID = self.check_by_video_id_checkbox.isChecked()
            settings.CHECK_BY_FILENAME = self.check_by_filename_checkbox.isChecked()

            # Output template
            preset_map = {0: "channel", 1: "date", 2: "channel_date", 3: "channel_type",
                         4: "flat", 5: "detailed", 6: "quality", 7: "custom"}
            preset_key = preset_map.get(self.template_preset_combo.currentIndex(), "channel")
            settings.DIRECTORY_STRUCTURE = preset_key
            settings.CUSTOM_OUTPUT_TEMPLATE = self.custom_template_input.text()

            # Metadata settings
            settings.DOWNLOAD_THUMBNAIL = self.download_thumbnail_checkbox.isChecked()
            settings.EMBED_THUMBNAIL = self.embed_thumbnail_checkbox.isChecked()
            settings.WRITE_INFO_JSON = self.write_info_json_checkbox.isChecked()
            settings.WRITE_DESCRIPTION = self.write_description_checkbox.isChecked()

            # Quality settings
            quality_map = {0: "best", 1: "2160p", 2: "1440p", 3: "1080p",
                          4: "720p", 5: "480p", 6: "360p", 7: "worst", 8: "audio_only"}
            settings.VIDEO_QUALITY = quality_map.get(self.quality_combo.currentIndex(), "best")
            settings.VIDEO_FORMAT = self.video_format_combo.currentText().lower()
            settings.DOWNLOAD_VIDEO = self.download_video_checkbox.isChecked()

            audio_quality_map = {0: "best", 1: "320k", 2: "256k", 3: "192k", 4: "128k", 5: "worst"}
            settings.AUDIO_QUALITY = audio_quality_map.get(self.audio_quality_combo.currentIndex(), "best")
            settings.AUDIO_FORMAT = self.audio_format_combo.currentText().lower()
            settings.DOWNLOAD_AUDIO = self.download_audio_checkbox.isChecked()
            settings.ENABLE_GPU = self.gpu_checkbox.isChecked()

            # Subtitle settings
            settings.DOWNLOAD_SUBTITLES = self.download_subtitles_checkbox.isChecked()
            settings.DOWNLOAD_AUTO_SUBTITLES = self.download_auto_subtitles_checkbox.isChecked()

            # Parse subtitle languages
            lang_text = self.subtitle_languages_input.text()
            settings.SUBTITLE_LANGUAGES = [lang.strip() for lang in lang_text.split(",") if lang.strip()]

            settings.SUBTITLE_FORMAT = self.subtitle_format_combo.currentText().lower()
            settings.EMBED_SUBTITLES = self.embed_subtitles_checkbox.isChecked()

            # Playlist settings
            settings.PLAYLIST_DOWNLOAD = self.playlist_download_checkbox.isChecked()
            settings.PLAYLIST_START = self.playlist_start_spin.value()
            settings.PLAYLIST_END = self.playlist_end_spin.value() if self.playlist_end_spin.value() > 0 else None
            settings.PLAYLIST_ITEMS = self.playlist_items_input.text() or None
            settings.MAX_DOWNLOADS = self.max_downloads_spin.value() if self.max_downloads_spin.value() > 0 else None
            settings.DOWNLOAD_ARCHIVE = self.download_archive_checkbox.isChecked()

            # Filters
            settings.DATE_AFTER = self.date_after_input.text() or None
            settings.DATE_BEFORE = self.date_before_input.text() or None
            settings.MIN_VIEWS = self.min_views_spin.value() if self.min_views_spin.value() > 0 else None
            settings.MAX_VIEWS = self.max_views_spin.value() if self.max_views_spin.value() > 0 else None
            settings.MIN_DURATION = self.min_duration_spin.value() if self.min_duration_spin.value() > 0 else None
            settings.MAX_DURATION = self.max_duration_spin.value() if self.max_duration_spin.value() > 0 else None

            # Notification settings
            settings.ENABLE_NOTIFICATIONS = self.enable_notifications_checkbox.isChecked()
            settings.DESKTOP_NOTIFICATION = self.desktop_notification_checkbox.isChecked()
            settings.NOTIFICATION_SOUND = self.notification_sound_checkbox.isChecked()
            settings.NOTIFY_ON_START = self.notify_on_start_checkbox.isChecked()
            settings.NOTIFY_ON_COMPLETE = self.notify_on_complete_checkbox.isChecked()
            settings.NOTIFY_ON_ERROR = self.notify_on_error_checkbox.isChecked()

            # Email settings
            settings.EMAIL_NOTIFICATION = self.email_notification_checkbox.isChecked()
            settings.EMAIL_SMTP_SERVER = self.smtp_server_input.text() or None
            settings.EMAIL_SMTP_PORT = self.smtp_port_spin.value()
            settings.EMAIL_USE_TLS = self.smtp_use_tls_checkbox.isChecked()
            settings.EMAIL_USERNAME = self.email_username_input.text() or None
            settings.EMAIL_PASSWORD = self.email_password_input.text() or None
            settings.EMAIL_FROM = self.email_from_input.text() or None
            settings.EMAIL_TO = self.email_to_input.text() or None

            # Advanced settings
            settings.LIMIT_DOWNLOAD_SPEED = self.limit_speed_checkbox.isChecked()
            settings.MAX_DOWNLOAD_SPEED = self.max_speed_spin.value() if self.limit_speed_checkbox.isChecked() else None

            settings.AUTO_UPDATE_YTDLP = self.auto_update_checkbox.isChecked()
            settings.CHECK_UPDATE_ON_START = self.check_update_on_start_checkbox.isChecked()
            settings.UPDATE_INTERVAL_DAYS = self.update_interval_spin.value()

            # Proxy settings
            settings.ENABLE_PROXY = self.enable_proxy_checkbox.isChecked()
            settings.PROXY_TYPE = self.proxy_type_combo.currentText().lower()
            settings.HTTP_PROXY = self.http_proxy_input.text() or None
            settings.HTTPS_PROXY = self.https_proxy_input.text() or None
            settings.SOCKS_PROXY = self.socks_proxy_input.text() or None
            settings.PROXY_USERNAME = self.proxy_username_input.text() or None
            settings.PROXY_PASSWORD = self.proxy_password_input.text() or None

            # Save to database
            if self.db_manager:
                self.db_manager.set_setting('download_dir', str(settings.DOWNLOAD_DIR))
                self.db_manager.set_setting('max_concurrent_downloads', settings.MAX_CONCURRENT_DOWNLOADS)
                self.db_manager.set_setting('video_quality', settings.VIDEO_QUALITY)
                self.db_manager.set_setting('enable_gpu', settings.ENABLE_GPU)
                self.db_manager.set_setting('directory_structure', settings.DIRECTORY_STRUCTURE)
                self.db_manager.set_setting('custom_output_template', settings.CUSTOM_OUTPUT_TEMPLATE)
                # Save more settings...

            QMessageBox.information(self, "成功", "設定を保存しました")
            logger.info("Settings saved successfully")

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"設定の保存に失敗しました:\n{str(e)}")
            logger.error(f"Failed to save settings: {e}", exc_info=True)

    def _load_settings(self):
        """Load settings from database"""
        if not self.db_manager:
            return

        try:
            # Load basic settings
            download_dir = self.db_manager.get_setting('download_dir')
            if download_dir:
                self.download_dir_input.setText(download_dir)

            max_concurrent = self.db_manager.get_setting('max_concurrent_downloads')
            if max_concurrent:
                self.concurrent_spin.setValue(int(max_concurrent))

            video_quality = self.db_manager.get_setting('video_quality')
            if video_quality:
                quality_map = {"best": 0, "2160p": 1, "1440p": 2, "1080p": 3,
                              "720p": 4, "480p": 5, "360p": 6, "worst": 7, "audio_only": 8}
                index = quality_map.get(video_quality, 0)
                self.quality_combo.setCurrentIndex(index)

            enable_gpu = self.db_manager.get_setting('enable_gpu')
            if enable_gpu is not None:
                self.gpu_checkbox.setChecked(bool(enable_gpu))

            # Load template settings
            directory_structure = self.db_manager.get_setting('directory_structure')
            if directory_structure:
                preset_index_map = {
                    "channel": 0, "date": 1, "channel_date": 2, "channel_type": 3,
                    "flat": 4, "detailed": 5, "quality": 6, "custom": 7
                }
                index = preset_index_map.get(directory_structure, 0)
                self.template_preset_combo.setCurrentIndex(index)

            custom_template = self.db_manager.get_setting('custom_output_template')
            if custom_template:
                self.custom_template_input.setText(custom_template)

            # Update auth status
            if self.auth_manager and self.auth_manager.is_authenticated():
                self.auth_status_label.setText("認証状態: 認証済み")

            # Update yt-dlp version status
            if self.updater_manager:
                self.update_status_label.setText("状態: 読み込み中...")

        except Exception as e:
            logger.error(f"Failed to load settings: {e}", exc_info=True)
