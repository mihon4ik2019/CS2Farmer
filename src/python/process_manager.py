"""
Process Manager - ПАРАМЕТРЫ ДЛЯ КАЖДОГО АККАУНТА
Исправление: каждый аккаунт получает свои параметры
"""
import subprocess
import time
import os
import random
import psutil
import win32gui
import win32con
import threading
from typing import Optional, Dict, Tuple, List
from datetime import datetime

from . import config
from .window_finder import WindowFinder
from .bes_manager import BESManager
from .library_killer import LibraryKiller
from .cs2_waiter import CS2Waiter
from .window_manager import WindowManager
from .steam_launcher import SteamLauncher
from .fsm_settings import FSMSettings
from .cs2_video_config import CS2VideoConfig
from .steam_library_optimizer import SteamLibraryOptimizer
from .logger import SecureLogger

logger = SecureLogger()


class ProcessManager:
    STEAM_APP_ID = "730"
    
    def __init__(self):
        self.steam_instances: Dict[int, Dict] = {}
        self.cs2_instances: Dict[int, Dict] = {}
        self.instance_count = 0
        self.account_positions: Dict[int, int] = {}
        self.finder = WindowFinder()
        self.bes = BESManager()
        self.library_killer = LibraryKiller()
        self.cs2_waiter = CS2Waiter()
        self.window_manager = WindowManager()
        self.steam_launcher = SteamLauncher()
        self.fsm_settings = FSMSettings()
        self.video_config = CS2VideoConfig()
        self.library_optimizer = SteamLibraryOptimizer()
        self.optimized = False
        self.start_time = datetime.now()
    
    def optimize_once(self):
        if not self.optimized:
            logger.step("Оптимизация", "...")
            self.library_optimizer.optimize_library_load()
            self.optimized = True
            logger.success("Оптимизация завершена")
    
    def clear_cs2_tracker(self):
        self.cs2_waiter.clear_known_pids()
        self.window_manager.clear_all_positions()
        if config.RESET_WINDOW_POSITION_ON_START:
            self.account_positions.clear()
            self.instance_count = 0
        logger.debug("[ProcessManager] Трекер CS2 очищен")
    
    def get_total_cs2_count(self) -> int:
        return self.cs2_waiter.get_total_cs2_count()
    
    def get_uptime(self) -> str:
        uptime = datetime.now() - self.start_time
        return str(uptime).split('.')[0]
    
    def get_next_account_index(self) -> int:
        index = self.instance_count % 4
        self.instance_count += 1
        logger.debug(f"[ProcessManager] Позиция аккаунта: {index}")
        return index
    
    @staticmethod
    def find_steam_path() -> Optional[str]:
        paths = [
            r"C:\Program Files (x86)\Steam\steam.exe",
            r"C:\Program Files\Steam\steam.exe",
            os.path.expandvars(r"%ProgramFiles(x86)%\Steam\steam.exe"),
        ]
        for path in paths:
            if os.path.exists(path):
                return path
        return None

    def generate_ipc_name(self, account_id: int, username: str) -> str:
        return f"steam_{username}_{account_id}_{random.randint(1000,9999)}"[:60]

    def kill_all_steam(self):
        logger.step("Завершение", "Steam...")
        os.system("taskkill /f /im steam.exe 2>nul")
        os.system("taskkill /f /im steamwebhelper.exe 2>nul")
        time.sleep(3)
        logger.success("Steam завершён")

    def kill_all_cs2(self):
        os.system("taskkill /f /im cs2.exe 2>nul")
        time.sleep(2)
        logger.debug("CS2 завершён")

    def set_high_priority(self, pid: int) -> bool:
        try:
            process = psutil.Process(pid)
            process.nice(psutil.HIGH_PRIORITY_CLASS)
            logger.debug(f"[ProcessManager] ⚡ HIGH Priority (PID: {pid})")
            return True
        except:
            return False

    def set_process_affinity(self, pid: int, cores: list = [0, 1, 2, 3]) -> bool:
        try:
            process = psutil.Process(pid)
            process.cpu_affinity(cores)
            logger.debug(f"[ProcessManager] 🔗 Привязка к ядрам: {cores} (PID: {pid})")
            return True
        except:
            return False

    def start_steam_with_cs2(
        self,
        account_id: int,
        ipc_name: str,
        steam_data_dir: str,
        username: str,
        steam_id: int = None,
        window_position: tuple = (0, 0)
    ) -> Tuple[Optional[subprocess.Popen], Optional[int]]:
        self.optimize_once()
        
        account_index = self.get_next_account_index()
        self.account_positions[account_id] = account_index
        
        # ✅ ПРИМЕНЯЕМ ВИДЕО НАСТРОЙКИ ДЛЯ КАЖДОГО АККАУНТА
        self.video_config.apply_to_account(username)
        
        # ✅ ПАРАМЕТРЫ ИЗ CONFIG (ПРИМЕНЯЮТСЯ ДЛЯ КАЖДОГО)
        launch_params = config.CS2_LAUNCH_OPTIONS.copy()
        
        # Добавляем из FSM settings
        fsm_options = self.fsm_settings.get_launch_options()
        if fsm_options:
            launch_params.extend(fsm_options)
        
        if window_position and window_position != (0, 0):
            launch_params.extend(["+setpos", str(window_position[0]), str(window_position[1]), "0"])
        
        logger.step("Запуск", f"#{account_index + 1} ({username}) - Позиция [{account_index}]")
        logger.debug(f"[ProcessManager] Окно: {window_position}")
        logger.debug(f"[ProcessManager] Разрешение: {config.CS_RESOLUTION}")
        logger.debug(f"[ProcessManager] Параметры: {' '.join(launch_params[:5])}...")
        
        # ✅ ЗАПУСК С ПАРАМЕТРАМИ ДЛЯ КАЖДОГО АККАУНТА
        process, pid = self.steam_launcher.launch_steam(
            username=username,
            ipc_name=ipc_name,
            steam_id=steam_id,
            launch_params=launch_params
        )
        
        if not pid:
            logger.error("[ProcessManager] Не удалось запустить Steam")
            return None, None

        # HIGH PRIORITY для каждого
        if config.HIGH_PRIORITY:
            time.sleep(1)
            self.set_high_priority(pid)
        
        # PROCESS AFFINITY для каждого
        if config.PROCESS_AFFINITY:
            time.sleep(1)
            self.set_process_affinity(pid, [0, 1, 2, 3])

        time.sleep(10)
        
        if not psutil.pid_exists(pid):
            logger.error("Steam процесс умер")
            return None, None
        
        self.steam_instances[account_id] = {
            'process': process,
            'pid': pid,
            'ipc': ipc_name,
            'username': username,
            'window_position': window_position,
            'account_index': account_index,
            'start_time': datetime.now(),
            'params_applied': launch_params  # ✅ Запись применённых параметров
        }
        
        return process, pid

    def wait_for_cs2_and_close_library(self, account_id: int, timeout: int = 180) -> bool:
        logger.step("Ожидание", f"CS2 для аккаунта {account_id}...")
        logger.info(f"Ожидание загрузки: {config.CS2_LOAD_SECONDS}s")
        
        load_seconds = config.CS2_LOAD_SECONDS if config.WAIT_CS2_LOAD else 0
        success, cs2_pid = self.cs2_waiter.wait_for_new_cs2_process(
            timeout=timeout,
            load_seconds=load_seconds
        )
        
        if not success:
            logger.error(f"CS2 не загрузился для аккаунта {account_id}")
            return False
        
        account_index = self.account_positions.get(account_id, 0)
        window_position = self.get_account_window_position(account_index)
        
        self.cs2_instances[account_id] = {
            'pid': cs2_pid,
            'window_position': window_position,
            'account_index': account_index,
            'load_time': datetime.now()
        }
        
        logger.info(f"[ProcessManager] Аккаунт {account_id} → Позиция [{account_index}] → {window_position}")
        
        # HIGH PRIORITY для каждого CS2
        if config.HIGH_PRIORITY:
            self.set_high_priority(cs2_pid)
        
        # PROCESS AFFINITY для каждого CS2
        if config.PROCESS_AFFINITY:
            time.sleep(1)
            self.set_process_affinity(cs2_pid, [0, 1, 2, 3])
        
        # BES для каждого CS2
        if config.BES_AUTO_APPLY:
            time.sleep(2)
            bes_success = self.bes.apply_to_cs2_fast(cs2_pid, config.BES_CPU_LIMIT)
            
            if config.LOG_BES_APPLICATION:
                if bes_success:
                    logger.success(f"BES применён к PID {cs2_pid}")
                else:
                    logger.warning(f"BES не применён к PID {cs2_pid}")
        
        # ЗАКРЫТИЕ БИБЛИОТЕКИ
        if config.FORCE_CLOSE_LIBRARY:
            logger.step("Закрытие", "библиотек Steam...")
            self.library_killer.close_all_guaranteed(timeout=20)
            
            if not self.library_killer.wait_for_no_libraries(timeout=20):
                logger.warning("Библиотеки не закрылись полностью")
            else:
                logger.success("Библиотеки закрыты")
        
        # ПОЗИЦИОНИРОВАНИЕ (5 попыток)
        time.sleep(3)
        logger.step("Позиционирование", f"окна [{account_index}]...")
        
        if self.window_manager.position_cs2_window(account_index, timeout=config.TIMEOUT_WINDOW_POSITION):
            logger.success(f"Окно [{account_index}] позиционировано: {window_position}")
        else:
            logger.warning(f"Не удалось позиционировать окно [{account_index}]")
        
        logger.success(f"Аккаунт {account_id} полностью готов (позиция [{account_index}])")
        return True

    def verify_all_windows(self) -> Dict[int, bool]:
        return self.window_manager.verify_all_windows()
    
    def reposition_failed_windows(self) -> int:
        return self.window_manager.reposition_failed_windows()

    def find_login_window(self, timeout: int = 60) -> Optional[int]:
        return self.finder.find_steam_login(timeout)

    def find_library_window(self, timeout: int = 90) -> Optional[int]:
        return self.finder.find_steam_library(timeout)

    def find_cs2_window(self, timeout: int = 120) -> Optional[int]:
        return self.finder.find_cs2_window(timeout)

    def activate_window(self, hwnd: int) -> bool:
        return self.finder.activate_window(hwnd)

    def position_window(self, hwnd: int, x: int, y: int, width: int = None, height: int = None) -> bool:
        if width is None:
            width = config.CS_WIDTH
        if height is None:
            height = config.CS_HEIGHT
        return self.finder.position_window(hwnd, x, y, width, height)

    def get_account_window_position(self, account_index: int) -> tuple:
        col = account_index % 2
        row = account_index // 2
        x = col * config.WINDOW_OFFSET_X
        y = row * config.WINDOW_OFFSET_Y
        logger.debug(f"[ProcessManager] Позиция [{account_index}]: ({x}, {y})")
        return (x, y)

    def kill_all_instances(self):
        logger.step("Завершение", "...")
        self.bes.remove_all_limits()
        self.kill_all_cs2()
        if not config.KEEP_STEAM_RUNNING:
            self.kill_all_steam()
        else:
            logger.info("Steam оставлен запущенным")
        self.steam_instances.clear()
        self.cs2_instances.clear()
        self.account_positions.clear()
        self.instance_count = 0
        logger.success("Все процессы завершены")
    
    def get_status_report(self) -> Dict:
        return {
            'uptime': self.get_uptime(),
            'steam_instances': len(self.steam_instances),
            'cs2_instances': len(self.cs2_instances),
            'total_cs2_processes': self.get_total_cs2_count(),
            'bes_applied': self.bes.get_applied_count(),
            'windows_positioned': len(self.window_manager.get_all_positioned()),
            'account_positions': self.account_positions
        }


process_manager = ProcessManager()