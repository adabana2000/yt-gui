# YouTube ダウンローダー 実装案ドキュメント

## 1. アーキテクチャ概要

### 1.1 システム構成図

```
┌─────────────────────────────────────────────────────────────┐
│                         ユーザーインターフェース層                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ Desktop  │ │   Web    │ │   CLI    │ │   API    │   │
│  │   GUI    │ │    UI    │ │Interface │ │ Client   │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        アプリケーション層                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    Core Service Manager                │  │
│  ├──────────┬──────────┬──────────┬──────────┬─────────┤  │
│  │Download  │Schedule  │ Encode   │Metadata  │  Auth   │  │
│  │ Manager  │ Manager  │ Manager  │ Manager  │Manager  │  │
│  └──────────┴──────────┴──────────┴──────────┴─────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         インフラ層                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ yt-dlp   │ │  FFmpeg  │ │  SQLite  │ │  Redis   │   │
│  │ Wrapper  │ │ Wrapper  │ │    DB    │ │  Cache   │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 技術スタック

#### バックエンド
- **言語**: Python 3.10+
- **フレームワーク**: FastAPI (Web API), asyncio (非同期処理)
- **タスクキュー**: Celery + Redis
- **データベース**: SQLite (ローカル), PostgreSQL (オプション)
- **キャッシュ**: Redis

#### フロントエンド
- **デスクトップGUI**: 
  - Electron + React + TypeScript
  - または PyQt6/PySide6
- **Web UI**: React + TypeScript + Material-UI
- **状態管理**: Redux Toolkit
- **通信**: Axios, WebSocket (socket.io)

#### 外部ツール
- **yt-dlp**: 最新版
- **FFmpeg**: 5.0+
- **GPU エンコード**: NVIDIA SDK, Intel Media SDK

## 2. モジュール詳細設計

### 2.1 Core Service Manager

```python
# core/service_manager.py
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass

@dataclass
class ServiceConfig:
    """サービス設定"""
    max_workers: int = 5
    retry_count: int = 3
    timeout: int = 300

class BaseService(ABC):
    """基底サービスクラス"""
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.is_running = False
        
    @abstractmethod
    async def start(self) -> None:
        """サービス開始"""
        pass
        
    @abstractmethod
    async def stop(self) -> None:
        """サービス停止"""
        pass

class ServiceManager:
    """サービス管理クラス"""
    
    def __init__(self):
        self.services: Dict[str, BaseService] = {}
        self.event_bus = EventBus()
        
    def register_service(self, name: str, service: BaseService) -> None:
        """サービス登録"""
        self.services[name] = service
        
    async def start_all(self) -> None:
        """全サービス起動"""
        tasks = [service.start() for service in self.services.values()]
        await asyncio.gather(*tasks)
```

### 2.2 Download Manager

```python
# modules/download_manager.py
import asyncio
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import yt_dlp
from concurrent.futures import ThreadPoolExecutor

