"""
Avast Sandbox Manager - ЗАПУСК В AVAST SANDBOX
Как в FSM Panel
"""
import subprocess
import time
import os
import psutil
from typing import Optional, List, Dict

from . import config


class AvastSandboxManager:
    def __init__(self):
        self.avast_path = self._find_avast()
        self.instances: Dict[int, Dict] = {}
        
    def _find_avast(self) -> Optional[str]:
        for path in config.AVAST_PATHS:
            if os.path.exists(path):
                print(f"[Avast] ✅ Найден: {path}")
                return path
        print(f"[Avast] ❌ Не найден")
        return None
    
    def check_avast(self) -> bool:
        if self.avast_path:
            return True
        print(f"[Avast] ⚠️ Установите Avast Free Antivirus")
        print(f"[Avast] 🔗 https://www.avast.com/free-antivirus-download")
        return False
    
    def run_in_sandbox(
        self,
        account_id: int,
        command: List[str],
        cwd: str = None
    ) -> Optional[subprocess.Popen]:
        """Запуск программы в Avast Sandbox"""
        if not self.avast_path:
            return None
        
        # Avast Sandbox команда
        cmd = [self.avast_path, "/sandbox"] + command
        
        try:
            print(f"[Avast] 🚀 Запуск в Sandbox: {command[0]}")
            
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            )
            
            return process
        except Exception as e:
            print(f"[Avast] ❌ Ошибка: {e}")
            return None
    
    def run_steam_in_sandbox(
        self,
        account_id: int,
        steam_path: str,
        steam_args: List[str],
        cwd: str = None
    ) -> Optional[subprocess.Popen]:
        """Запуск Steam в Avast Sandbox"""
        if not self.avast_path:
            return None
        
        # Команда: AvastUI.exe /sandbox steam.exe [параметры]
        cmd = [self.avast_path, "/sandbox", steam_path] + steam_args
        
        try:
            print(f"[Avast] 🖥️ Запуск Steam в Sandbox...")
            
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            )
            
            return process
        except Exception as e:
            print(f"[Avast] ❌ Ошибка: {e}")
            return None
    
    def run_cs2_in_sandbox(
        self,
        account_id: int,
        steam_path: str,
        cs2_args: List[str],
        cwd: str = None
    ) -> Optional[subprocess.Popen]:
        """Запуск CS2 в Avast Sandbox (через Steam)"""
        if not self.avast_path:
            return None
        
        # Запуск через Steam в той же песочнице
        cmd = [self.avast_path, "/sandbox", steam_path, "-applaunch", "730"] + cs2_args
        
        try:
            print(f"[Avast] 🎮 Запуск CS2 в Sandbox...")
            
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            )
            
            return process
        except Exception as e:
            print(f"[Avast] ❌ Ошибка: {e}")
            return None
    
    def terminate_all(self):
        """Завершение всех процессов в Sandbox"""
        print("[Avast] 🛑 Завершение...")
        # Avast автоматически завершает при закрытии
        self.instances.clear()