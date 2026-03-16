"""
CS2Farmer Pro v4.0.0 ULTIMATE
Профессиональный дизайн + Modern UI + Glassmorphism + Animations
"""
import customtkinter as ctk
import tkinter as tk
from CTkMessagebox import CTkMessagebox
from CTkToolTip import CTkToolTip
import threading
import os
import sys
import psutil
import subprocess
import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
from collections import deque
import win32gui
import win32con
from pathlib import Path
from ..database import Database
from ..process_manager import ProcessManager
from ..account_manager import AccountManager
from ..ban_checker import BanChecker
from ..models import AccountStatus, Account
from .. import config
from ..monitoring import ConsoleCapture, SystemMonitor

# ============================================================================
# КОНСТАНТЫ
# ============================================================================
VERSION = "4.0.0 ULTIMATE"
MAX_LOG_LINES = 1000
GRAPH_POINTS = 100
REFRESH_RATE_MS = 500

# ============================================================================
# СОВРЕМЕННАЯ ЦВЕТОВАЯ СХЕМА (Modern Dark + Neon)
# ============================================================================
COLORS = {
    # Основные фоны (Glassmorphism)
    'bg_primary': '#0a0a0f',
    'bg_secondary': '#12121a',
    'bg_card': '#1a1a25',
    'bg_hover': '#252535',
    'bg_active': '#2a2a40',
    'bg_glass': '#1a1a25cc',  # С прозрачностью
    
    # Текст
    'text_primary': '#ffffff',
    'text_secondary': '#9ca3af',
    'text_muted': '#6b7280',
    
    # Акценты (Neon Gradient)
    'accent_green': '#10b981',
    'accent_green_light': '#34d399',
    'accent_blue': '#3b82f6',
    'accent_blue_light': '#60a5fa',
    'accent_purple': '#8b5cf6',
    'accent_purple_light': '#a78bfa',
    'accent_cyan': '#06b6d4',
    'accent_cyan_light': '#22d3ee',
    'accent_orange': '#f59e0b',
    'accent_red': '#ef4444',
    'accent_pink': '#ec4899',
    
    # Градиенты
    'gradient_1': ['#3b82f6', '#8b5cf6'],
    'gradient_2': ['#10b981', '#06b6d4'],
    'gradient_3': ['#f59e0b', '#ef4444'],
    
    # Границы и тени
    'border': '#2d3748',
    'border_glow': '#3b82f640',
    'shadow': '#00000080',
}

# ============================================================================
# SRT DATA MANAGER
# ============================================================================
class SRTDataManager:
    """Управление данными SRT"""
    
    def __init__(self):
        self.srt_data_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'srt_data'
        )
        self.servers_file = os.path.join(self.srt_data_dir, 'servers.json')
        self.config_file = os.path.join(self.srt_data_dir, 'srt_config.json')
        self._ensure_data_dir()
        self._load_data()
    
    def _ensure_data_dir(self):
        os.makedirs(self.srt_data_dir, exist_ok=True)
        
        if not os.path.exists(self.servers_file):
            servers_data = {
                "servers": [
                    {"id": "eu_west", "name": "Europe West", "ping": "20-40ms"},
                    {"id": "eu_east", "name": "Europe East", "ping": "30-50ms"},
                    {"id": "us_east", "name": "US East", "ping": "80-120ms"},
                    {"id": "russia", "name": "Russia", "ping": "40-80ms"},
                ],
                "default": "eu_west"
            }
            with open(self.servers_file, 'w', encoding='utf-8') as f:
                json.dump(servers_data, f, indent=2, ensure_ascii=False)
        
        if not os.path.exists(self.config_file):
            config_data = {"selected_server": "eu_west"}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def _load_data(self):
        try:
            with open(self.servers_file, 'r', encoding='utf-8') as f:
                self.servers = json.load(f)
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except:
            self.servers = {"servers": [], "default": "eu_west"}
            self.config = {"selected_server": "eu_west"}
    
    def get_servers(self) -> List[dict]:
        return self.servers.get('servers', [])
    
    def get_selected_server(self) -> str:
        return self.config.get('selected_server', 'eu_west')
    
    def set_selected_server(self, server_id: str):
        self.config['selected_server'] = server_id
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def get_server_by_id(self, server_id: str) -> Optional[dict]:
        for server in self.get_servers():
            if server['id'] == server_id:
                return server
        return None