class DownloadStatus(Enum):
    """ダウンロード状態"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class DownloadTask:
    """ダウンロードタスク"""
    id: str
    url: str
    output_path: str
    format_id: Optional[str] = None
    status: DownloadStatus = DownloadStatus.PENDING
    progress: float = 0.0
    speed: float = 0.0
    eta: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class DownloadManager(BaseService):
    """ダウンロード管理クラス"""
    
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self.queue: asyncio.Queue = asyncio.Queue()
        self.active_downloads: Dict[str, DownloadTask] = {}
        self.executor = ThreadPoolExecutor(max_workers=config.max_workers)
        self.ydl_opts = self._get_default_ydl_opts()
        
    def _get_default_ydl_opts(self) -> Dict[str, Any]:
        """デフォルトyt-dlpオプション取得"""
        return {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': '%(title)s.%(ext)s',
            'progress_hooks': [self._progress_hook],
            'postprocessor_hooks': [self._postprocessor_hook],
            'concurrent_fragment_downloads': 5,
            'nocheckcertificate': True,
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
        }
    
    def _progress_hook(self, d: Dict[str, Any]) -> None:
        """進捗フック"""
        if d['status'] == 'downloading':
            task_id = d.get('task_id')
            if task_id and task_id in self.active_downloads:
                task = self.active_downloads[task_id]
                task.progress = d.get('downloaded_bytes', 0) / d.get('total_bytes', 1) * 100
                task.speed = d.get('speed', 0)
                task.eta = d.get('eta', None)
                
                # イベント発火
                self.event_bus.emit('download:progress', {
                    'task_id': task_id,
                    'progress': task.progress,
                    'speed': task.speed,
                    'eta': task.eta
                })
    
    async def add_download(self, url: str, **kwargs) -> DownloadTask:
        """ダウンロード追加"""
        task = DownloadTask(
            id=self._generate_task_id(),
            url=url,
            output_path=kwargs.get('output_path', './downloads/'),
            format_id=kwargs.get('format_id')
        )
        
        await self.queue.put(task)
        return task
    
    async def start(self) -> None:
        """ダウンロードマネージャー開始"""
        self.is_running = True
        
        # ワーカー起動
        workers = [
            asyncio.create_task(self._download_worker(f"worker-{i}"))
            for i in range(self.config.max_workers)
        ]
        
        await asyncio.gather(*workers)
    
    async def _download_worker(self, worker_id: str) -> None:
        """ダウンロードワーカー"""
        while self.is_running:
            try:
                task = await asyncio.wait_for(
                    self.queue.get(), 
                    timeout=1.0
                )
                
                self.active_downloads[task.id] = task
                task.status = DownloadStatus.DOWNLOADING
                task.started_at = datetime.now()
                
                # yt-dlpで実際のダウンロード実行
                await self._execute_download(task)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
    
    async def _execute_download(self, task: DownloadTask) -> None:
        """実際のダウンロード処理"""
        try:
            opts = self.ydl_opts.copy()
            opts['outtmpl'] = f"{task.output_path}/%(title)s.%(ext)s"
            
            if task.format_id:
                opts['format'] = task.format_id
            
            # yt-dlpインスタンス作成
            with yt_dlp.YoutubeDL(opts) as ydl:
                # メタデータ取得
                info = await asyncio.get_event_loop().run_in_executor(
                    self.executor, 
                    ydl.extract_info, 
                    task.url, 
                    False
                )
                task.metadata = info
                
                # ダウンロード実行
                await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    ydl.download,
                    [task.url]
                )
            
            task.status = DownloadStatus.COMPLETED
            task.completed_at = datetime.now()
            
        except Exception as e:
            task.status = DownloadStatus.FAILED
            task.error_message = str(e)
            logger.error(f"Download failed for {task.url}: {e}")
            
        finally:
            del self.active_downloads[task.id]
```

### 2.3 Schedule Manager

```python
# modules/schedule_manager.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import uuid

@dataclass
class ScheduledJob:
    """スケジュールジョブ"""
    id: str
    name: str
    cron_expression: str
    task_type: str
    task_params: Dict[str, Any]
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None

class ScheduleManager(BaseService):
    """スケジュール管理クラス"""
    
    def __init__(self, config: ServiceConfig, download_manager: DownloadManager):
        super().__init__(config)
        self.scheduler = AsyncIOScheduler()
        self.download_manager = download_manager
        self.jobs: Dict[str, ScheduledJob] = {}
        
    async def start(self) -> None:
        """スケジューラー開始"""
        self.scheduler.start()
        await self._load_scheduled_jobs()
        
    async def add_scheduled_job(
        self, 
        name: str,
        cron_expression: str,
        task_type: str,
        task_params: Dict[str, Any]
    ) -> ScheduledJob:
        """スケジュールジョブ追加"""
        job = ScheduledJob(
            id=str(uuid.uuid4()),
            name=name,
            cron_expression=cron_expression,
            task_type=task_type,
            task_params=task_params
        )
        
        trigger = CronTrigger.from_crontab(cron_expression)
        
        self.scheduler.add_job(
            func=self._execute_scheduled_task,
            trigger=trigger,
            args=[job],
            id=job.id,
            name=job.name
        )
        
        self.jobs[job.id] = job
        return job
    
    async def _execute_scheduled_task(self, job: ScheduledJob) -> None:
        """スケジュールタスク実行"""
        try:
            job.last_run = datetime.now()
            
            if job.task_type == "channel_download":
                await self._download_channel_updates(job.task_params)
            elif job.task_type == "playlist_download":
                await self._download_playlist(job.task_params)
                
            # 次回実行時刻更新
            job.next_run = self.scheduler.get_job(job.id).next_run_time
            
        except Exception as e:
            logger.error(f"Scheduled task failed: {job.name}, Error: {e}")
    
    async def _download_channel_updates(self, params: Dict[str, Any]) -> None:
        """チャンネル更新ダウンロード"""
        channel_url = params.get('channel_url')
        last_check = params.get('last_check', datetime.now() - timedelta(days=1))
        
        # 新着動画取得
        with yt_dlp.YoutubeDL({'extract_flat': True}) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            entries = info.get('entries', [])
            
            for entry in entries:
                upload_date = datetime.strptime(entry['upload_date'], '%Y%m%d')
                if upload_date > last_check:
                    await self.download_manager.add_download(
                        url=entry['url'],
                        output_path=params.get('output_path')
                    )
```

### 2.4 Authentication Manager

```python
# modules/auth_manager.py
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
import os
from typing import Optional, Dict, Any

class AuthManager(BaseService):
    """認証管理クラス"""
    
    SCOPES = ['https://www.googleapis.com/auth/youtube.readonly']
    
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self.credentials: Optional[Credentials] = None
        self.cookie_jar: Dict[str, Any] = {}
        
    async def authenticate_google(self, client_secrets_file: str) -> bool:
        """Google認証"""
        creds = None
        token_file = 'token.pickle'
        
        # 保存済みトークン読み込み
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # トークンが無効な場合は再認証
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secrets_file, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # トークン保存
            with open(token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        self.credentials = creds
        return True
    
    def get_cookies_for_ytdlp(self) -> str:
        """yt-dlp用Cookie取得"""
        # ブラウザからCookieを取得
        from browser_cookie3 import chrome, firefox, edge
        
        cookies = []
        try:
            # Chrome Cookies
            for cookie in chrome():
                if 'youtube.com' in cookie.domain:
                    cookies.append(cookie)
        except:
            pass
            
        # Cookie文字列生成
        cookie_str = '; '.join([f"{c.name}={c.value}" for c in cookies])
        return cookie_str
```

### 2.5 Database Manager

```python
# database/models.py
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class DownloadHistory(Base):
    """ダウンロード履歴モデル"""
    __tablename__ = 'download_history'
    
    id = Column(String, primary_key=True)
    url = Column(String, nullable=False, index=True)
    title = Column(String)
    channel_name = Column(String)
    channel_id = Column(String, index=True)
    file_path = Column(String)
    file_size = Column(Integer)
    duration = Column(Integer)
    format = Column(String)
    resolution = Column(String)
    download_date = Column(DateTime, default=datetime.now)
    metadata = Column(Text)  # JSON string
    
class Channel(Base):
    """チャンネルモデル"""
    __tablename__ = 'channels'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    auto_download = Column(Boolean, default=False)
    last_checked = Column(DateTime)
    download_path = Column(String)
    format_preference = Column(String)
    
class ScheduledTask(Base):
    """スケジュールタスクモデル"""
    __tablename__ = 'scheduled_tasks'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    task_type = Column(String, nullable=False)
    cron_expression = Column(String)
    parameters = Column(Text)  # JSON string
    enabled = Column(Boolean, default=True)
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)

# database/db_manager.py
class DatabaseManager:
    """データベース管理クラス"""
    
    def __init__(self, db_path: str = "youtube_downloader.db"):
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
    def add_download_history(self, download_info: Dict[str, Any]) -> None:
        """ダウンロード履歴追加"""
        session = self.Session()
        try:
            history = DownloadHistory(
                id=download_info['id'],
                url=download_info['url'],
                title=download_info.get('title'),
                channel_name=download_info.get('uploader'),
                channel_id=download_info.get('channel_id'),
                file_path=download_info.get('file_path'),
                file_size=download_info.get('filesize'),
                duration=download_info.get('duration'),
                format=download_info.get('format'),
                resolution=download_info.get('resolution'),
                metadata=json.dumps(download_info)
            )
            session.add(history)
            session.commit()
        finally:
            session.close()
    
    def check_duplicate(self, url: str) -> bool:
        """重複チェック"""
        session = self.Session()
        try:
            exists = session.query(DownloadHistory).filter_by(url=url).first() is not None
            return exists
        finally:
            session.close()
```

### 2.6 エンコードマネージャー

```python
# modules/encode_manager.py
import ffmpeg
from typing import Optional, Dict, Any
import subprocess
import os

class EncodeManager(BaseService):
    """エンコード管理クラス"""
    
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self.gpu_available = self._check_gpu_availability()
        
    def _check_gpu_availability(self) -> Dict[str, bool]:
        """GPU利用可能性チェック"""
        availability = {
            'nvidia': False,
            'intel': False,
            'amd': False
        }
        
        # NVIDIA GPU チェック
        try:
            subprocess.run(['nvidia-smi'], capture_output=True, check=True)
            availability['nvidia'] = True
        except:
            pass
            
        return availability
    
    async def encode_video(
        self,
        input_file: str,
        output_file: str,
        codec: str = 'h264',
        preset: str = 'medium',
        bitrate: Optional[str] = None,
        resolution: Optional[str] = None,
        use_gpu: bool = True
    ) -> bool:
        """動画エンコード"""
        try:
            stream = ffmpeg.input(input_file)
            
            # GPU エンコード設定
            if use_gpu and self.gpu_available['nvidia'] and codec == 'h264':
                codec = 'h264_nvenc'
                preset = 'p4'  # NVENC preset
            
            # 解像度変更
            if resolution:
                stream = ffmpeg.filter(stream, 'scale', resolution)
            
            # エンコードパラメータ
            output_params = {
                'c:v': codec,
                'preset': preset,
                'c:a': 'aac',
                'b:a': '128k'
            }
            
            if bitrate:
                output_params['b:v'] = bitrate
            
            # エンコード実行
            stream = ffmpeg.output(stream, output_file, **output_params)
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: ffmpeg.run(stream, overwrite_output=True)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Encode failed: {e}")
            return False
    
    async def extract_audio(
        self,
        input_file: str,
        output_file: str,
        format: str = 'mp3',
        bitrate: str = '192k'
    ) -> bool:
        """音声抽出"""
        try:
            stream = ffmpeg.input(input_file)
            stream = ffmpeg.output(
                stream, 
                output_file,
                acodec='libmp3lame' if format == 'mp3' else 'aac',
                audio_bitrate=bitrate
            )
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: ffmpeg.run(stream, overwrite_output=True)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Audio extraction failed: {e}")
            return False
```

## 3. フロントエンド実装

### 3.1 Electron + React 構成

```typescript
// src/main/index.ts (Electron メインプロセス)
import { app, BrowserWindow, ipcMain, dialog, Tray, Menu } from 'electron';
import { autoUpdater } from 'electron-updater';
import * as path from 'path';

class MainApp {
    private mainWindow: BrowserWindow | null = null;
    private tray: Tray | null = null;
    private apiClient: APIClient;
    
    constructor() {
        this.apiClient = new APIClient('http://localhost:8000');
        this.setupIPC();
    }
    
    async createWindow() {
        this.mainWindow = new BrowserWindow({
            width: 1200,
            height: 800,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                preload: path.join(__dirname, 'preload.js')
            }
        });
        
        if (process.env.NODE_ENV === 'development') {
            this.mainWindow.loadURL('http://localhost:3000');
            this.mainWindow.webContents.openDevTools();
        } else {
            this.mainWindow.loadFile('index.html');
        }
        
        this.createTray();
    }
    
    private createTray() {
        this.tray = new Tray(path.join(__dirname, 'assets/icon.png'));
        
        const contextMenu = Menu.buildFromTemplate([
            {
                label: 'Show App',
                click: () => this.mainWindow?.show()
            },
            {
                label: 'Quit',
                click: () => app.quit()
            }
        ]);
        
        this.tray.setContextMenu(contextMenu);
        this.tray.setToolTip('YouTube Downloader');
    }
    
    private setupIPC() {
        // ダウンロード追加
        ipcMain.handle('download:add', async (event, url: string, options: any) => {
            return await this.apiClient.addDownload(url, options);
        });
        
        // ダウンロード状態取得
        ipcMain.handle('download:status', async (event) => {
            return await this.apiClient.getDownloadStatus();
        });
        
        // 設定取得・更新
        ipcMain.handle('settings:get', async () => {
            return await this.apiClient.getSettings();
        });
        
        ipcMain.handle('settings:update', async (event, settings: any) => {
            return await this.apiClient.updateSettings(settings);
        });
    }
}

// React コンポーネント (src/renderer/App.tsx)
import React, { useState, useEffect } from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, Tab, Tabs } from '@mui/material';
import DownloadTab from './components/DownloadTab';
import ScheduleTab from './components/ScheduleTab';
import HistoryTab from './components/HistoryTab';
import SettingsTab from './components/SettingsTab';

const App: React.FC = () => {
    const [tabValue, setTabValue] = useState(0);
    const [darkMode, setDarkMode] = useState(false);
    
    const theme = createTheme({
        palette: {
            mode: darkMode ? 'dark' : 'light',
        },
    });
    
    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <Box sx={{ width: '100%' }}>
                <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
                    <Tab label="Download" />
                    <Tab label="Schedule" />
                    <Tab label="History" />
                    <Tab label="Settings" />
                </Tabs>
                
                <Box sx={{ p: 3 }}>
                    {tabValue === 0 && <DownloadTab />}
                    {tabValue === 1 && <ScheduleTab />}
                    {tabValue === 2 && <HistoryTab />}
                    {tabValue === 3 && <SettingsTab onThemeChange={setDarkMode} />}
                </Box>
            </Box>
        </ThemeProvider>
    );
};

// ダウンロードタブコンポーネント
import { useState } from 'react';
import { 
    TextField, Button, LinearProgress, List, ListItem, 
    ListItemText, IconButton, Dialog, Select, MenuItem 
} from '@mui/material';
import { Download, Pause, Delete, Settings } from '@mui/icons-material';

const DownloadTab: React.FC = () => {
    const [url, setUrl] = useState('');
    const [downloads, setDownloads] = useState<DownloadTask[]>([]);
    const [settingsOpen, setSettingsOpen] = useState(false);
    const [format, setFormat] = useState('best');
    
    const handleAddDownload = async () => {
        const result = await window.api.addDownload(url, { format });
        if (result.success) {
            setDownloads([...downloads, result.task]);
            setUrl('');
        }
    };
    
    useEffect(() => {
        // WebSocketで進捗更新を受信
        const ws = new WebSocket('ws://localhost:8000/ws');
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'download:progress') {
                setDownloads(prev => 
                    prev.map(d => 
                        d.id === data.task_id 
                            ? { ...d, progress: data.progress }
                            : d
                    )
                );
            }
        };
        
        return () => ws.close();
    }, []);
    
    return (
        <Box>
            <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
                <TextField
                    fullWidth
                    label="YouTube URL"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleAddDownload()}
                />
                <Button
                    variant="contained"
                    startIcon={<Download />}
                    onClick={handleAddDownload}
                >
                    Download
                </Button>
                <IconButton onClick={() => setSettingsOpen(true)}>
                    <Settings />
                </IconButton>
            </Box>
            
            <List>
                {downloads.map(download => (
                    <ListItem key={download.id}>
                        <ListItemText
                            primary={download.title || download.url}
                            secondary={
                                <LinearProgress
                                    variant="determinate"
                                    value={download.progress}
                                />
                            }
                        />
                        <IconButton>
                            <Pause />
                        </IconButton>
                        <IconButton>
                            <Delete />
                        </IconButton>
                    </ListItem>
                ))}
            </List>
            
            <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)}>
                <Box sx={{ p: 3 }}>
                    <Select
                        value={format}
                        onChange={(e) => setFormat(e.target.value)}
                        fullWidth
                    >
                        <MenuItem value="best">Best Quality</MenuItem>
                        <MenuItem value="1080p">1080p</MenuItem>
                        <MenuItem value="720p">720p</MenuItem>
                        <MenuItem value="audio">Audio Only</MenuItem>
                    </Select>
                </Box>
            </Dialog>
        </Box>
    );
};
```

## 4. API設計

### 4.1 RESTful API エンドポイント

```python
# api/main.py
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

app = FastAPI(title="YouTube Downloader API", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# リクエストモデル
class DownloadRequest(BaseModel):
    url: str
    output_path: Optional[str] = "./downloads/"
    format: Optional[str] = "best"
    playlist_items: Optional[str] = None

class ScheduleRequest(BaseModel):
    name: str
    cron_expression: str
    task_type: str
    parameters: Dict[str, Any]

# エンドポイント
@app.post("/api/downloads")
async def create_download(request: DownloadRequest):
    """ダウンロード作成"""
    task = await download_manager.add_download(
        url=request.url,
        output_path=request.output_path,
        format_id=request.format
    )
    return {"success": True, "task": task}

@app.get("/api/downloads")
async def get_downloads():
    """ダウンロード一覧取得"""
    return {
        "active": list(download_manager.active_downloads.values()),
        "queued": download_manager.queue.qsize()
    }

@app.delete("/api/downloads/{task_id}")
async def cancel_download(task_id: str):
    """ダウンロードキャンセル"""
    success = await download_manager.cancel_download(task_id)
    return {"success": success}

@app.get("/api/downloads/{task_id}/status")
async def get_download_status(task_id: str):
    """ダウンロード状態取得"""
    task = download_manager.get_task_status(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/api/schedules")
async def create_schedule(request: ScheduleRequest):
    """スケジュール作成"""
    job = await schedule_manager.add_scheduled_job(
        name=request.name,
        cron_expression=request.cron_expression,
        task_type=request.task_type,
        task_params=request.parameters
    )
    return {"success": True, "job": job}

@app.get("/api/history")
async def get_history(
    skip: int = 0,
    limit: int = 100,
    channel_id: Optional[str] = None
):
    """履歴取得"""
    history = db_manager.get_history(skip, limit, channel_id)
    return history

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket接続"""
    await websocket.accept()
    
    # イベントリスナー登録
    def on_progress(data):
        asyncio.create_task(
            websocket.send_json({"type": "download:progress", **data})
        )
    
    event_bus.on("download:progress", on_progress)
    
    try:
        while True:
            await websocket.receive_text()
    except:
        pass
    finally:
        event_bus.off("download:progress", on_progress)
