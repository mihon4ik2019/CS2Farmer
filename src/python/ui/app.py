"""
CS2Farmer Pro - MEGA VERSION
Максимальная производительность + SRT + Полный мониторинг + Расширенный UI
1500+ строк кода | Все функции | Профессиональный дизайн
"""
import customtkinter as ctk
import threading
import os
import sys
import psutil
import subprocess
import random
import json
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import time
from collections import deque
import win32gui
import win32con
import win32process
from ctypes import windll
import math
import csv
from pathlib import Path

from ..database import Database
from ..process_manager import ProcessManager
from ..account_manager import AccountManager
from ..ban_checker import BanChecker
from ..models import AccountStatus, Account
from .. import config

# ============================================================================
# КОНСТАНТЫ И НАСТРОЙКИ
# ============================================================================

VERSION = "3.0.0 MEGA"
BUILD_DATE = "2025"
AUTHOR = "CS2Farmer Team"
MAX_LOG_LINES = 1000
GRAPH_POINTS = 120
REFRESH_RATE_MS = 1000
MAX_PROCESS_HISTORY = 200
MAX_NETWORK_HISTORY = 100

# Цветовая схема
COLORS = {
    'bg_dark': '#0d0d0d',
    'bg_medium': '#1a1a1a',
    'bg_light': '#252525',
    'bg_card': '#2a2a2a',
    'text_primary': '#ffffff',
    'text_secondary': '#888888',
    'text_muted': '#555555',
    'accent_green': '#4CAF50',
    'accent_blue': '#2196F3',
    'accent_orange': '#FF9800',
    'accent_red': '#f44336',
    'accent_cyan': '#4ECDC4',
    'accent_purple': '#9C27B0',
    'accent_yellow': '#FCE38A',
    'accent_pink': '#FF6B6B',
    'success': '#4ECDC4',
    'warning': '#FF9800',
    'error': '#f44336',
    'info': '#4CAF50'
}

# Статусы
STATUS_ICONS = {
    'stopped': '⏸️',
    'starting': '⏳',
    'running': '✅',
    'error': '❌',
    'banned': '🚫',
    'offline': '⚪',
    'online': '🟢',
    'busy': '🟡'
}


# ============================================================================
# УТИЛИТЫ
# ============================================================================