# ============================================================================
# STEAM ROOT TOOL
# ============================================================================
class SteamRootTool:
    """SRT - Управление Steam"""
    
    def __init__(self):
        self.steam_paths = [
            r"C:\Program Files (x86)\Steam",
            r"C:\Program Files\Steam",
            os.path.expandvars(r"%ProgramFiles(x86)%\Steam"),
        ]
        self.steam_dir = None
        self.config_dir = None
        self.srt_data = SRTDataManager()
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
                return f"{HIWORD(info['FileVersionMS'])}.{LOWORD(info['FileVersionMS'])}"
        except:
            pass
        return "Unknown"
    
    def get_servers(self) -> List[dict]:
        return self.srt_data.get_servers()
    
    def get_selected_server(self) -> str:
        return self.srt_data.get_selected_server()
    
    def set_selected_server(self, server_id: str) -> bool:
        try:
            self.srt_data.set_selected_server(server_id)
            return True
        except:
            return False
    
    def get_server_by_id(self, server_id: str) -> Optional[dict]:
        return self.srt_data.get_server_by_id(server_id)
    
    def clear_steam_cache(self) -> int:
        cleared = 0
        cache_paths = [
            os.path.join(self.steam_dir, 'appcache') if self.steam_dir else '',
            os.path.join(self.steam_dir, 'config', 'htmlcache') if self.steam_dir else '',
            os.path.join(os.getenv('APPDATA'), 'Steam', 'htmlcache'),
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
            subprocess.run(['taskkill', '/f', '/im', 'steam.exe'], 
                          capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
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
        for proc_name in ['steam.exe', 'steamwebhelper.exe']:
            try:
                result = subprocess.run(['taskkill', '/f', '/im', proc_name], 
                                       capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if result.returncode == 0:
                    killed += 1
            except:
                pass
        return killed

# ============================================================================
# UI КОМПОНЕНТЫ (УЛУЧШЕННЫЕ)
# ============================================================================
class ModernGraph(ctk.CTkCanvas):
    """✅ Современный график с градиентом и анимацией"""
    
    def __init__(self, parent, title: str, colors: List[str], 
                 width: int = 220, height: int = 100):
        super().__init__(parent, width=width, height=height, 
                        bg=COLORS['bg_card'], highlightthickness=0)
        
        self.colors = colors
        self.data_series: List[deque] = [deque(maxlen=GRAPH_POINTS) for _ in colors]
        self.title = title
        self.graph_width = width - 20
        self.graph_height = height - 30
        
        # Заголовок
        self.create_text(10, 8, text=title, fill=COLORS['text_secondary'], 
                        anchor="nw", font=("Segoe UI", 9, "bold"))
        
        # Значения
        self.value_labels = []
        for i, color in enumerate(colors):
            y = 8 + i * 16
            lbl = self.create_text(width - 10, y, text="0%", fill=color, 
                                  anchor="ne", font=("Segoe UI", 8, "bold"))
            self.value_labels.append(lbl)
        
        # Сетка
        for i in range(4):
            y = 28 + i * (self.graph_height // 3)
            self.create_line(12, y, width - 10, y, fill=COLORS['border'], width=1)
    
    def update_data(self, values: List[float]):
        for i, value in enumerate(values):
            if i < len(self.data_series):
                self.data_series[i].append(value)
                self.itemconfig(self.value_labels[i], text=f"{value:.0f}%")
        
        self.draw_graphs()
    
    def draw_graphs(self):
        self.delete("graph")
        
        for series_idx, data in enumerate(self.data_series):
            if len(data) < 2:
                continue
            
            width = self.graph_width / GRAPH_POINTS
            points = []
            
            for i, value in enumerate(data):
                x = 14 + i * width
                y = self.graph_height + 25 - (min(value, 100) / 100 * self.graph_height)
                points.extend([x, y])
            
            if points:
                # Основная линия с градиентом
                self.create_line(points, fill=self.colors[series_idx], 
                               width=2, tags="graph", smooth=True, capstyle="round")
                
                # Заполнение
                fill_points = [14, self.graph_height + 25] + points + [14 + len(data) * width, self.graph_height + 25]
                self.create_polygon(fill_points, fill=self.colors[series_idx], 
                                  outline="", tags="graph", stipple='gray50')
    
    def clear(self):
        for series in self.data_series:
            series.clear()
        self.delete("graph")


class GradientCard(ctk.CTkFrame):
    """✅ Карточка с градиентной границей и тенью"""
    
    def __init__(self, parent, title: str, icon: str, value: str = "0",
                 gradient_color: str = COLORS['accent_blue'], height: int = 75):
        super().__init__(parent, fg_color=COLORS['bg_card'], corner_radius=10)
        self.configure(height=height)
        
        # Градиентная полоска слева
        gradient = ctk.CTkFrame(self, fg_color=gradient_color, width=4, corner_radius=0)
        gradient.place(relx=0, rely=0, relheight=1)
        
        # Иконка
        icon_lbl = ctk.CTkLabel(self, text=icon, font=ctk.CTkFont(size=16), 
                               text_color=gradient_color)
        icon_lbl.place(relx=0.08, rely=0.5, anchor="w")
        
        # Заголовок
        title_lbl = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=8), 
                                text_color=COLORS['text_secondary'])
        title_lbl.place(relx=0.22, rely=0.35, anchor="w")
        
        # Значение
        self.value_lbl = ctk.CTkLabel(self, text=value, 
                                     font=ctk.CTkFont(size=16, weight="bold"), 
                                     text_color=COLORS['text_primary'])
        self.value_lbl.place(relx=0.22, rely=0.65, anchor="w")
        
        # Тултип
        CTkToolTip(self, message=f"{title}: {value}", delay=0.5)
    
    def update_value(self, value: str, color: str = None):
        self.value_lbl.configure(text=value)


class ModernCS2Card(ctk.CTkFrame):
    """✅ Современная карточка CS2 с анимацией"""
    
    def __init__(self, parent, username: str, index: int, apply_bes_callback):
        super().__init__(parent, fg_color=COLORS['bg_card'], corner_radius=10)
        
        self.account_id = index
        self.username = username
        self.apply_bes_callback = apply_bes_callback
        
        # Верхняя строка
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=8)
        
        # Номер и имя
        ctk.CTkLabel(top, text=f"#{index + 1}", width=30, 
                    font=ctk.CTkFont(size=11, weight="bold"), 
                    text_color=COLORS['accent_blue']).pack(side="left")
        
        ctk.CTkLabel(top, text=username[:18], width=120, anchor="w", 
                    font=ctk.CTkFont(size=9), 
                    text_color=COLORS['text_primary']).pack(side="left", padx=6)
        
        # Статус
        self.status = ctk.CTkLabel(top, text="⚪", font=ctk.CTkFont(size=12))
        self.status.pack(side="right")
        
        # Статистика
        stats = ctk.CTkFrame(self, fg_color=COLORS['bg_secondary'], corner_radius=8)
        stats.pack(fill="x", padx=10, pady=4)
        
        stats_grid = ctk.CTkFrame(stats, fg_color="transparent")
        stats_grid.pack(fill="x", padx=6, pady=4)
        
        stats_grid.grid_columnconfigure(0, weight=1)
        stats_grid.grid_columnconfigure(1, weight=1)
        stats_grid.grid_columnconfigure(2, weight=1)
        
        self.cpu = ctk.CTkLabel(stats_grid, text="0%", font=ctk.CTkFont(size=8), 
                               text_color=COLORS['accent_red'])
        self.cpu.grid(row=0, column=0, padx=3)
        
        self.ram = ctk.CTkLabel(stats_grid, text="0MB", font=ctk.CTkFont(size=8), 
                               text_color=COLORS['accent_cyan'])
        self.ram.grid(row=0, column=1, padx=3)
        
        self.thr = ctk.CTkLabel(stats_grid, text="0", font=ctk.CTkFont(size=8), 
                               text_color=COLORS['accent_purple'])
        self.thr.grid(row=0, column=2, padx=3)
        
        # BES кнопка
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="x", padx=10, pady=(0, 6))
        
        self.bes_btn = ctk.CTkButton(bottom, text="BES", width=45, height=22, 
                                    font=ctk.CTkFont(size=7, weight="bold"), 
                                    fg_color=COLORS['accent_orange'], 
                                    hover_color='#f97316',
                                    corner_radius=5, command=self._on_bes)
        self.bes_btn.pack(side="left")
        
        self.bes_status = ctk.CTkLabel(bottom, text="⚪", font=ctk.CTkFont(size=9))
        self.bes_status.pack(side="left", padx=5)
        
        # Мини-график
        self.graph = ModernGraph(bottom, "", [COLORS['accent_red']], 
                                width=110, height=22)
        self.graph.pack(side="right")
        
        # Тултип
        CTkToolTip(self, message=f"CS2 #{index + 1}: {username}", delay=0.5)
    
    def _on_bes(self):
        if self.apply_bes_callback:
            self.apply_bes_callback(self.account_id)
    
    def update(self, cpu: float, mem: int, thr: int, bes: bool = False):
        self.cpu.configure(text=f"{cpu:.0f}%")
        self.ram.configure(text=f"{mem}MB")
        self.thr.configure(text=f"{thr}")
        
        if bes:
            self.bes_status.configure(text="🟢", text_color=COLORS['accent_green'])
            self.bes_btn.configure(state="disabled", text="BES ✓", 
                                  fg_color=COLORS['accent_green'])
            self.status.configure(text="🟢")
        else:
            self.bes_status.configure(text="⚪")
            self.bes_btn.configure(state="normal", text="BES", 
                                  fg_color=COLORS['accent_orange'])
            self.status.configure(text="🟡")
        
        self.graph.update_data([cpu])
    
    def set_inactive(self):
        self.cpu.configure(text="-")
        self.ram.configure(text="-")
        self.thr.configure(text="-")
        self.status.configure(text="⚪")
        self.bes_btn.configure(state="disabled")