```

## 5. デプロイメント

### 5.1 Docker構成

```dockerfile
# Dockerfile
FROM python:3.10-slim

# システム依存パッケージ
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Python依存パッケージ
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコピー
COPY . .

# yt-dlp更新
RUN yt-dlp -U

# 起動
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# docker-compose.yml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./downloads:/app/downloads
      - ./data:/app/data
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=sqlite:///data/youtube_downloader.db
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - backend
```

### 5.2 インストーラー作成

```javascript
// electron-builder.json
{
  "productName": "YouTube Downloader",
  "appId": "com.example.youtube-downloader",
  "directories": {
    "output": "dist"
  },
  "files": [
    "build/**/*",
    "node_modules/**/*",
    "package.json"
  ],
  "mac": {
    "category": "public.app-category.utilities",
    "icon": "assets/icon.icns"
  },
  "win": {
    "target": "nsis",
    "icon": "assets/icon.ico"
  },
  "linux": {
    "target": "AppImage",
    "category": "Utility"
  },
  "nsis": {
    "oneClick": false,
    "allowToChangeInstallationDirectory": true
  }
}
```

## 6. テスト戦略

### 6.1 単体テスト

```python
# tests/test_download_manager.py
import pytest
import asyncio
from unittest.mock import Mock, patch
from modules.download_manager import DownloadManager, DownloadTask

