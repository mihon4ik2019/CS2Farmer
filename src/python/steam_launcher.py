"""
Steam Launcher - ПАРАМЕТРЫ ДЛЯ КАЖДОГО АККАУНТА
Исправление: каждый аккаунт получает СВОИ параметры
"""
import os
import subprocess
import time
import ctypes
from typing import Optional, Tuple, List

from . import config
from .logger import SecureLogger

logger = SecureLogger()


def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


class SteamLauncher:
    def __init__(self):
        self.steam_data_base = getattr(config, 'STEAM_DATA_DIR', './steam_data')
        self.steam_path = self._find_steam_path()
        os.makedirs(self.steam_data_base, exist_ok=True)
        
        if not is_admin():
            logger.warning("[SteamLauncher] ⚠️ Запущено НЕ от администратора!")
    
    def get_steam_data_path(self, username: str) -> str:
        safe_username = "".join(c for c in username if c.isalnum() or c in ('-', '_')).rstrip()
        return os.path.join(self.steam_data_base, f"steam_{safe_username}")
    
    def prepare_steam_data(self, username: str) -> str:
        steam_data_path = self.get_steam_data_path(username)
        os.makedirs(steam_data_path, exist_ok=True)
        os.makedirs(os.path.join(steam_data_path, 'config'), exist_ok=True)
        os.makedirs(os.path.join(steam_data_path, 'steamapps'), exist_ok=True)
        logger.info(f"[SteamLauncher] Данные: {steam_data_path}")
        return steam_data_path
    
    def fix_steam_service(self) -> bool:
        if not getattr(config, 'FIX_STEAM_SERVICE', False):
            return False
        
        try:
            subprocess.run(['sc', 'stop', 'SteamService'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            time.sleep(2)
            subprocess.run(['sc', 'start', 'SteamService'], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            logger.info("[SteamLauncher] Steam Service перезапущен")
            return True
        except:
            return False
    
    def launch_steam(
        self,
        username: str,
        ipc_name: str,
        steam_id: int = None,
        launch_params: list = None
    ) -> Tuple[Optional[subprocess.Popen], Optional[int]]:
        """
        ✅ ЗАПУСК С ОТДЕЛЬНЫМИ ПАРАМЕТРАМИ ДЛЯ КАЖДОГО АККАУНТА
        """
        if not self.steam_path:
            logger.error("Steam не найден")
            return None, None
        
        if getattr(config, 'FIX_STEAM_SERVICE', False):
            self.fix_steam_service()
        
        # ✅ ОТДЕЛЬНЫЕ ДАННЫЕ ДЛЯ КАЖДОГО
        steam_data_path = self.prepare_steam_data(username)
        unique_id = steam_id if steam_id else int(time.time() * 1000) % 100000
        
        # ✅ НОВАЯ КОМАНДА ДЛЯ КАЖДОГО АККАУНТА
        cmd = [
            self.steam_path,
            "-master_ipc_name_override", ipc_name,
            "-fulldir", steam_data_path,
            "-id", str(unique_id),
        ]
        
        # ✅ КОПИЯ ПАРАМЕТРОВ STEAM
        steam_opts = list(getattr(config, 'STEAM_LAUNCH_OPTIONS', []))
        cmd.extend(steam_opts)
        
        # ✅ -applaunch 730
        cmd.extend(["-applaunch", "730"])
        
        # ✅ КОПИЯ ПАРАМЕТРОВ CS2 (не ссылка!)
        if launch_params:
            cs2_opts = list(launch_params)  # ✅ НОВАЯ КОПИЯ
            cmd.extend(cs2_opts)
            logger.info(f"[SteamLauncher] CS2 параметры ({len(cs2_opts)}): {' '.join(cs2_opts[:5])}...")
        else:
            logger.warning("[SteamLauncher] ⚠️ Параметры CS2 не переданы!")
        
        if getattr(config, 'DISABLE_STEAM_OVERLAY', True):
            cmd.append("-nooverlay")
        
        try:
            logger.info(f"[SteamLauncher] Запуск для {username}")
            logger.info(f"[SteamLauncher] Данные: {steam_data_path}")
            logger.info(f"[SteamLauncher] IPC: {ipc_name}")
            
            process = subprocess.Popen(
                cmd,
                cwd=os.path.dirname(self.steam_path),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            )
            
            pid = process.pid
            logger.success(f"[SteamLauncher] Steam PID: {pid}")
            
            time.sleep(8)
            
            if not self._is_process_running(pid):
                logger.error("[SteamLauncher] Steam умер")
                return None, None
            
            return process, pid
            
        except Exception as e:
            logger.error(f"[SteamLauncher] Ошибка: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    def _find_steam_path(self) -> Optional[str]:
        paths = [
            r"C:\Program Files (x86)\Steam\steam.exe",
            r"C:\Program Files\Steam\steam.exe",
            os.path.expandvars(r"%ProgramFiles(x86)%\Steam\steam.exe"),
        ]
        for path in paths:
            if os.path.exists(path):
                logger.success(f"[SteamLauncher] Steam: {path}")
                return path
        return None
    
    def _is_process_running(self, pid: int) -> bool:
        try:
            import psutil
            return psutil.pid_exists(pid)
        except:
            return False


steam_launcher = SteamLauncher()