class CompactServerSelector(ctk.CTkFrame):
    """✅ Компактный выбор серверов с OptionMenu"""
    
    def __init__(self, parent, srt, log_callback):
        super().__init__(parent, fg_color=COLORS['bg_card'], corner_radius=10)
        
        self.srt = srt
        self.log_callback = log_callback
        self.selected_server = self.srt.get_selected_server()
        
        # Заголовок
        ctk.CTkLabel(self, text="🌐 Сервер", font=ctk.CTkFont(size=10, weight="bold"), 
                    text_color=COLORS['text_primary']).pack(padx=10, pady=8)
        
        # Текущий сервер
        current = self.srt.get_server_by_id(self.selected_server)
        server_name = current['name'] if current else "Unknown"
        
        self.current_lbl = ctk.CTkLabel(self, text=f"📍 {server_name}", 
                                       font=ctk.CTkFont(size=8), 
                                       text_color=COLORS['accent_blue'])
        self.current_lbl.pack(padx=10, pady=2)
        
        # Выпадающий список
        servers = self.srt.get_servers()
        server_names = [s['name'] for s in servers]
        self.server_map = {s['name']: s['id'] for s in servers}
        
        self.server_var = ctk.StringVar(value=server_name)
        self.server_menu = ctk.CTkOptionMenu(self, values=server_names, 
                                            variable=self.server_var, 
                                            width=160, height=28, 
                                            font=ctk.CTkFont(size=8),
                                            fg_color=COLORS['bg_secondary'],
                                            button_color=COLORS['bg_hover'],
                                            button_hover_color=COLORS['bg_active'],
                                            command=self._on_server_change)
        self.server_menu.pack(padx=10, pady=6)
        
        # Кнопки
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(padx=10, pady=6)
        
        ctk.CTkButton(btns, text="🔄", width=35, height=24, 
                     fg_color=COLORS['accent_blue'], font=ctk.CTkFont(size=8), 
                     corner_radius=5, command=self._restart).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="🗑️", width=35, height=24, 
                     fg_color=COLORS['accent_orange'], font=ctk.CTkFont(size=8), 
                     corner_radius=5, command=self._clear).pack(side="left", padx=2)
        ctk.CTkButton(btns, text="💀", width=35, height=24, 
                     fg_color=COLORS['accent_red'], font=ctk.CTkFont(size=8), 
                     corner_radius=5, command=self._kill).pack(side="left", padx=2)
        
        # Тултипы
        CTkToolTip(btns.winfo_children()[0], message="Перезапустить Steam")
        CTkToolTip(btns.winfo_children()[1], message="Очистить кэш")
        CTkToolTip(btns.winfo_children()[2], message="Завершить процессы")
    
    def _on_server_change(self, name):
        server_id = self.server_map.get(name)
        if server_id and self.srt.set_selected_server(server_id):
            self.selected_server = server_id
            self.log_callback(f"✅ Сервер: {name}", "success")
    
    def _restart(self):
        threading.Thread(target=self._restart_thread, daemon=True).start()
    
    def _restart_thread(self):
        self.log_callback("🔄 Restart Steam...", "info")
        if self.srt.restart_steam():
            self.log_callback("✅ OK", "success")
    
    def _clear(self):
        threading.Thread(target=self._clear_thread, daemon=True).start()
    
    def _clear_thread(self):
        self.log_callback("🗑️ Clear cache...", "info")
        count = self.srt.clear_steam_cache()
        self.log_callback(f"✅ {count} cleared", "success")
    
    def _kill(self):
        threading.Thread(target=self._kill_thread, daemon=True).start()
    
    def _kill_thread(self):
        self.log_callback("💀 Kill processes...", "warning")
        count = self.srt.kill_steam_processes()
        self.log_callback(f"✅ {count} killed", "success")