@pytest.fixture
def download_manager():
    config = ServiceConfig(max_workers=2)
    return DownloadManager(config)

@pytest.mark.asyncio
async def test_add_download(download_manager):
    """ダウンロード追加テスト"""
    task = await download_manager.add_download(
        url="https://youtube.com/watch?v=test",
        output_path="/tmp/"
    )
    
    assert task.url == "https://youtube.com/watch?v=test"
    assert task.status == DownloadStatus.PENDING
    assert download_manager.queue.qsize() == 1

@pytest.mark.asyncio
async def test_download_with_retry(download_manager):
    """リトライ付きダウンロードテスト"""
    with patch('yt_dlp.YoutubeDL') as mock_ydl:
        # 最初の2回は失敗、3回目で成功
        mock_ydl.return_value.download.side_effect = [
            Exception("Network error"),
            Exception("Network error"),
            None
        ]
        
        task = await download_manager.add_download("test_url")
        await download_manager._execute_download(task)
        
        assert task.status == DownloadStatus.COMPLETED
        assert mock_ydl.return_value.download.call_count == 3
```

### 6.2 統合テスト

```python
# tests/test_integration.py
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_download_flow():
    """ダウンロードフロー統合テスト"""
    # 1. ダウンロード作成
    response = client.post("/api/downloads", json={
        "url": "https://youtube.com/watch?v=test",
        "format": "720p"
    })
    assert response.status_code == 200
    task_id = response.json()["task"]["id"]
    
    # 2. 状態確認
    response = client.get(f"/api/downloads/{task_id}/status")
    assert response.status_code == 200
    assert response.json()["status"] in ["pending", "downloading"]
    
    # 3. 履歴確認
    response = client.get("/api/history")
    assert response.status_code == 200