class Utils:
    """Вспомогательные функции"""
    
    @staticmethod
    def format_bytes(bytes_val: int) -> str:
        """Форматирование байтов"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f}{unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f}PB"
    
    @staticmethod
    def format_time(seconds: int) -> str:
        """Форматирование времени"""
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"
    
    @staticmethod
    def format_number(num: float, suffix: str = "") -> str:
        """Форматирование чисел"""
        if num >= 1e9:
            return f"{num/1e9:.1f}B{suffix}"
        elif num >= 1e6:
            return f"{num/1e6:.1f}M{suffix}"
        elif num >= 1e3:
            return f"{num/1e3:.1f}K{suffix}"
        return f"{num:.1f}{suffix}"
    
    @staticmethod
    def get_color_for_value(value: float, thresholds: List[Tuple[float, str]]) -> str:
        """Получить цвет для значения"""
        for threshold, color in reversed(thresholds):
            if value >= threshold:
                return color
        return thresholds[0][1] if thresholds else COLORS['text_primary']
    
    @staticmethod
    def calculate_percentage(current: float, total: float) -> float:
        """Расчёт процента"""
        if total == 0:
            return 0
        return min(100, (current / total) * 100)
    
    @staticmethod
    def generate_id() -> str:
        """Генерация уникального ID"""
        return hashlib.md5(str(time.time()).encode()).hexdigest()[:8]


# ============================================================================
# КЛАССЫ МОНТОРИНГА
# ============================================================================

class ConsoleCapture:
    """Перехват вывода консоли"""
    
    def __init__(self, callback):
        self.callback = callback
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.buffer = ""
        self.lock = threading.Lock()
    
    def write(self, text):
        with self.lock:
            self.buffer += text
            while '\n' in self.buffer:
                line, self.buffer = self.buffer.split('\n', 1)
                if line.strip():
                    self.callback(line)
            self.original_stdout.write(text)
    
    def flush(self):
        self.original_stdout.flush()
    
    def start(self):
        sys.stdout = self
        sys.stderr = self
    
    def stop(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr


class PerformanceMonitor:
    """Мониторинг производительности системы"""
    
    def __init__(self):
        self.cpu_history = deque(maxlen=GRAPH_POINTS)
        self.memory_history = deque(maxlen=GRAPH_POINTS)
        self.network_history = deque(maxlen=MAX_NETWORK_HISTORY)
        self.disk_history = deque(maxlen=GRAPH_POINTS)
        self.process_history: Dict[int, deque] = {}
        self.start_time = datetime.now()
        self.last_net_counters = None
    
    def get_cpu_info(self) -> Dict:
        """Информация о CPU"""
        try:
            return {
                'percent': psutil.cpu_percent(interval=0.2),
                'freq': psutil.cpu_freq().current if psutil.cpu_freq() else 0,
                'cores': psutil.cpu_count(logical=False),
                'threads': psutil.cpu_count(logical=True),
                'per_core': psutil.cpu_percent(percpu=True, interval=0.1)
            }
        except:
            return {'percent': 0, 'freq': 0, 'cores': 0, 'threads': 0, 'per_core': []}
    
    def get_memory_info(self) -> Dict:
        """Информация о памяти"""
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            return {
                'total': mem.total,
                'available': mem.available,
                'used': mem.used,
                'percent': mem.percent,
                'swap_total': swap.total,
                'swap_used': swap.used,
                'swap_percent': swap.percent
            }
        except:
            return {'total': 0, 'available': 0, 'used': 0, 'percent': 0, 'swap_total': 0, 'swap_used': 0, 'swap_percent': 0}
    
    def get_disk_info(self, drive: str = 'C:') -> Dict:
        """Информация о диске"""
        try:
            disk = psutil.disk_usage(drive)
            io = psutil.disk_io_counters()
            return {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent,
                'read_bytes': io.read_bytes if io else 0,
                'write_bytes': io.write_bytes if io else 0,
                'read_count': io.read_count if io else 0,
                'write_count': io.write_count if io else 0
            }
        except:
            return {'total': 0, 'used': 0, 'free': 0, 'percent': 0, 'read_bytes': 0, 'write_bytes': 0, 'read_count': 0, 'write_count': 0}
    
    def get_network_info(self) -> Dict:
        """Информация о сети"""
        try:
            net = psutil.net_io_counters()
            current = {
                'bytes_sent': net.bytes_sent,
                'bytes_recv': net.bytes_recv,
                'packets_sent': net.packets_sent,
                'packets_recv': net.packets_recv
            }
            
            upload = 0
            download = 0
            
            if self.last_net_counters:
                upload = (current['bytes_sent'] - self.last_net_counters['bytes_sent']) // 1024
                download = (current['bytes_recv'] - self.last_net_counters['bytes_recv']) // 1024
            
            self.last_net_counters = current
            
            return {
                **current,
                'upload_kb': upload,
                'download_kb': download,
                'total_kb': upload + download
            }
        except:
            return {'bytes_sent': 0, 'bytes_recv': 0, 'packets_sent': 0, 'packets_recv': 0, 'upload_kb': 0, 'download_kb': 0, 'total_kb': 0}
    
    def track_process(self, pid: int, name: str) -> Optional[Dict]:
        """Отслеживание процесса"""
        if pid not in self.process_history:
            self.process_history[pid] = deque(maxlen=MAX_PROCESS_HISTORY)
        
        try:
            proc = psutil.Process(pid)
            data = {
                'timestamp': time.time(),
                'name': name,
                'cpu': proc.cpu_percent(interval=0.1),
                'memory': proc.memory_info().rss // 1024 // 1024,
                'threads': proc.num_threads(),
                'status': proc.status()
            }
            self.process_history[pid].append(data)
            return data
        except:
            return None
    
    def get_process_stats(self, pid: int) -> Optional[Dict]:
        """Статистика процесса"""
        if pid in self.process_history and self.process_history[pid]:
            return self.process_history[pid][-1]
        return None
    
    def get_uptime(self) -> timedelta:
        """Время работы"""
        return datetime.now() - self.start_time
    
    def update_history(self, cpu: float, memory: float, disk: float, network: Dict):
        """Обновление истории"""
        self.cpu_history.append(cpu)
        self.memory_history.append(memory)
        self.disk_history.append(disk)
        self.network_history.append(network)
    
    def get_history_stats(self) -> Dict:
        """Статистика истории"""
        return {
            'cpu_avg': sum(self.cpu_history) / len(self.cpu_history) if self.cpu_history else 0,
            'cpu_max': max(self.cpu_history) if self.cpu_history else 0,
            'memory_avg': sum(self.memory_history) / len(self.memory_history) if self.memory_history else 0,
            'memory_max': max(self.memory_history) if self.memory_history else 0,
            'network_total': sum(n.get('total_kb', 0) for n in self.network_history)
        }
    
    def clear(self):
        """Очистка"""
        self.cpu_history.clear()
        self.memory_history.clear()
        self.network_history.clear()
        self.disk_history.clear()
        self.process_history.clear()
        self.start_time = datetime.now()
        self.last_net_counters = None


class SystemMonitor:
    """Главный монитор системы"""
    
    def __init__(self, callback):
        self.callback = callback
        self.running = False
        self.cs2_pids: List[int] = []
        self.steam_pids: List[int] = []
        self.perf_monitor = PerformanceMonitor()
        self.history = deque(maxlen=GRAPH_POINTS)
        self.alerts: List[Dict] = []
    
    def start(self):
        self.running = True
        threading.Thread(target=self._monitor_loop, daemon=True).start()
    
    def stop(self):
        self.running = False
    
    def update_cs2_pids(self, pids: List[int]):
        self.cs2_pids = pids
    
    def update_steam_pids(self, pids: List[int]):
        self.steam_pids = pids
    
    def add_alert(self, level: str, message: str):
        """Добавить уведомление"""
        self.alerts.append({
            'timestamp': datetime.now(),
            'level': level,
            'message': message
        })
        if len(self.alerts) > 50:
            self.alerts.pop(0)
    
    def get_alerts(self) -> List[Dict]:
        return self.alerts
    
    def _check_alerts(self, data: Dict):
        """Проверка уведомлений"""
        if data.get('cpu', 0) > 90:
            self.add_alert('warning', f"Высокая загрузка CPU: {data['cpu']:.1f}%")
        if data.get('memory_percent', 0) > 90:
            self.add_alert('warning', f"Высокое использование RAM: {data['memory_percent']:.1f}%")
        if data.get('disk_percent', 0) > 95:
            self.add_alert('error', f"Критическое заполнение диска: {data['disk_percent']:.1f}%")
        for cs2 in data.get('cs2_loads', []):
            if cs2.get('cpu', 0) > 80:
                self.add_alert('info', f"CS2 PID {cs2.get('pid')} использует {cs2['cpu']:.1f}% CPU")
    
    def _monitor_loop(self):
        while self.running:
            try:
                cpu_info = self.perf_monitor.get_cpu_info()
                mem_info = self.perf_monitor.get_memory_info()
                disk_info = self.perf_monitor.get_disk_info()
                net_info = self.perf_monitor.get_network_info()
                
                cs2_loads = []
                total_cs2_cpu = 0
                total_cs2_mem = 0
                
                for pid in self.cs2_pids:
                    try:
                        proc = psutil.Process(pid)
                        cpu = proc.cpu_percent(interval=0.1)
                        mem = proc.memory_info().rss // 1024 // 1024
                        total_cs2_cpu += cpu
                        total_cs2_mem += mem
                        cs2_loads.append({
                            'pid': pid,
                            'cpu': cpu,
                            'memory': mem,
                            'threads': proc.num_threads(),
                            'status': proc.status(),
                            'create_time': proc.create_time()
                        })
                        self.perf_monitor.track_process(pid, f"CS2_{pid}")
                    except:
                        pass
                
                steam_loads = []
                for pid in self.steam_pids:
                    try:
                        proc = psutil.Process(pid)
                        steam_loads.append({
                            'pid': pid,
                            'name': proc.name(),
                            'cpu': proc.cpu_percent(interval=0.1),
                            'memory': proc.memory_info().rss // 1024 // 1024
                        })
                    except:
                        pass
                
                data = {
                    'timestamp': time.time(),
                    'uptime': self.perf_monitor.get_uptime(),
                    'cpu': cpu_info['percent'],
                    'cpu_freq': cpu_info['freq'],
                    'cpu_cores': cpu_info['cores'],
                    'cpu_threads': cpu_info['threads'],
                    'cpu_per_core': cpu_info['per_core'],
                    'memory_percent': mem_info['percent'],
                    'memory_used_gb': mem_info['used'] // 1024 // 1024 // 1024,
                    'memory_total_gb': mem_info['total'] // 1024 // 1024 // 1024,
                    'swap_percent': mem_info['swap_percent'],
                    'disk_percent': disk_info['percent'],
                    'disk_used_gb': disk_info['used'] // 1024 // 1024 // 1024,
                    'disk_total_gb': disk_info['total'] // 1024 // 1024 // 1024,
                    'disk_free_gb': disk_info['free'] // 1024 // 1024 // 1024,
                    'disk_read_mb': disk_info['read_bytes'] // 1024 // 1024,
                    'disk_write_mb': disk_info['write_bytes'] // 1024 // 1024,
                    'net_upload_kb': net_info['upload_kb'],
                    'net_download_kb': net_info['download_kb'],
                    'net_total_kb': net_info['total_kb'],
                    'cs2_count': len(cs2_loads),
                    'cs2_loads': cs2_loads,
                    'cs2_total_cpu': total_cs2_cpu,
                    'cs2_total_mem': total_cs2_mem,
                    'steam_count': len(steam_loads),
                    'steam_loads': steam_loads,
                    'total_processes': psutil.cpu_count(logical=True),
                    'history_stats': self.perf_monitor.get_history_stats()
                }
                
                self.perf_monitor.update_history(
                    data['cpu'],
                    data['memory_percent'],
                    data['disk_percent'],
                    net_info
                )
                
                self._check_alerts(data)
                self.history.append(data)
                self.callback(data)
            except Exception as e:
                pass
            
            time.sleep(REFRESH_RATE_MS / 1000)
    
    def get_history(self) -> List[Dict]:
        return list(self.history)
    
    def export_stats(self, filepath: str) -> bool:
        """Экспорт статистики в CSV"""
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Timestamp', 'CPU%', 'RAM%', 'Disk%', 'Net Upload', 'Net Download', 'CS2 Count'])
                for entry in self.history:
                    writer.writerow([
                        entry.get('timestamp', 0),
                        entry.get('cpu', 0),
                        entry.get('memory_percent', 0),
                        entry.get('disk_percent', 0),
                        entry.get('net_upload_kb', 0),
                        entry.get('net_download_kb', 0),
                        entry.get('cs2_count', 0)
                    ])
            return True
        except:
            return False


# ============================================================================
# SRT (STEAM ROOT TOOL)
# ============================================================================

class SteamRootTool:
    """Steam Root Tool - Управление Steam"""
    
    def __init__(self):
        self.steam_paths = [
            r"C:\Program Files (x86)\Steam",
            r"C:\Program Files\Steam",
            os.path.expandvars(r"%ProgramFiles(x86)%\Steam"),
        ]
        self.steam_dir = None
        self.config_dir = None
        self._find_steam()
    
    def _find_steam(self) -> bool:
        for path in self.steam_paths:
            if os.path.exists(path):
                self.steam_dir = path
                self.config_dir = os.path.join(path, 'config')
                return True
        return False
    
    def get_steam_version(self) -> str:
        try:
            exe_path = os.path.join(self.steam_dir, 'steam.exe')
            if os.path.exists(exe_path):
                from win32api import GetFileVersionInfo, HIWORD, LOWORD
                info = GetFileVersionInfo(exe_path, '\\')
                return f"{HIWORD(info['FileVersionMS'])}.{LOWORD(info['FileVersionMS'])}.{HIWORD(info['FileVersionLS'])}"
        except:
            pass
        return "Unknown"
    
    def get_steam_users(self) -> List[Dict]:
        users = []
        loginusers_path = os.path.join(self.config_dir, 'loginusers.vdf') if self.config_dir else None
        
        if loginusers_path and os.path.exists(loginusers_path):
            try:
                with open(loginusers_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                import re
                steamids = re.findall(r'"(\d+)"\s*\{', content)
                
                for steamid in steamids:
                    username_match = re.search(rf'{steamid}.*?"PersonaName"\s*"([^"]+)"', content, re.DOTALL)
                    username = username_match.group(1) if username_match else f"User_{steamid}"
                    
                    users.append({
                        'steamid': steamid,
                        'username': username,
                        'path': os.path.join(self.config_dir, 'users', steamid) if self.config_dir else ''
                    })
            except:
                pass
        
        return users
    
    def clear_steam_cache(self) -> int:
        cleared = 0
        cache_paths = [
            os.path.join(self.steam_dir, 'appcache') if self.steam_dir else '',
            os.path.join(self.steam_dir, 'config', 'htmlcache') if self.steam_dir else '',
            os.path.join(self.steam_dir, 'steamapps', 'shadercache') if self.steam_dir else '',
            os.path.join(os.getenv('APPDATA'), 'Steam', 'htmlcache'),
            os.path.join(os.getenv('LOCALAPPDATA'), 'Steam', 'htmlcache'),
        ]
        
        for path in cache_paths:
            if path and os.path.exists(path):
                try:
                    import shutil
                    shutil.rmtree(path, ignore_errors=True)
                    cleared += 1
                except:
                    pass
        
        return cleared
    
    def restart_steam(self) -> bool:
        try:
            subprocess.run(['taskkill', '/f', '/im', 'steam.exe'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            time.sleep(3)
            
            steam_exe = os.path.join(self.steam_dir, 'steam.exe') if self.steam_dir else 'steam.exe'
            if os.path.exists(steam_exe):
                subprocess.Popen([steam_exe], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                return True
        except:
            pass
        
        return False
    
    def kill_steam_processes(self) -> int:
        killed = 0
        processes = ['steam.exe', 'steamwebhelper.exe', 'steamservice.exe']
        
        for proc_name in processes:
            try:
                result = subprocess.run(['taskkill', '/f', '/im', proc_name], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode == 0:
                    killed += 1
            except:
                pass
        
        return killed
    
    def verify_steam_files(self) -> Dict:
        result = {'valid': True, 'missing': [], 'corrupted': []}
        
        if not self.steam_dir:
            result['valid'] = False
            return result
        
        required = ['steam.exe', 'steamclient.dll', 'bin/SteamService.exe']
        
        for file in required:
            path = os.path.join(self.steam_dir, file)
            if not os.path.exists(path):
                result['valid'] = False
                result['missing'].append(file)
        
        return result
    
    def get_steam_processes(self) -> List[Dict]:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
            try:
                if proc.info['name'] and 'steam' in proc.info['name'].lower():
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu': proc.cpu_percent(interval=0.1),
                        'memory': proc.info['memory_info'].rss // 1024 // 1024 if proc.info['memory_info'] else 0
                    })
            except:
                pass
        
        return processes


# ============================================================================
# UI КОМПОНЕНТЫ
# ============================================================================

class AdvancedGraph(ctk.CTkCanvas):
    """Продвинутый график с несколькими линиями"""
    
    def __init__(self, parent, title: str, icon: str, colors: List[str], 
                 width: int = 200, height: int = 100, show_grid: bool = True):
        super().__init__(parent, width=width, height=height, bg="#1a1a1a", highlightthickness=0)
        
        self.title = title
        self.icon = icon
        self.colors = colors
        self.data_series: List[deque] = [deque(maxlen=GRAPH_POINTS) for _ in colors]
        self.show_grid = show_grid
        
        # Заголовок
        self.create_text(10, 10, text=f"{icon} {title}", fill="#aaaaaa", anchor="nw", font=("Segoe UI", 11, "bold"))
        
        # Значения
        self.value_labels = []
        for i, color in enumerate(colors):
            y = 10 + i * 18
            lbl = self.create_text(width - 10, y, text="0%", fill=color, anchor="ne", font=("Segoe UI", 10, "bold"))
            self.value_labels.append(lbl)
        
        # Сетка
        if show_grid:
            for i in range(5):
                y = 35 + i * ((height - 40) // 4)
                self.create_line(15, y, width - 5, y, fill="#2a2a2a", width=1)
                self.create_text(12, y, text=f"{100 - i*20}", fill="#555555", font=("Segoe UI", 7), anchor="e")
    
    def update_data(self, values: List[float], suffixes: List[str] = None):
        if suffixes is None:
            suffixes = ["%"] * len(values)
        
        for i, value in enumerate(values):
            if i < len(self.data_series):
                self.data_series[i].append(value)
                self.itemconfig(self.value_labels[i], text=f"{value:.1f}{suffixes[i]}")
        
        self.draw_graphs()
    
    def draw_graphs(self):
        self.delete("graph")
        
        for series_idx, data in enumerate(self.data_series):
            if len(data) < 2:
                continue
            
            width = (self.winfo_width() - 20) / GRAPH_POINTS
            points = []
            
            for i, value in enumerate(data):
                x = 20 + i * width
                y = self.winfo_height() - 25 - (min(value, 100) / 100 * (self.winfo_height() - 40))
                points.extend([x, y])
            
            if points:
                self.create_line(points, fill=self.colors[series_idx], width=2, tags="graph", smooth=True)
                
                # Заполнение
                fill_points = [20, self.winfo_height() - 25] + points + [20 + len(data) * width, self.winfo_height() - 25]
                self.create_polygon(fill_points, fill=self.colors[series_idx], outline="", tags="graph", stipple='gray50')
    
    def clear(self):
        for series in self.data_series:
            series.clear()
        self.delete("graph")


class DonutChart(ctk.CTkCanvas):
    """Круговая диаграмма"""
    
    def __init__(self, parent, size: int = 120):
        super().__init__(parent, width=size, height=size, bg="#1a1a1a", highlightthickness=0)
        self.size = size
        self.center = size // 2
        self.radius = size // 2 - 10
        self.segments = []
        self.center_text = self.create_text(self.center, self.center, text="0%", fill="#ffffff", anchor="center", font=("Segoe UI", 16, "bold"))
    
    def update(self, values: List[float], colors: List[str], labels: List[str] = None):
        self.delete("segment")
        total = sum(values)
        
        if total == 0:
            return
        
        start_angle = 0
        self.segments = []
        
        for i, value in enumerate(values):
            angle = (value / total) * 360
            color = colors[i % len(colors)]
            
            start_rad = math.radians(start_angle)
            end_rad = math.radians(start_angle + angle)
            
            x1 = self.center + self.radius * math.cos(start_rad)
            y1 = self.center + self.radius * math.sin(start_rad)
            x2 = self.center + self.radius * math.cos(end_rad)
            y2 = self.center + self.radius * math.sin(end_rad)
            
            self.create_arc(
                self.center - self.radius, self.center - self.radius,
                self.center + self.radius, self.center + self.radius,
                start=start_angle, extent=angle, fill=color, tags="segment", style=tk.ARC, width=20
            )
            
            start_angle += angle
        
        self.itemconfig(self.center_text, text=f"{values[0]:.1f}%" if values else "0%")


class StatCard(ctk.CTkFrame):
    """Карточка статистики"""
    
    def __init__(self, parent, title: str, icon: str, value: str = "0", 
                 color: str = COLORS['accent_blue'], height: int = 70):
        super().__init__(parent, fg_color=COLORS['bg_light'], corner_radius=8)
        
        self.configure(height=height)
        
        # Иконка
        icon_lbl = ctk.CTkLabel(self, text=icon, font=ctk.CTkFont(size=20), text_color=color)
        icon_lbl.place(relx=0.15, rely=0.5, anchor="center")
        
        # Заголовок
        title_lbl = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=9), text_color=COLORS['text_secondary'])
        title_lbl.place(relx=0.4, rely=0.35, anchor="w")
        
        # Значение
        self.value_lbl = ctk.CTkLabel(self, text=value, font=ctk.CTkFont(size=16, weight="bold"), text_color=COLORS['text_primary'])
        self.value_lbl.place(relx=0.4, rely=0.65, anchor="w")
        
        # Индикатор
        self.indicator = ctk.CTkLabel(self, text="●", font=ctk.CTkFont(size=10), text_color=color)
        self.indicator.place(relx=0.95, rely=0.5, anchor="e")
    
    def update_value(self, value: str, color: str = None):
        self.value_lbl.configure(text=value)
        if color:
            self.indicator.configure(text_color=color)


class ProcessTable(ctk.CTkFrame):
    """Таблица процессов"""
    
    def __init__(self, parent, height: int = 150):
        super().__init__(parent, fg_color=COLORS['bg_medium'], corner_radius=8)
        
        # Заголовок
        header = ctk.CTkFrame(self, fg_color=COLORS['bg_card'], height=30, corner_radius=6)
        header.pack(fill="x", padx=8, pady=(8, 0))
        
        ctk.CTkLabel(header, text="PID", width=50, font=ctk.CTkFont(weight="bold", size=9), text_color=COLORS['text_primary']).pack(side="left", padx=4)
        ctk.CTkLabel(header, text="Процесс", width=100, font=ctk.CTkFont(weight="bold", size=9), text_color=COLORS['text_primary']).pack(side="left", padx=4)
        ctk.CTkLabel(header, text="CPU", width=50, font=ctk.CTkFont(weight="bold", size=9), text_color=COLORS['text_primary']).pack(side="left", padx=4)
        ctk.CTkLabel(header, text="RAM", width=60, font=ctk.CTkFont(weight="bold", size=9), text_color=COLORS['text_primary']).pack(side="left", padx=4)
        ctk.CTkLabel(header, text="Потоки", width=50, font=ctk.CTkFont(weight="bold", size=9), text_color=COLORS['text_primary']).pack(side="left", padx=4)
        
        # Таблица
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=8, pady=8)
        
        self.rows: Dict[int, ctk.CTkFrame] = {}
    
    def update_processes(self, processes: List[Dict]):
        # Очистка старых
        for pid in list(self.rows.keys()):
            if not any(p.get('pid') == pid for p in processes):
                self.rows[pid].destroy()
                del self.rows[pid]
        
        # Обновление/создание
        for proc in processes:
            pid = proc.get('pid', 0)
            
            if pid not in self.rows:
                row = ctk.CTkFrame(self.scroll, fg_color=COLORS['bg_light'], height=28, corner_radius=4)
                row.pack(fill="x", pady=2)
                
                ctk.CTkLabel(row, text=str(pid), width=50, font=ctk.CTkFont(size=8), text_color=COLORS['text_secondary']).pack(side="left", padx=4)
                ctk.CTkLabel(row, text=proc.get('name', 'Unknown')[:15], width=100, anchor="w", font=ctk.CTkFont(size=9, weight="bold"), text_color=COLORS['text_primary']).pack(side="left", padx=4)
                
                cpu_lbl = ctk.CTkLabel(row, text="0%", width=50, font=ctk.CTkFont(size=8), text_color=COLORS['accent_pink'])
                cpu_lbl.pack(side="left", padx=4)
                
                ram_lbl = ctk.CTkLabel(row, text="0MB", width=60, font=ctk.CTkFont(size=8), text_color=COLORS['accent_cyan'])
                ram_lbl.pack(side="left", padx=4)
                
                thr_lbl = ctk.CTkLabel(row, text="0", width=50, font=ctk.CTkFont(size=8), text_color=COLORS['accent_purple'])
                thr_lbl.pack(side="left", padx=4)
                
                self.rows[pid] = {'frame': row, 'cpu': cpu_lbl, 'ram': ram_lbl, 'thr': thr_lbl}
            
            # Обновление
            if pid in self.rows:
                self.rows[pid]['cpu'].configure(text=f"{proc.get('cpu', 0):.1f}%", text_color=COLORS['accent_pink'] if proc.get('cpu', 0) > 50 else COLORS['accent_green'])
                self.rows[pid]['ram'].configure(text=f"{proc.get('memory', 0)}MB")
                self.rows[pid]['thr'].configure(text=f"{proc.get('threads', 0)}")
    
    def clear(self):
        for row in self.rows.values():
            row['frame'].destroy()
        self.rows.clear()


class CS2Card(ctk.CTkFrame):
    """Карточка CS2 процесса"""
    
    def __init__(self, parent, username: str, index: int, apply_bes_callback):
        super().__init__(parent, fg_color=COLORS['bg_light'], corner_radius=10)
        
        self.account_id = index
        self.username = username
        self.apply_bes_callback = apply_bes_callback
        
        # Заголовок
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=8)
        
        ctk.CTkLabel(header, text=f"🎮 #{index + 1}", width=50, font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS['text_primary']).pack(side="left")
        ctk.CTkLabel(header, text=username[:20], width=140, anchor="w", font=ctk.CTkFont(size=10), text_color=COLORS['text_secondary']).pack(side="left", padx=8)
        
        self.status = ctk.CTkLabel(header, text="⚪", font=ctk.CTkFont(size=14))
        self.status.pack(side="right")
        
        # Статистика
        stats = ctk.CTkFrame(self, fg_color=COLORS['bg_medium'], corner_radius=8)
        stats.pack(fill="x", padx=12, pady=6)
        
        stats_grid = ctk.CTkFrame(stats, fg_color="transparent")
        stats_grid.pack(fill="x", padx=8, pady=6)
        stats_grid.grid_columnconfigure(0, weight=1)
        stats_grid.grid_columnconfigure(1, weight=1)
        stats_grid.grid_columnconfigure(2, weight=1)
        stats_grid.grid_columnconfigure(3, weight=1)
        
        self.cpu = ctk.CTkLabel(stats_grid, text="0%", font=ctk.CTkFont(size=9), text_color=COLORS['accent_pink'])
        self.cpu.grid(row=0, column=0, padx=3)
        
        self.ram = ctk.CTkLabel(stats_grid, text="0MB", font=ctk.CTkFont(size=9), text_color=COLORS['accent_cyan'])
        self.ram.grid(row=0, column=1, padx=3)
        
        self.thr = ctk.CTkLabel(stats_grid, text="0", font=ctk.CTkFont(size=9), text_color=COLORS['accent_purple'])
        self.thr.grid(row=0, column=2, padx=3)
        
        self.fps = ctk.CTkLabel(stats_grid, text="30 FPS", font=ctk.CTkFont(size=9), text_color=COLORS['accent_yellow'])
        self.fps.grid(row=0, column=3, padx=3)
        
        # BES + График
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=12, pady=(0, 8))
        
        self.bes_btn = ctk.CTkButton(bottom, text="🔧 BES", width=60, height=26, font=ctk.CTkFont(size=9, weight="bold"), fg_color=COLORS['accent_orange'], hover_color="#F57C00", corner_radius=4, command=self._on_bes)
        self.bes_btn.pack(side="left")
        
        self.bes_status = ctk.CTkLabel(bottom, text="⚪", font=ctk.CTkFont(size=11))
        self.bes_status.pack(side="left", padx=6)
        
        self.graph = AdvancedGraph(bottom, "", "", [COLORS['accent_pink']], width=120, height=26, show_grid=False)
        self.graph.pack(side="right")
    
    def _on_bes(self):
        if self.apply_bes_callback:
            self.apply_bes_callback(self.account_id)
    
    def update(self, cpu: float, mem: int, thr: int, bes: bool = False):
        self.cpu.configure(text=f"{cpu:.1f}%", text_color=COLORS['accent_pink'] if cpu > 50 else COLORS['accent_green'])
        self.ram.configure(text=f"{mem}MB")
        self.thr.configure(text=f"{thr}")
        
        if bes:
            self.bes_status.configure(text="🟢", text_color=COLORS['accent_green'])
            self.bes_btn.configure(state="disabled", text="BES ✓", fg_color=COLORS['accent_green'])
            self.status.configure(text="🟢")
        else:
            self.bes_status.configure(text="⚪", text_color=COLORS['text_secondary'])
            self.bes_btn.configure(state="normal", text="🔧 BES", fg_color=COLORS['accent_orange'])
            self.status.configure(text="🟡")
        
        self.graph.update_data([cpu])
    
    def set_inactive(self):
        self.cpu.configure(text="-", text_color=COLORS['text_muted'])
        self.ram.configure(text="-", text_color=COLORS['text_muted'])
        self.thr.configure(text="-", text_color=COLORS['text_muted'])
        self.status.configure(text="⚪")
        self.bes_btn.configure(state="disabled", fg_color=COLORS['text_muted'])


class SRTFrame(ctk.CTkFrame):
    """SRT Панель"""
    
    def __init__(self, parent, log_callback):
        super().__init__(parent, fg_color=COLORS['bg_medium'], corner_radius=10)
        
        self.log_callback = log_callback
        self.srt = SteamRootTool()
        
        # Заголовок
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=10)
        
        ctk.CTkLabel(header, text="🔧 SRT", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS['text_primary']).pack(side="left")
        
        version = self.srt.get_steam_version()
        ctk.CTkLabel(header, text=f"v{version}", font=ctk.CTkFont(size=9), text_color=COLORS['text_secondary']).pack(side="right")
        
        # Статус
        status = ctk.CTkFrame(self, fg_color=COLORS['bg_light'], corner_radius=6)
        status.pack(fill="x", padx=12, pady=4)
        
        self.status_lbl = ctk.CTkLabel(status, text="🟢 Steam найден" if self.srt.steam_dir else "🔴 Не найден", font=ctk.CTkFont(size=10), text_color=COLORS['accent_green'] if self.srt.steam_dir else COLORS['accent_red'])
        self.status_lbl.pack(side="left", padx=8, pady=6)
        
        # Кнопки
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=12, pady=4)
        
        ctk.CTkButton(btns, text="🔄 Restart", width=70, height=30, fg_color=COLORS['accent_blue'], font=ctk.CTkFont(size=9, weight="bold"), command=self._restart).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="🗑️ Cache", width=70, height=30, fg_color=COLORS['accent_orange'], font=ctk.CTkFont(size=9, weight="bold"), command=self._clear).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="💀 Kill", width=70, height=30, fg_color=COLORS['accent_red'], font=ctk.CTkFont(size=9, weight="bold"), command=self._kill).pack(side="left", padx=2)
        
        # Пользователи
        users_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_light'], corner_radius=6)
        users_frame.pack(fill="both", expand=True, padx=12, pady=8)
        
        ctk.CTkLabel(users_frame, text="👥 Пользователи", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS['text_primary']).pack(fill="x", padx=8, pady=6)
        
        self.users_scroll = ctk.CTkScrollableFrame(users_frame, fg_color="transparent", height=100)
        self.users_scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        
        self._load_users()
    
    def _load_users(self):
        for w in self.users_scroll.winfo_children():
            w.destroy()
        
        users = self.srt.get_steam_users()
        if users:
            for user in users:
                row = ctk.CTkFrame(self.users_scroll, fg_color=COLORS['bg_medium'], corner_radius=4, height=26)
                row.pack(fill="x", pady=2)
                
                ctk.CTkLabel(row, text=f"👤 {user['username'][:18]}", font=ctk.CTkFont(size=9), text_color=COLORS['text_primary']).pack(side="left", padx=6)
                ctk.CTkLabel(row, text=f"ID:{user['steamid'][-6:]}", font=ctk.CTkFont(size=8), text_color=COLORS['text_secondary']).pack(side="right", padx=6)
        else:
            ctk.CTkLabel(self.users_scroll, text="Нет пользователей", font=ctk.CTkFont(size=9), text_color=COLORS['text_secondary']).pack(pady=8)
    
    def _restart(self):
        threading.Thread(target=self._restart_thread, daemon=True).start()
    
    def _restart_thread(self):
        self.log_callback("🔄 Перезапуск Steam...", "info")
        if self.srt.restart_steam():
            self.log_callback("✅ Steam перезапущен", "success")
        else:
            self.log_callback("❌ Ошибка перезапуска", "error")
        self.after(0, self._load_users)
    
    def _clear(self):
        threading.Thread(target=self._clear_thread, daemon=True).start()
    
    def _clear_thread(self):
        self.log_callback("🗑️ Очистка кэша...", "info")
        count = self.srt.clear_steam_cache()
        self.log_callback(f"✅ Очищено {count} кэшей", "success")
    
    def _kill(self):
        threading.Thread(target=self._kill_thread, daemon=True).start()
    
    def _kill_thread(self):
        self.log_callback("💀 Завершение процессов...", "warning")
        count = self.srt.kill_steam_processes()
        self.log_callback(f"✅ Завершено {count} процессов", "success")


class LogPanel(ctk.CTkFrame):
    """Панель логов с фильтрами"""
    
    LEVELS = ['Все', 'Info', 'Warning', 'Error', 'Success']
    COLORS_MAP = {
        'info': COLORS['info'],
        'warning': COLORS['warning'],
        'error': COLORS['error'],
        'success': COLORS['success']
    }
    
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS['bg_medium'], corner_radius=10)
        
        # Заголовок
        header = ctk.CTkFrame(self, fg_color="transparent", height=38)
        header.pack(fill="x", pady=(10, 0))
        
        ctk.CTkLabel(header, text="📋 Логи событий", font=ctk.CTkFont(weight="bold", size=13), text_color=COLORS['text_primary']).pack(side="left", padx=12)
        
        # Фильтр
        self.filter_var = ctk.StringVar(value="Все")
        filter_menu = ctk.CTkOptionMenu(header, values=self.LEVELS, variable=self.filter_var, width=90, height=28, font=ctk.CTkFont(size=9), command=self._apply_filter)
        filter_menu.pack(side="right", padx=12)
        
        ctk.CTkButton(header, text="🗑️", width=35, height=28, fg_color=COLORS['bg_card'], hover_color=COLORS['bg_light'], font=ctk.CTkFont(size=10), command=self.clear).pack(side="right", padx=4)
        
        ctk.CTkButton(header, text="💾", width=35, height=28, fg_color=COLORS['bg_card'], hover_color=COLORS['bg_light'], font=ctk.CTkFont(size=10), command=self._export).pack(side="right", padx=4)
        
        # Текст
        self.log_text = ctk.CTkTextbox(self, font=ctk.CTkFont(size=9, family="Consolas"), wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=12, pady=12)
        
        # Цвета
        for level, color in self.COLORS_MAP.items():
            self.log_text.tag_config(level, foreground=color)
        
        # Статистика
        self.stats = ctk.CTkFrame(self, fg_color=COLORS['bg_light'], corner_radius=6)
        self.stats.pack(fill="x", padx=12, pady=(0, 10))
        
        self.stats_lbl = ctk.CTkLabel(self.stats, text="📊 0 записей", font=ctk.CTkFont(size=9), text_color=COLORS['text_secondary'])
        self.stats_lbl.pack(side="left", padx=8, pady=6)
        
        self.log_count = 0
    
    def log(self, msg: str, level: str = "info"):
        if self.filter_var.get() != "Все" and level.capitalize() != self.filter_var.get():
            return
        
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {msg}\n", level)
        self.log_text.see("end")
        
        self.log_count += 1
        self.stats_lbl.configure(text=f"📊 {self.log_count} записей")
        
        # Ограничение
        lines = int(self.log_text.index('end-1c').split('.')[0])
        if lines > MAX_LOG_LINES:
            self.log_text.delete("1.0", f"{lines - MAX_LOG_LINES}.0")
    
    def _apply_filter(self, _):
        self.log_count = 0
        self.stats_lbl.configure(text="📊 Фильтрация...")
    
    def _export(self):
        try:
            filepath = os.path.join(config.DATA_DIR, f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get("1.0", "end"))
            print(f"Логи экспортированы: {filepath}")
        except Exception as e:
            print(f"Ошибка экспорта: {e}")
    
    def clear(self):
        self.log_text.delete("1.0", "end")
        self.log_count = 0
        self.stats_lbl.configure(text="📊 0 записей")


# ============================================================================
# ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ============================================================================

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title(f"🎮 CS2Farmer Pro v{VERSION}")
        self.geometry("1920x1080")
        self.minsize(1600, 900)
        
        # Сетка
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.db = Database(config.DB_PATH, "cs2farmer")
        self.pm = ProcessManager()
        
        try:
            self.ban_checker = BanChecker(api_key="")
        except:
            self.ban_checker = self._create_dummy_ban_checker()
        
        self.am = AccountManager(self.db, self.pm, self.ban_checker)
        
        # Переменные
        self.selected_accounts: Dict[int, bool] = {}
        self.is_running = False
        self.cs2_cards: Dict[int, CS2Card] = {}
        self.stat_labels: Dict[int, ctk.CTkLabel] = {}
        
        self.console_capture = ConsoleCapture(self._log)
        self.console_capture.start()
        
        self.system_monitor = SystemMonitor(self._update_dashboard)
        self.system_monitor.start()
        
        self._create_ui()
        self._auto_import_accounts()
        self._load_accounts()
        self._refresh_loop()
    
    def _create_dummy_ban_checker(self):
        class DummyBanChecker:
            def check_account(self, steam_id: str) -> bool:
                return False
        return DummyBanChecker()
    
    def _create_ui(self):
        # === КОЛОНКА 1: АККАУНТЫ ===
        acc_panel = ctk.CTkFrame(self, fg_color=COLORS['bg_dark'], corner_radius=0)
        acc_panel.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 3))
        
        # Заголовок
        header = ctk.CTkFrame(acc_panel, fg_color=COLORS['bg_medium'], corner_radius=10)
        header.pack(fill="x", padx=12, pady=12)
        
        title_row = ctk.CTkFrame(header, fg_color="transparent")
        title_row.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(title_row, text="🎮 CS2Farmer Pro", font=ctk.CTkFont(size=22, weight="bold"), text_color=COLORS['text_primary']).pack(side="left")
        ctk.CTkLabel(title_row, text=f"v{VERSION}", font=ctk.CTkFont(size=9), text_color=COLORS['text_secondary']).pack(side="left", padx=10, pady=25)
        
        # Статус
        status = ctk.CTkFrame(header, fg_color=COLORS['bg_light'], corner_radius=6)
        status.pack(fill="x", padx=15, pady=10)
        
        self.status_dot = ctk.CTkLabel(status, text="●", font=ctk.CTkFont(size=16), text_color=COLORS['accent_green'])
        self.status_dot.pack(side="left", padx=12, pady=8)
        
        self.status_text = ctk.CTkLabel(status, text="Готов к запуску", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLORS['accent_green'])
        self.status_text.pack(side="left", padx=8, pady=8)
        
        # Кнопки
        btns = ctk.CTkFrame(header, fg_color="transparent")
        btns.pack(fill="x", padx=15, pady=8)
        
        self.start_btn = ctk.CTkButton(btns, text="▶️ Запустить", width=120, height=42, fg_color=COLORS['accent_green'], hover_color="#45a049", font=ctk.CTkFont(size=12, weight="bold"), corner_radius=6, command=self._start_selected)
        self.start_btn.pack(side="left", padx=(0, 6))
        
        self.stop_btn = ctk.CTkButton(btns, text="⏹️ Стоп", width=80, height=42, fg_color=COLORS['accent_red'], hover_color="#da190b", font=ctk.CTkFont(size=12, weight="bold"), corner_radius=6, command=self._stop_all)
        self.stop_btn.pack(side="left", padx=(0, 6))
        
        ctk.CTkButton(btns, text="🔄", width=40, height=42, fg_color=COLORS['accent_blue'], hover_color="#1976D2", font=ctk.CTkFont(size=12), corner_radius=6, command=self._load_accounts).pack(side="left", padx=(0, 6))
        ctk.CTkButton(btns, text="☑️", width=40, height=42, fg_color=COLORS['bg_card'], hover_color=COLORS['bg_light'], font=ctk.CTkFont(size=12), corner_radius=6, command=self._select_all).pack(side="left")
        
        # Список
        acc_list = ctk.CTkFrame(acc_panel, fg_color=COLORS['bg_medium'], corner_radius=10)
        acc_list.pack(fill="both", expand=True, padx=12, pady=8)
        
        hdr = ctk.CTkFrame(acc_list, fg_color=COLORS['bg_card'], height=32, corner_radius=6)
        hdr.pack(fill="x", padx=8, pady=(8, 0))
        
        ctk.CTkLabel(hdr, text="✓", width=28, font=ctk.CTkFont(weight="bold", size=10), text_color=COLORS['text_primary']).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Аккаунт", width=120, font=ctk.CTkFont(weight="bold", size=10), text_color=COLORS['text_primary']).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Статус", width=40, font=ctk.CTkFont(weight="bold", size=10), text_color=COLORS['text_primary']).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="maFile", width=35, font=ctk.CTkFont(weight="bold", size=10), text_color=COLORS['text_primary']).pack(side="left", padx=4)
        ctk.CTkLabel(hdr, text="Время", width=65, font=ctk.CTkFont(weight="bold", size=10), text_color=COLORS['text_primary']).pack(side="left", padx=4)
        
        self.accounts_frame = ctk.CTkScrollableFrame(acc_list, fg_color="transparent")
        self.accounts_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        # === КОЛОНКА 2: ДАШБОРД ===
        dash_top = ctk.CTkFrame(self, fg_color=COLORS['bg_dark'], corner_radius=0)
        dash_top.grid(row=0, column=1, sticky="nsew", padx=(3, 3), pady=(0, 3))
        
        # Графики
        graphs = ctk.CTkFrame(dash_top, fg_color=COLORS['bg_medium'], corner_radius=10)
        graphs.pack(fill="both", expand=True, padx=12, pady=12)
        
        ctk.CTkLabel(graphs, text="📈 Мониторинг системы", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS['text_primary']).pack(fill="x", padx=12, pady=10)
        
        graphs_grid = ctk.CTkFrame(graphs, fg_color="transparent")
        graphs_grid.pack(fill="both", expand=True, padx=12, pady=6)
        graphs_grid.grid_columnconfigure(0, weight=1)
        graphs_grid.grid_columnconfigure(1, weight=1)
        
        self.cpu_graph = AdvancedGraph(graphs_grid, "CPU Load", "🖥️", [COLORS['accent_pink'], COLORS['accent_red']], width=250, height=110)
        self.cpu_graph.grid(row=0, column=0, padx=6, pady=6)
        
        self.ram_graph = AdvancedGraph(graphs_grid, "Memory", "💾", [COLORS['accent_cyan'], COLORS['accent_blue']], width=250, height=110)
        self.ram_graph.grid(row=0, column=1, padx=6, pady=6)
        
        # Статистика
        stats = ctk.CTkFrame(dash_top, fg_color=COLORS['bg_medium'], corner_radius=10)
        stats.pack(fill="x", padx=12, pady=(0, 10))
        
        stats_grid = ctk.CTkFrame(stats, fg_color="transparent")
        stats_grid.pack(fill="x", padx=12, pady=10)
        stats_grid.grid_columnconfigure(0, weight=1)
        stats_grid.grid_columnconfigure(1, weight=1)
        stats_grid.grid_columnconfigure(2, weight=1)
        stats_grid.grid_columnconfigure(3, weight=1)
        stats_grid.grid_columnconfigure(4, weight=1)
        
        self._create_stat_card(stats_grid, "CPU", "🖥️", "0%", 0, 0)
        self._create_stat_card(stats_grid, "RAM", "💾", "0GB", 0, 1)
        self._create_stat_card(stats_grid, "CS2", "🎮", "0", 0, 2)
        self._create_stat_card(stats_grid, "Сеть", "🌐", "0KB", 0, 3)
        self._create_stat_card(stats_grid, "Время", "⏱️", "00:00", 0, 4)
        
        # CS2
        cs2_panel = ctk.CTkFrame(self, fg_color=COLORS['bg_dark'], corner_radius=0)
        cs2_panel.grid(row=1, column=1, sticky="nsew", padx=(3, 3), pady=(3, 0))
        
        cs2_frame = ctk.CTkFrame(cs2_panel, fg_color=COLORS['bg_medium'], corner_radius=10)
        cs2_frame.pack(fill="both", expand=True, padx=12, pady=12)
        
        cs2_hdr = ctk.CTkFrame(cs2_frame, fg_color="transparent")
        cs2_hdr.pack(fill="x", padx=12, pady=10)
        
        ctk.CTkLabel(cs2_hdr, text="🎮 Активные CS2 процессы", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLORS['text_primary']).pack(side="left")
        self.cs2_count = ctk.CTkLabel(cs2_hdr, text="0/4", font=ctk.CTkFont(size=12), text_color=COLORS['text_secondary'])
        self.cs2_count.pack(side="right")
        
        self.cs2_frame = ctk.CTkScrollableFrame(cs2_frame, fg_color="transparent")
        self.cs2_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        
        # === КОЛОНКА 3: SRT + ЛОГИ ===
        right = ctk.CTkFrame(self, fg_color=COLORS['bg_dark'], corner_radius=0)
        right.grid(row=0, column=2, rowspan=2, sticky="nsew", padx=(3, 0))
        
        self.srt = SRTFrame(right, self._log)
        self.srt.pack(fill="x", padx=12, pady=12)
        
        self.log_panel = LogPanel(right)
        self.log_panel.pack(fill="both", expand=True, padx=12, pady=12)
        
        self._log("🎉 CS2Farmer Pro запущен!", "success")
        self._log(f"⚡ Версия: {VERSION}", "info")
        self._log(f"📅 Дата сборки: {BUILD_DATE}", "info")
    
    def _create_stat_card(self, parent, title: str, icon: str, value: str, row: int, col: int):
        card = StatCard(parent, title, icon, value, COLORS['accent_blue'], height=75)
        card.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
        
        # Сохраняем ссылку на label значения
        self.stat_labels[col] = card.value_lbl
    
    def _update_dashboard(self, data: Dict):
        self.after(0, lambda: self._safe_update(data))
    
    def _safe_update(self, data: Dict):
        try:
            # Графики
            cpu_cores = data.get('cpu_per_core', [])
            self.cpu_graph.update_data([data.get('cpu', 0), max(cpu_cores) if cpu_cores else 0])
            self.ram_graph.update_data([data.get('memory_percent', 0), data.get('swap_percent', 0)])
            
            # Статистика
            cpu = data.get('cpu', 0)
            mem = data.get('memory_used_gb', 0)
            cs2 = data.get('cs2_count', 0)
            net = data.get('net_total_kb', 0)
            uptime = data.get('uptime', timedelta())
            
            if 0 in self.stat_labels:
                self.stat_labels[0].configure(text=f"{cpu:.0f}%", text_color=COLORS['accent_pink'] if cpu > 80 else COLORS['accent_green'])
            if 1 in self.stat_labels:
                self.stat_labels[1].configure(text=f"{mem}GB", text_color=COLORS['accent_cyan'])
            if 2 in self.stat_labels:
                self.stat_labels[2].configure(text=f"{cs2}", text_color=COLORS['accent_purple'])
            if 3 in self.stat_labels:
                self.stat_labels[3].configure(text=f"{Utils.format_bytes(net * 1024)}/s", text_color=COLORS['accent_blue'])
            
            h, rem = divmod(int(uptime.total_seconds()), 3600)
            m, s = divmod(rem, 60)
            if 4 in self.stat_labels:
                self.stat_labels[4].configure(text=f"{h:02d}:{m:02d}", text_color=COLORS['accent_yellow'])
            
            # CS2 карточки
            self._update_cs2(data.get('cs2_loads', []))
            
            # Уведомления
            for alert in self.system_monitor.get_alerts()[-5:]:
                self._log(f"⚠️ {alert['message']}", alert['level'])
                
        except Exception as e:
            pass
    
    def _update_cs2(self, loads: List[Dict]):
        self.cs2_count.configure(text=f"{len(loads)}/4")
        
        for i, load in enumerate(loads):
            pid = load.get('pid')
            acc_id = None
            username = f"CS2 #{i+1}"
            
            for aid, info in self.pm.cs2_instances.items():
                if info.get('pid') == pid:
                    acc_id = aid
                    username = info.get('username', f"CS2 #{i+1}")
                    break
            
            if acc_id is None:
                acc_id = pid
            
            if acc_id not in self.cs2_cards:
                card = CS2Card(self.cs2_frame, username, i, self._apply_bes)
                card.pack(fill="x", padx=10, pady=6)
                self.cs2_cards[acc_id] = card
            
            bes = self.pm.is_bes_applied(acc_id)
            self.cs2_cards[acc_id].update(load.get('cpu', 0), load.get('memory', 0), load.get('threads', 0), bes)
        
        for aid, card in list(self.cs2_cards.items()):
            active = any(self.pm.cs2_instances.get(aid, {}).get('pid') == l.get('pid') for l in loads)
            if not active:
                card.set_inactive()
    
    def _apply_bes(self, account_id: int):
        threading.Thread(target=self._bes_thread, args=(account_id,), daemon=True).start()
    
    def _bes_thread(self, account_id: int):
        try:
            username = self.pm.cs2_instances.get(account_id, {}).get('username', f"#{account_id}")
            self._log(f"🔧 BES к {username}...", "info")
            
            if self.pm.apply_bes_to_account(account_id):
                self._log(f"✅ BES применён", "success")
            else:
                self._log(f"❌ BES ошибка", "error")
            
            self.after(0, self._load_accounts)
        except Exception as e:
            self._log(f"❌ BES: {e}", "error")
    
    def _refresh_loop(self):
        pids = [info.get('pid') for info in self.pm.cs2_instances.values() if info.get('pid')]
        self.system_monitor.update_cs2_pids(pids)
        self.after(REFRESH_RATE_MS, self._refresh_loop)
    
    def _auto_import_accounts(self):
        path = os.path.join(config.BASE_DIR, 'logpass.txt')
        if os.path.exists(path):
            count = self.am.import_from_logpass(path)
            self._log(f"✅ Импортировано: {count}", "success" if count > 0 else "info")
        else:
            self._log("⚠️ logpass.txt не найден", "warning")
    
    def _load_accounts(self):
        for w in self.accounts_frame.winfo_children():
            w.destroy()
        
        accounts = self.am.get_all()
        self._update_selected()
        
        if not accounts:
            ctk.CTkLabel(self.accounts_frame, text="📭 Нет аккаунтов", font=ctk.CTkFont(size=13), text_color=COLORS['text_secondary']).pack(pady=30)
            return
        
        for acc in accounts:
            self._create_row(acc)
    
    def _create_row(self, acc: Account):
        row = ctk.CTkFrame(self.accounts_frame, fg_color=COLORS['bg_light'], corner_radius=6, height=32)
        row.pack(fill="x", padx=4, pady=2)
        
        var = ctk.BooleanVar(value=self.selected_accounts.get(acc.id, False))
        cb = ctk.CTkCheckBox(row, text="", variable=var, width=24, checkbox_width=14, command=lambda aid=acc.id, v=var: self._update_sel(aid, v.get()), hover_color=COLORS['accent_green'])
        cb.pack(side="left", padx=4, pady=4)
        
        ctk.CTkLabel(row, text=acc.username[:18], width=120, anchor="w", font=ctk.CTkFont(size=10, weight="bold"), text_color=COLORS['text_primary']).pack(side="left", padx=4)
        
        colors = {AccountStatus.STOPPED: COLORS['text_secondary'], AccountStatus.STARTING: COLORS['accent_orange'], AccountStatus.IN_GAME: COLORS['accent_green'], AccountStatus.ERROR: COLORS['accent_red']}
        icons = {AccountStatus.STOPPED: "⏸️", AccountStatus.STARTING: "⏳", AccountStatus.IN_GAME: "✅", AccountStatus.ERROR: "❌"}
        sc = colors.get(acc.status, COLORS['text_secondary'])
        si = icons.get(acc.status, "⏸️")
        ctk.CTkLabel(row, text=si, width=30, text_color=sc, font=ctk.CTkFont(size=12)).pack(side="left", padx=4)
        
        mc = COLORS['accent_green'] if acc.ma_file_path else COLORS['accent_red']
        ctk.CTkLabel(row, text="✅" if acc.ma_file_path else "❌", width=30, text_color=mc, font=ctk.CTkFont(size=10)).pack(side="left", padx=4)
        
        pt = acc.play_time_minutes if acc.play_time_minutes else 0
        ctk.CTkLabel(row, text=f"{pt//60}ч{pt%60}м", width=65, font=ctk.CTkFont(size=9), text_color=COLORS['text_secondary']).pack(side="left", padx=4)
    
    def _update_sel(self, aid: int, sel: bool):
        self.selected_accounts[aid] = sel
        self._update_selected()
    
    def _update_selected(self):
        cnt = sum(1 for v in self.selected_accounts.values() if v)
    
    def _select_all(self):
        for acc in self.am.get_all():
            self.selected_accounts[acc.id] = True
        self._load_accounts()
        self._log("☑️ Выбраны все", "info")
    
    def _start_selected(self):
        selected = [aid for aid, s in self.selected_accounts.items() if s]
        
        if not selected:
            self._log("⚠️ Выберите аккаунты!", "warning")
            return
        if self.is_running:
            self._log("⚠️ Уже запущено", "warning")
            return
        
        self.is_running = True
        self.start_btn.configure(state="disabled")
        self.status_text.configure(text="Запуск...", text_color=COLORS['accent_orange'])
        self.status_dot.configure(text_color=COLORS['accent_orange'])
        
        self._log(f"🚀 Запуск {len(selected)}...", "info")
        
        def run():
            total = len(selected)
            self.am.start_accounts_sequential(selected, self._on_progress)
            
            self.pm.mark_all_accounts_launched(total)
            if getattr(config, 'POSITION_WINDOWS_AFTER_ALL_LAUNCHED', False):
                self._log("🪟 Позиционирование...", "info")
                time.sleep(5)
                self.pm.position_all_windows_after_launch(total)
            
            self.is_running = False
            self.after(0, self._on_complete)
        
        threading.Thread(target=run, daemon=True).start()
    
    def _stop_all(self):
        self._log("⏹️ Остановка...", "info")
        self.am.stop_all()
        self.is_running = False
        self.start_btn.configure(state="normal")
        self.status_text.configure(text="Готов", text_color=COLORS['accent_green'])
        self.status_dot.configure(text_color=COLORS['accent_green'])
        self._load_accounts()
        self._log("✅ Остановлено", "success")
    
    def _on_progress(self, current: int, total: int):
        self._log(f"✅ {current}/{total}", "success")
        self.after(0, self._load_accounts)
    
    def _on_complete(self):
        self.start_btn.configure(state="normal")
        self.status_text.configure(text="Запущено", text_color=COLORS['accent_green'])
        self.status_dot.configure(text_color=COLORS['accent_green'])
        self._log("✅ Все запущены!", "success")
        self._log("ℹ️ 🔧 BES для каждого", "info")
        self._load_accounts()
    
    def _log(self, msg: str, level: str = "info"):
        if hasattr(self, 'log_panel'):
            self.log_panel.log(msg, level)
        try:
            with open(config.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        except:
            pass
    
    def _on_closing(self):
        self.console_capture.stop()
        self.system_monitor.stop()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app._on_closing)
    app.mainloop()