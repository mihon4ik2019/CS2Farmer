"""
Steam Launcher - ПАРАМЕТРЫ ДЛЯ КАЖДОГО АККАУНТА
Исправление: каждый аккаунт получает свои параметры
"""
import os
import subprocess
import time
import shutil
from typing import Optional, Tuple, List

from . import config
from .logger import SecureLogger

logger = SecureLogger()


class SteamLauncher:
    """ЗАПУСК STEAM С ОТДЕЛЬНЫМИ ДАННЫМИ ДЛЯ КАЖДОГО АККАУНТА"""
    
    def __init__(self):
        self.steam_data_base = config.STEAM_DATA_DIR
        self.steam_path = self._find_steam_path()
        os.makedirs(self.steam_data_base, exist_ok=True)
    
    def get_steam_data_path(self, username: str) -> str:
        """Получить путь к данным Steam для аккаунта"""
        safe_username = "".join(c for c in username if c.isalnum() or c in ('-', '_')).rstrip()
        return os.path.join(self.steam_data_base, f"steam_{safe_username}")
    
    def prepare_steam_data(self, username: str) -> str:
        """Подготовка данных Steam"""
        steam_data_path = self.get_steam_data_path(username)
        
        os.makedirs(steam_data_path, exist_ok=True)
        os.makedirs(os.path.join(steam_data_path, 'config'), exist_ok=True)
        os.makedirs(os.path.join(steam_data_path, 'steamapps'), exist_ok=True)
        
        logger.debug(f"[SteamLauncher] Данные Steam: {steam_data_path}")
        return steam_data_path
    
    def fix_steam_service(self) -> bool:
        """
        ✅ ИСПРАВЛЕНИЕ STEAM SERVICE ERROR
        """
        if not config.FIX_STEAM_SERVICE:
            return False
        
        logger.info("[SteamLauncher] Проверка Steam Service...")
        
        try:
            # Метод 1: Перезапуск службы
            subprocess.run(
                ['sc', 'stop', 'SteamService'],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            time.sleep(2)
            subprocess.run(
                ['sc', 'start', 'SteamService'],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            logger.info("[SteamLauncher] Steam Service перезапущен")
            return True
            
        except Exception as e:
            logger.debug(f"[SteamLauncher] Ошибка Steam Service: {e}")
            
            # Метод 2: Переустановка службы
            try:
                if os.path.exists(config.STEAM_SERVICE_PATH):
                    subprocess.run(
                        [config.STEAM_SERVICE_PATH, '/install'],
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    logger.info("[SteamLauncher] Steam Service переустановлен")
                    return True
            except:
                pass
        
        return False
    
    def launch_steam(
        self,
        username: str,
        ipc_name: str,
        steam_id: int = None,
        launch_params: list = None
    ) -> Tuple[Optional[subprocess.Popen], Optional[int]]:
        """
        ✅ ЗАПУСК STEAM + CS2 С ПАРАМЕТРАМИ ДЛЯ КАЖДОГО АККАУНТА
        """
        if not self.steam_path:
            logger.error("Steam не найден")
            return None, None
        
        # ✅ ИСПРАВЛЕНИЕ STEAM SERVICE
        if config.FIX_STEAM_SERVICE:
            self.fix_steam_service()
        
        # Подготовка отдельных данных
        steam_data_path = self.prepare_steam_data(username)
        
        unique_id = steam_id if steam_id else int(time.time() * 1000) % 100000
        
        # ✅ ВАЖНО: Параметры для КАЖДОГО аккаунта
        cmd = [
            self.steam_path,
            "-master_ipc_name_override", ipc_name,
            "-fulldir", steam_data_path,
            "-id", str(unique_id),
        ]
        
        # Параметры Steam (для каждого аккаунта)
        steam_opts = config.STEAM_LAUNCH_OPTIONS.copy()
        cmd.extend(steam_opts)
        logger.debug(f"[SteamLauncher] Steam параметры: {' '.join(steam_opts[:3])}...")
        
        # ✅ ОБЯЗАТЕЛЬНО: -applaunch 730 (для каждого аккаунта)
        cmd.extend(["-applaunch", "730"])
        
        # Параметры CS2 (для каждого аккаунта)
        if launch_params:
            cmd.extend(launch_params)
            logger.debug(f"[SteamLauncher] CS2 параметры: {' '.join(launch_params[:5])}...")
        
        if config.DISABLE_STEAM_OVERLAY:
            cmd.append("-nooverlay")
        
        try:
            logger.info(f"[SteamLauncher] Запуск Steam для {username}")
            logger.debug(f"[SteamLauncher] Данные: {steam_data_path}")
            logger.debug(f"[SteamLauncher] Команда: steam.exe -applaunch 730 {' '.join(launch_params[:5] if launch_params else [])}...")
            
            # ✅ ВАЖНО: Отдельный процесс для каждого аккаунта
            process = subprocess.Popen(
                cmd,
                cwd=os.path.dirname(self.steam_path),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            )
            
            pid = process.pid
            logger.success(f"[SteamLauncher] Steam PID: {pid}")
            
            # Ждём пока Steam запустится
            time.sleep(8)
            
            if not self._is_process_running(pid):
                logger.error("[SteamLauncher] Steam процесс умер")
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
                logger.success(f"[SteamLauncher] Steam найден: {path}")
                return path
        logger.error("[SteamLauncher] Steam не найден!")
        return None
    
    def _is_process_running(self, pid: int) -> bool:
        try:
            import psutil
            return psutil.pid_exists(pid)
        except:
            return False


steam_launcher = SteamLauncher()