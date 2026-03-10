"""
Process Manager - BES ПО КНОПКЕ + ПОЗИЦИОНИРОВАНИЕ ПОСЛЕ ВСЕХ
"""
import subprocess
import time
import os
import random
import psutil
import win32gui
import win32con
from typing import Optional, Dict, Tuple, List
from datetime import datetime

from . import config
from .window_finder import WindowFinder
from .bes_manager import BESManager
from .library_killer import LibraryKiller
from .cs2_waiter import CS2Waiter
from .window_manager import WindowManager
from .steam_launcher import SteamLauncher
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
        self.optimized = False
        self.start_time = datetime.now()
        self.all_accounts_launched = False  # ✅ Флаг что все запущены
    
    def optimize_once(self):
        if not self.optimized:
            logger.step("Оптимизация", "...")
            from .steam_library_optimizer import SteamLibraryOptimizer
            optimizer = SteamLibraryOptimizer()
            optimizer.optimize_library_load()
            self.optimized = True
            logger.success("Оптимизация завершена")
    
    def clear_cs2_tracker(self):
        self.cs2_waiter.clear_known_pids()
        self.window_manager.clear_all_positions()
        if getattr(config, 'RESET_WINDOW_POSITION_ON_START', True):
            self.account_positions.clear()
            self.instance_count = 0
        self.all_accounts_launched = False
    
    def get_total_cs2_count(self) -> int:
        return self.cs2_waiter.get_total_cs2_count()
    
    def get_next_account_index(self) -> int:
        index = self.instance_count % 4
        self.instance_count += 1
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

    def kill_all_cs2(self):
        os.system("taskkill /f /im cs2.exe 2>nul")
        time.sleep(2)

    def set_high_priority(self, pid: int) -> bool:
        try:
            process = psutil.Process(pid)
            process.nice(psutil.HIGH_PRIORITY_CLASS)
            return True
        except:
            return False

    def set_process_affinity(self, pid: int, cores: list = [0, 1, 2, 3]) -> bool:
        try:
            process = psutil.Process(pid)
            process.cpu_affinity(cores)
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
        
        launch_params = list(getattr(config, 'CS2_LAUNCH_OPTIONS', []))
        
        if window_position and window_position != (0, 0):
            launch_params.extend(["+setpos", str(window_position[0]), str(window_position[1]), "0"])
        
        logger.step("Запуск", f"#{account_index + 1} ({username})")
        logger.info(f"[ProcessManager] Параметры ({len(launch_params)}): {' '.join(launch_params[:5])}...")
        
        process, pid = self.steam_launcher.launch_steam(
            username=username,
            ipc_name=ipc_name,
            steam_id=steam_id,
            launch_params=launch_params
        )
        
        if not pid:
            return None, None

        if getattr(config, 'HIGH_PRIORITY', True):
            time.sleep(1)
            self.set_high_priority(pid)
        
        if getattr(config, 'PROCESS_AFFINITY', True):
            time.sleep(1)
            self.set_process_affinity(pid, [0, 1, 2, 3])

        time.sleep(10)
        
        if not psutil.pid_exists(pid):
            return None, None
        
        self.steam_instances[account_id] = {
            'process': process,
            'pid': pid,
            'ipc': ipc_name,
            'username': username,
            'window_position': window_position,
            'account_index': account_index,
            'start_time': datetime.now(),
        }
        
        return process, pid

    def wait_for_cs2_and_close_library(self, account_id: int, timeout: int = 180) -> bool:
        logger.step("Ожидание", f"CS2 для аккаунта {account_id}...")
        
        load_seconds = getattr(config, 'CS2_LOAD_SECONDS', 25)
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
            'bes_applied': False  # ✅ BES не применён автоматически
        }
        
        if getattr(config, 'HIGH_PRIORITY', True):
            self.set_high_priority(cs2_pid)
        
        if getattr(config, 'PROCESS_AFFINITY', True):
            time.sleep(1)
            self.set_process_affinity(cs2_pid, [0, 1, 2, 3])
        
        # ✅ BES НЕ ПРИМЕНЯЕТСЯ АВТОМАТИЧЕСКИ
        logger.info(f"[ProcessManager] BES не применён (ожидание кнопки)")
        
        # ✅ ЗАКРЫТИЕ БИБЛИОТЕКИ
        if getattr(config, 'FORCE_CLOSE_LIBRARY', True):
            logger.step("Закрытие", "библиотек...")
            self.library_killer.close_all_guaranteed(timeout=20)
            self.library_killer.wait_for_no_libraries(timeout=20)
            logger.success("Библиотеки закрыты")
        
        # ✅ ПОЗИЦИОНИРОВАНИЕ ТОЛЬКО ПОСЛЕ ВСЕХ
        if not getattr(config, 'POSITION_WINDOWS_AFTER_ALL_LAUNCHED', False):
            time.sleep(3)
            self.position_cs2_window(account_id, window_position)
        
        logger.success(f"Аккаунт {account_id} готов")
        return True

    def mark_all_accounts_launched(self, total_accounts: int):
        """
        ✅ ОТМЕТИТЬ ЧТО ВСЕ АККАУНТЫ ЗАПУЩЕНЫ
        """
        self.all_accounts_launched = True
        logger.info(f"[ProcessManager] Все {total_accounts} аккаунтов запущены")

    def position_all_windows_after_launch(self, total_accounts: int):
        """
        ✅ ПОЗИЦИОНИРОВАНИЕ ВСЕХ ОКОН ПОСЛЕ ЗАПУСКА ВСЕХ АККАУНТОВ
        """
        if not self.all_accounts_launched:
            logger.warning("[ProcessManager] Не все аккаунты запущены, ожидание...")
            return
        
        logger.info(f"[ProcessManager] Позиционирование {total_accounts} окон...")
        time.sleep(5)
        
        for account_id, cs2_info in self.cs2_instances.items():
            window_position = cs2_info.get('window_position', (0, 0))
            account_index = cs2_info.get('account_index', 0)
            
            logger.step("Позиционирование", f"окна [{account_index}]...")
            
            if self.window_manager.position_cs2_window(account_index, timeout=30):
                logger.success(f"Окно [{account_index}] позиционировано: {window_position}")
            else:
                logger.warning(f"Не удалось позиционировать окно [{account_index}]")
        
        logger.success(f"Все {total_accounts} окон позиционированы")

    def apply_bes_to_account(self, account_id: int) -> bool:
        """
        ✅ ПРИМЕНИТЬ BES К КОНКРЕТНОМУ АККАУНТУ (по кнопке)
        """
        if account_id not in self.cs2_instances:
            logger.error(f"[ProcessManager] Аккаунт {account_id} не найден")
            return False
        
        cs2_info = self.cs2_instances[account_id]
        cs2_pid = cs2_info.get('pid')
        
        if not cs2_pid:
            logger.error(f"[ProcessManager] PID не найден для аккаунта {account_id}")
            return False
        
        # Применяем BES
        bes_limit = getattr(config, 'BES_CPU_LIMIT', 25)
        success = self.bes.apply_to_cs2_fast(cs2_pid, bes_limit)
        
        if success:
            cs2_info['bes_applied'] = True
            logger.success(f"[ProcessManager] BES применён к аккаунту {account_id} (PID: {cs2_pid})")
        else:
            logger.error(f"[ProcessManager] BES не применён к аккаунту {account_id}")
        
        return success

    def is_bes_applied(self, account_id: int) -> bool:
        """Проверить применён ли BES"""
        if account_id not in self.cs2_instances:
            return False
        return self.cs2_instances[account_id].get('bes_applied', False)

    def position_cs2_window(self, account_id: int, window_position: tuple) -> bool:
        cs2_window = self.finder.find_cs2_window(timeout=30)
        if cs2_window:
            x, y = window_position
            return self.finder.position_window(cs2_window, x, y, getattr(config, 'CS_WIDTH', 360), getattr(config, 'CS_HEIGHT', 270))
        return False

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
            width = getattr(config, 'CS_WIDTH', 360)
        if height is None:
            height = getattr(config, 'CS_HEIGHT', 270)
        return self.finder.position_window(hwnd, x, y, width, height)

    def get_account_window_position(self, account_index: int) -> tuple:
        """
        ✅ СЕТКА 2x2 С УЧЁТОМ UI (окна не перекрывают программу)
        Программа справа, окна слева
        """
        col = account_index % 2
        row = account_index // 2
        # ✅ ОКНА СЛЕВА (не перекрывают UI который справа)
        x = col * getattr(config, 'WINDOW_OFFSET_X', 360)
        y = row * getattr(config, 'WINDOW_OFFSET_Y', 270)
        return (x, y)

    def kill_all_instances(self):
        logger.step("Завершение", "...")
        self.bes.remove_all_limits()
        self.kill_all_cs2()
        if not getattr(config, 'KEEP_STEAM_RUNNING', True):
            self.kill_all_steam()
        self.steam_instances.clear()
        self.cs2_instances.clear()
        self.account_positions.clear()
        self.instance_count = 0
        self.all_accounts_launched = False
        logger.success("Все завершено")
    
    def get_system_load(self) -> Dict:
        """Получить нагрузку системы"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            memory = psutil.virtual_memory()
            
            cs2_loads = []
            for acc_id, cs2_info in self.cs2_instances.items():
                pid = cs2_info.get('pid')
                if pid:
                    try:
                        proc = psutil.Process(pid)
                        cs2_loads.append({
                            'account_id': acc_id,
                            'pid': pid,
                            'cpu': proc.cpu_percent(interval=0.1),
                            'memory': proc.memory_info().rss // 1024 // 1024,
                            'threads': proc.num_threads(),
                            'bes_applied': cs2_info.get('bes_applied', False)
                        })
                    except:
                        pass
            
            return {
                'cpu': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_gb': memory.used // 1024 // 1024 // 1024,
                'memory_total_gb': memory.total // 1024 // 1024 // 1024,
                'cs2_processes': len(cs2_loads),
                'cs2_loads': cs2_loads
            }
        except:
            return {}


process_manager = ProcessManager()