class ModernLogPanel(ctk.CTkFrame):
    """✅ Современная панель логов с фильтрами"""
    
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS['bg_card'], corner_radius=10)
        
        # Заголовок
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=8)
        
        ctk.CTkLabel(header, text="📋 Логи", font=ctk.CTkFont(size=10, weight="bold"), 
                    text_color=COLORS['text_primary']).pack(side="left")
        
        # Фильтр
        self.filter_var = ctk.StringVar(value="Все")
        filter_menu = ctk.CTkOptionMenu(header, values=['Все', 'Info', 'Warning', 'Error', 'Success'], 
                                       variable=self.filter_var, 
                                       width=85, height=26, 
                                       font=ctk.CTkFont(size=7),
                                       fg_color=COLORS['bg_secondary'])
        filter_menu.pack(side="right")
        
        # Текст
        self.log_text = ctk.CTkTextbox(self, font=ctk.CTkFont(size=7, family="Consolas"), 
                                      wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=8)
        
        # Цвета
        self.log_text.tag_config("success", foreground=COLORS['accent_green'])
        self.log_text.tag_config("error", foreground=COLORS['accent_red'])
        self.log_text.tag_config("warning", foreground=COLORS['accent_orange'])
        self.log_text.tag_config("info", foreground=COLORS['accent_blue'])
        
        self.log_count = 0
    
    def log(self, msg: str, level: str = "info"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {msg}\n", level)
        self.log_text.see("end")
        self.log_count += 1
        
        lines = int(self.log_text.index('end-1c').split('.')[0])
        if lines > MAX_LOG_LINES:
            self.log_text.delete("1.0", f"{lines - MAX_LOG_LINES}.0")
    
    def clear(self):
        self.log_text.delete("1.0", "end")
        self.log_count = 0

# ============================================================================
# ГЛАВНОЕ ПРИЛОЖЕНИЕ
# ============================================================================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title(f"🎮 CS2Farmer Pro v{VERSION}")
        self.geometry("1400x850")  # ✅ Оптимальный размер
        self.minsize(1300, 750)
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Сетка (2 колонки)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)
        
        self.db = Database(config.DB_PATH, "cs2farmer")
        self.pm = ProcessManager()
        
        try:
            self.ban_checker = BanChecker(api_key="")
        except:
            self.ban_checker = self._create_dummy_ban_checker()
        
        self.am = AccountManager(self.db, self.pm, self.ban_checker)
        self.srt = SteamRootTool()
        
        self.selected_accounts: Dict[int, bool] = {}
        self.is_running = False
        self.cs2_cards: Dict[int, ModernCS2Card] = {}
        self.stat_labels: Dict[int, ctk.CTkLabel] = {}
        self.start_time = datetime.now()
        
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
        # === ЛЕВАЯ КОЛОНКА: АККАУНТЫ ===
        left_panel = ctk.CTkFrame(self, fg_color=COLORS['bg_primary'], corner_radius=0)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 3))
        
        # Заголовок
        header = ctk.CTkFrame(left_panel, fg_color=COLORS['bg_card'], corner_radius=10)
        header.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header, text="🎮 CS2Farmer", font=ctk.CTkFont(size=18, weight="bold"), 
                    text_color=COLORS['text_primary']).pack(side="left", padx=10, pady=10)
        ctk.CTkLabel(header, text=f"v{VERSION}", font=ctk.CTkFont(size=8), 
                    text_color=COLORS['accent_blue']).pack(side="left", pady=16)
        
        # Статус
        status = ctk.CTkFrame(header, fg_color=COLORS['bg_secondary'], corner_radius=8)
        status.pack(fill="x", padx=10, pady=6)
        
        self.status_dot = ctk.CTkLabel(status, text="●", font=ctk.CTkFont(size=13), 
                                      text_color=COLORS['accent_green'])
        self.status_dot.pack(side="left", padx=8, pady=6)
        
        self.status_text = ctk.CTkLabel(status, text="Готов", font=ctk.CTkFont(size=10, weight="bold"), 
                                       text_color=COLORS['accent_green'])
        self.status_text.pack(side="left", padx=6, pady=6)
        
        # Кнопки
        btns = ctk.CTkFrame(header, fg_color="transparent")
        btns.pack(fill="x", padx=10, pady=6)
        
        self.start_btn = ctk.CTkButton(btns, text="▶️ Старт", width=85, height=36, 
                                      fg_color=COLORS['accent_green'], 
                                      hover_color=COLORS['accent_green_light'],
                                      font=ctk.CTkFont(size=10, weight="bold"), 
                                      corner_radius=7, command=self._start_selected)
        self.start_btn.pack(side="left", padx=(0, 4))
        
        self.stop_btn = ctk.CTkButton(btns, text="⏹️ Стоп", width=65, height=36, 
                                     fg_color=COLORS['accent_red'], 
                                     hover_color='#dc2626',
                                     font=ctk.CTkFont(size=10, weight="bold"), 
                                     corner_radius=7, command=self._stop_all)
        self.stop_btn.pack(side="left", padx=(0, 4))
        
        ctk.CTkButton(btns, text="🔄", width=36, height=36, fg_color=COLORS['accent_blue'], 
                     font=ctk.CTkFont(size=10), corner_radius=7, 
                     command=self._load_accounts).pack(side="left", padx=(0, 4))
        ctk.CTkButton(btns, text="☑️", width=36, height=36, fg_color=COLORS['bg_secondary'], 
                     font=ctk.CTkFont(size=10), corner_radius=7, 
                     command=self._select_all).pack(side="left")
        
        # Список аккаунтов
        acc_list = ctk.CTkFrame(left_panel, fg_color=COLORS['bg_card'], corner_radius=10)
        acc_list.pack(fill="both", expand=True, padx=10, pady=6)
        
        hdr = ctk.CTkFrame(acc_list, fg_color=COLORS['bg_secondary'], height=30, corner_radius=8)
        hdr.pack(fill="x", padx=6, pady=(6, 0))
        
        ctk.CTkLabel(hdr, text="✓", width=22, font=ctk.CTkFont(weight="bold", size=8), 
                    text_color=COLORS['text_primary']).pack(side="left", padx=3)
        ctk.CTkLabel(hdr, text="Аккаунт", width=100, font=ctk.CTkFont(weight="bold", size=8), 
                    text_color=COLORS['text_primary']).pack(side="left", padx=3)
        ctk.CTkLabel(hdr, text="Статус", width=35, font=ctk.CTkFont(weight="bold", size=8), 
                    text_color=COLORS['text_primary']).pack(side="left", padx=3)
        ctk.CTkLabel(hdr, text="maFile", width=35, font=ctk.CTkFont(weight="bold", size=8), 
                    text_color=COLORS['text_primary']).pack(side="left", padx=3)
        
        self.accounts_frame = ctk.CTkScrollableFrame(acc_list, fg_color="transparent")
        self.accounts_frame.pack(fill="both", expand=True, padx=6, pady=6)
        
        # === ПРАВАЯ КОЛОНКА: ДАШБОРД ===
        right_panel = ctk.CTkFrame(self, fg_color=COLORS['bg_primary'], corner_radius=0)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(3, 0))
        
        # Графики
        graphs = ctk.CTkFrame(right_panel, fg_color=COLORS['bg_card'], corner_radius=10)
        graphs.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(graphs, text="📈 Мониторинг", font=ctk.CTkFont(size=12, weight="bold"), 
                    text_color=COLORS['text_primary']).pack(padx=10, pady=8)
        
        graphs_grid = ctk.CTkFrame(graphs, fg_color="transparent")
        graphs_grid.pack(fill="x", padx=10, pady=4)
        
        graphs_grid.grid_columnconfigure(0, weight=1)
        graphs_grid.grid_columnconfigure(1, weight=1)
        
        self.cpu_graph = ModernGraph(graphs_grid, "CPU", [COLORS['accent_red'], COLORS['accent_orange']], 
                                     width=220, height=100)
        self.cpu_graph.grid(row=0, column=0, padx=6, pady=6)
        
        self.ram_graph = ModernGraph(graphs_grid, "RAM", [COLORS['accent_cyan'], COLORS['accent_blue']], 
                                     width=220, height=100)
        self.ram_graph.grid(row=0, column=1, padx=6, pady=6)
        
        # Статистика
        stats = ctk.CTkFrame(right_panel, fg_color=COLORS['bg_card'], corner_radius=10)
        stats.pack(fill="x", padx=10, pady=4)
        
        ctk.CTkLabel(stats, text="📊 Статистика", font=ctk.CTkFont(size=12, weight="bold"), 
                    text_color=COLORS['text_primary']).pack(padx=10, pady=8)
        
        stats_grid = ctk.CTkFrame(stats, fg_color="transparent")
        stats_grid.pack(fill="x", padx=10, pady=4)
        
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
        
        # CS2 процессы
        cs2_frame = ctk.CTkFrame(right_panel, fg_color=COLORS['bg_card'], corner_radius=10)
        cs2_frame.pack(fill="both", expand=True, padx=10, pady=4)
        
        cs2_hdr = ctk.CTkFrame(cs2_frame, fg_color="transparent")
        cs2_hdr.pack(fill="x", padx=10, pady=8)
        
        ctk.CTkLabel(cs2_hdr, text="🎮 CS2 Процессы", font=ctk.CTkFont(size=12, weight="bold"), 
                    text_color=COLORS['text_primary']).pack(side="left")
        self.cs2_count = ctk.CTkLabel(cs2_hdr, text="0/4", font=ctk.CTkFont(size=9), 
                                     text_color=COLORS['text_secondary'])
        self.cs2_count.pack(side="right")
        
        self.cs2_scroll = ctk.CTkScrollableFrame(cs2_frame, fg_color="transparent")
        self.cs2_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        
        # SRT + Логи (внизу)
        bottom_frame = ctk.CTkFrame(right_panel, fg_color=COLORS['bg_card'], corner_radius=10)
        bottom_frame.pack(fill="x", padx=10, pady=4)
        
        bottom_grid = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        bottom_grid.pack(fill="x", padx=6, pady=6)
        
        bottom_grid.grid_columnconfigure(0, weight=1)
        bottom_grid.grid_columnconfigure(1, weight=2)
        
        # SRT
        self.server_selector = CompactServerSelector(bottom_grid, self.srt, self._log)
        self.server_selector.grid(row=0, column=0, padx=4, pady=4, sticky="nsew")
        
        # Логи
        self.log_panel = ModernLogPanel(bottom_grid)
        self.log_panel.grid(row=0, column=1, padx=4, pady=4, sticky="nsew")
        
        self._log("🎉 CS2Farmer запущен!", "success")
        self._log(f"⚡ Версия: {VERSION}", "info")
    
    def _create_stat_card(self, parent, title: str, icon: str, value: str, row: int, col: int):
        card = GradientCard(parent, title, icon, value, COLORS['accent_blue'], height=75)
        card.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
        self.stat_labels[col] = card.value_lbl
    
    def _update_dashboard(self, data: Dict):
        self.after(0, lambda: self._safe_update(data))
    
    def _safe_update(self, data: Dict):
        try:
            cpu_cores = data.get('cpu_per_core', [])
            self.cpu_graph.update_data([data.get('cpu', 0), max(cpu_cores) if cpu_cores else 0])
            self.ram_graph.update_data([data.get('memory_percent', 0), data.get('swap_percent', 0)])
            
            cpu = data.get('cpu', 0)
            mem = data.get('memory_used_gb', 0)
            cs2 = data.get('cs2_count', 0)
            net = data.get('net_total_kb', 0)
            
            # ВРЕМЯ РАБОТЫ
            uptime = datetime.now() - self.start_time
            h, rem = divmod(int(uptime.total_seconds()), 3600)
            m, s = divmod(rem, 60)
            time_str = f"{h:02d}:{m:02d}:{s:02d}"
            
            if 0 in self.stat_labels:
                self.stat_labels[0].configure(text=f"{cpu:.0f}%")
            if 1 in self.stat_labels:
                self.stat_labels[1].configure(text=f"{mem}GB")
            if 2 in self.stat_labels:
                self.stat_labels[2].configure(text=f"{cs2}")
            if 3 in self.stat_labels:
                self.stat_labels[3].configure(text=f"{net}KB/s")
            if 4 in self.stat_labels:
                self.stat_labels[4].configure(text=time_str)
            
            self._update_cs2(data.get('cs2_loads', []))
        except:
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
                card = ModernCS2Card(self.cs2_scroll, username, i, self._apply_bes)
                card.pack(fill="x", padx=6, pady=4)
                self.cs2_cards[acc_id] = card
            
            bes = self.pm.is_bes_applied(acc_id)
            self.cs2_cards[acc_id].update(load.get('cpu', 0), load.get('memory', 0), 
                                         load.get('threads', 0), bes)
        
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
        
        if not accounts:
            ctk.CTkLabel(self.accounts_frame, text="📭 Нет аккаунтов", 
                        font=ctk.CTkFont(size=10), 
                        text_color=COLORS['text_secondary']).pack(pady=15)
            return
        
        for acc in accounts:
            self._create_row(acc)
    
    def _create_row(self, acc: Account):
        row = ctk.CTkFrame(self.accounts_frame, fg_color=COLORS['bg_secondary'], 
                          corner_radius=8, height=30)
        row.pack(fill="x", padx=3, pady=1)
        
        var = ctk.BooleanVar(value=self.selected_accounts.get(acc.id, False))
        cb = ctk.CTkCheckBox(row, text="", variable=var, width=20, checkbox_width=13, 
                            command=lambda aid=acc.id, v=var: self._update_sel(aid, v.get()))
        cb.pack(side="left", padx=3, pady=3)
        
        ctk.CTkLabel(row, text=acc.username[:16], width=100, anchor="w", 
                    font=ctk.CTkFont(size=8, weight="bold"), 
                    text_color=COLORS['text_primary']).pack(side="left", padx=3)
        
        colors = {AccountStatus.STOPPED: COLORS['text_muted'], 
                 AccountStatus.STARTING: COLORS['accent_orange'], 
                 AccountStatus.IN_GAME: COLORS['accent_green'], 
                 AccountStatus.ERROR: COLORS['accent_red']}
        icons = {AccountStatus.STOPPED: "⏸️", AccountStatus.STARTING: "⏳", 
                AccountStatus.IN_GAME: "✅", AccountStatus.ERROR: "❌"}
        
        sc = colors.get(acc.status, COLORS['text_muted'])
        si = icons.get(acc.status, "⏸️")
        ctk.CTkLabel(row, text=si, width=30, text_color=sc, 
                    font=ctk.CTkFont(size=9)).pack(side="left", padx=3)
        
        mc = COLORS['accent_green'] if acc.ma_file_path else COLORS['accent_red']
        ctk.CTkLabel(row, text="✅" if acc.ma_file_path else "❌", width=30, 
                    text_color=mc, font=ctk.CTkFont(size=7)).pack(side="left", padx=3)
    
    def _update_sel(self, aid: int, sel: bool):
        self.selected_accounts[aid] = sel
    
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