```

## 7. パフォーマンス最適化

### 7.1 並行処理最適化

```python
# optimization/concurrent_optimizer.py
import asyncio
from typing import List
import aiohttp
from concurrent.futures import ThreadPoolExecutor

class ConcurrentOptimizer:
    """並行処理最適化クラス"""
    
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_metadata_batch(self, urls: List[str]) -> List[Dict]:
        """バッチメタデータ取得"""
        tasks = [self._fetch_with_limit(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _fetch_with_limit(self, url: str) -> Dict:
        """制限付き取得"""
        async with self.semaphore:
            # yt-dlp extract_info を非同期実行
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, 
                self._extract_info_sync,
                url
            )
```

### 7.2 キャッシュ戦略

```python
# optimization/cache_manager.py
import redis
import pickle
from typing import Any, Optional
from functools import wraps

class CacheManager:
    """キャッシュ管理クラス"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url)
        
    def cache(self, ttl: int = 3600):
        """キャッシュデコレータ"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # キャッシュキー生成
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
                
                # キャッシュ確認
                cached = self.redis_client.get(cache_key)
                if cached:
                    return pickle.loads(cached)
                
                # 関数実行
                result = await func(*args, **kwargs)
                
                # キャッシュ保存
                self.redis_client.setex(
                    cache_key, 
                    ttl, 
                    pickle.dumps(result)
                )
                
                return result
            return wrapper
        return decorator
    
    @cache(ttl=86400)  # 24時間キャッシュ
    async def get_channel_info(self, channel_id: str) -> Dict:
        """チャンネル情報取得（キャッシュ付き）"""
        # 実際の取得処理
        pass
```

## 8. 運用・監視

### 8.1 ログ設定

```python
# config/logging_config.py
import logging
import logging.handlers
from pythonjsonlogger import jsonlogger

def setup_logging():
    """ログ設定"""
    # ルートロガー設定
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # JSON形式のフォーマッター
    formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    
    # ファイルハンドラー（ローテーション付き）
    file_handler = logging.handlers.RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger
```

### 8.2 メトリクス収集

```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

# メトリクス定義
download_counter = Counter(
    'downloads_total', 
    'Total number of downloads',
    ['status', 'format']
)

download_duration = Histogram(
    'download_duration_seconds',
    'Download duration in seconds',
    ['format']
)

active_downloads = Gauge(
    'active_downloads',
    'Number of active downloads'
)

queue_size = Gauge(
    'download_queue_size',
    'Size of download queue'
)

def start_metrics_server(port: int = 8001):
    """メトリクスサーバー起動"""
    start_http_server(port)

class MetricsCollector:
    """メトリクス収集クラス"""
    
    @staticmethod
    def record_download(status: str, format: str, duration: float):
        """ダウンロード記録"""
        download_counter.labels(status=status, format=format).inc()
        if status == 'completed':
            download_duration.labels(format=format).observe(duration)
    
    @staticmethod
    def update_active_downloads(count: int):
        """アクティブダウンロード数更新"""
        active_downloads.set(count)
```

## 9. セキュリティ

### 9.1 認証・認可

```python
# security/auth.py
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional

class SecurityManager:
    """セキュリティ管理クラス"""
    
    SECRET_KEY = "your-secret-key-here"
    ALGORITHM = "HS256"
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    @classmethod
    def create_access_token(cls, data: dict, expires_delta: Optional[timedelta] = None):
        """アクセストークン作成"""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(hours=24))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
    
    @classmethod
    def verify_token(cls, token: str) -> Optional[dict]:
        """トークン検証"""
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            return payload
        except JWTError:
            return None
```

## 10. まとめ

この実装案は、段階的な開発アプローチを推奨します：

### Phase 1 (MVP) - 2週間
- 基本的なダウンロード機能
- シンプルなGUI
- ローカルデータベース

### Phase 2 - 1ヶ月
- スケジューリング機能
- 認証システム
- エンコード機能

### Phase 3 - 2ヶ月
- 完全なGUI
- プラグインシステム
- パフォーマンス最適化

### 技術的な推奨事項
1. **非同期処理**を最大限活用
2. **モジュール設計**で保守性確保
3. **テスト駆動開発**で品質保証
4. **段階的リリース**でフィードバック収集

このドキュメントを基に、実際の開発を進めていくことができます。