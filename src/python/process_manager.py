#!/usr/bin/env python3
import subprocess
import time
import os
import urllib.parse
import psutil
from typing import Optional, List
from .logger import SecureLogger

logger = SecureLogger()

class ProcessManager:
    """Менеджер процессов для управления Steam и CS2"""
    
    STEAM_LAUNCH_OPTIONS = [
        "-nofriendsui",
        "-noreactlogin",
        "-no-cef-sandbox",
        "-silent",
        "-tcp"
    ]
    
    CS2_LAUNCH_OPTIONS = [
        "-windowed",
        "-w", "640",
        "-h", "480",
        "-novid",
        "-nojoy",
        "-nosound",
        "-noborder",
        "+engine_no_focus_sleep", "120",
        "+mat_disable_fancy_blending", "1",
        "+r_dynamic", "0",
        "+violence_hblood", "0",
        "-high"
    ]

    @staticmethod
    def find_steam_path() -> Optional[str]:
        """Поиск пути к steam.exe"""
        paths = [
            r"C:\Program Files (x86)\Steam\steam.exe",
            r"C:\Program Files\Steam\steam.exe",
            r"D:\Steam\steam.exe",
            r"E:\Steam\steam.exe",
        ]
        
        try:
            import winreg
            for key_path in [r"SOFTWARE\Valve\Steam", r"SOFTWARE\WOW6432Node\Valve\Steam"]:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                        steam_path = winreg.QueryValueEx(key, "SteamPath")[0]
                        steam_exe = os.path.join(steam_path, "steam.exe")
                        if os.path.exists(steam_exe):
                            logger.info(f"[ProcessManager] ✅ Steam найден в реестре: {steam_exe}")
                            return steam_exe
                except FileNotFoundError:
                    continue
        except Exception as e:
            logger.error(f"[ProcessManager] ⚠️ Ошибка чтения реестра: {e}")
        
        for path in paths:
            if os.path.exists(path):
                logger.info(f"[ProcessManager] ✅ Steam найден: {path}")
                return path
        
        logger.error(f"[ProcessManager] ❌ Steam не найден")
        return None

    @staticmethod
    def kill_all_steam():
        """Завершение всех процессов Steam"""
        logger.info("[ProcessManager] Завершение всех процессов Steam...")
        os.system("taskkill /f /im steam.exe 2>nul")
        os.system("taskkill /f /im steamwebhelper.exe 2>nul")
        time.sleep(3)
        logger.info("[ProcessManager] ✅ Процессы Steam завершены")

    @staticmethod
    def is_steam_running() -> bool:
        """Проверка, запущен ли Steam"""
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == 'steam.exe':
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    @staticmethod
    def get_steam_pids() -> List[int]:
        """Получение PID всех процессов Steam"""
        pids = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == 'steam.exe':
                    pids.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return pids

    @staticmethod
    def get_cs2_pids() -> List[int]:
        """Получение PID всех процессов CS2"""
        pids = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == 'cs2.exe':
                    pids.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return pids

    @staticmethod
    def start_cs2(steam_path: str, ipc_name: Optional[str] = None, 
                  steam_data_dir: Optional[str] = None) -> bool:
        """Запуск CS2 через Steam"""
        try:
            steam_dir = os.path.dirname(steam_path)
            
            if ipc_name and steam_data_dir:
                logger.info(f"[ProcessManager] 🎮 Запуск CS2 через Steam с IPC: {ipc_name}")
                cmd = [
                    steam_path,
                    "-master_ipc_name_override", ipc_name,
                    "-fulldir", steam_data_dir,
                    "-applaunch", "730"
                ] + ProcessManager.CS2_LAUNCH_OPTIONS
                
                logger.info(f"[ProcessManager] Команда: {' '.join(cmd)}")
                subprocess.Popen(cmd, cwd=steam_dir, 
                               creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                logger.info(f"[ProcessManager] ✅ CS2 запущен через Steam")
                return True
            else:
                logger.info(f"[ProcessManager] 🎮 Запуск CS2 через Steam URI")
                params = " ".join(ProcessManager.CS2_LAUNCH_OPTIONS)
                encoded_params = urllib.parse.quote(params)
                steam_uri = f"steam://rungameid/730/{encoded_params}"
                
                os.startfile(steam_uri)
                logger.info(f"[ProcessManager] ✅ CS2 запущен через URI")
                return True
                
        except Exception as e:
            logger.error(f"[ProcessManager] ❌ Ошибка запуска CS2: {e}")
            return ProcessManager._fallback_launch(steam_path)

    @staticmethod
    def _fallback_launch(steam_path: str) -> bool:
        """Резервный метод запуска"""
        try:
            steam_dir = os.path.dirname(steam_path)
            cs2_exe = os.path.join(
                steam_dir, "steamapps", "common", 
                "Counter-Strike Global Offensive", "game", "bin", "win64", "cs2.exe"
            )
            
            if os.path.exists(cs2_exe):
                logger.info(f"[ProcessManager] 🎮 Фолбэк: прямой запуск cs2.exe")
                cmd = [cs2_exe] + ProcessManager.CS2_LAUNCH_OPTIONS
                subprocess.Popen(cmd, cwd=os.path.dirname(cs2_exe),
                               creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                logger.info(f"[ProcessManager] ✅ CS2 запущен напрямую")
                return True
            else:
                logger.error(f"[ProcessManager] ❌ cs2.exe не найден: {cs2_exe}")
                
        except Exception as e:
            logger.error(f"[ProcessManager] ❌ Фолбэк-запуск не удался: {e}")
        
        return False

    @staticmethod
    def kill_all():
        """Завершение всех процессов CS2"""
        logger.info("[ProcessManager] Завершение всех процессов CS2...")
        os.system("taskkill /f /im cs2.exe 2>nul")
        time.sleep(2)
        logger.info("[ProcessManager] ✅ Процессы CS2 завершены")

    @staticmethod
    def kill_steam_by_pid(pid: int):
        """Завершение процесса Steam по PID"""
        try:
            proc = psutil.Process(pid)
            for child in proc.children(recursive=True):
                child.terminate()
            proc.terminate()
            logger.info(f"[ProcessManager] ✅ Steam PID {pid} завершён")
            return True
        except Exception as e:
            logger.error(f"[ProcessManager] ❌ Ошибка завершения PID {pid}: {e}")
            return False

    @staticmethod
    def wait_for_cs2(timeout: int = 120, check_interval: int = 3) -> bool:
        """Ожидание появления процесса CS2"""
        logger.info(f"[ProcessManager] ⏳ Ожидание запуска CS2 (таймаут {timeout} сек)...")
        start_time = time.time()
        attempt = 0
        
        while time.time() - start_time < timeout:
            attempt += 1
            pids = ProcessManager.get_cs2_pids()
            
            if pids:
                logger.info(f"[ProcessManager] ✅ CS2 обнаружен на попытке {attempt} (PID: {pids})")
                return True
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    name = proc.info['name']
                    if name and ('cs2' in name.lower() or 'counter' in name.lower()):
                        logger.info(f"[ProcessManager] ✅ Найден процесс: {name} (PID: {proc.info['pid']})")
                        return True
                except:
                    continue
            
            if attempt % 5 == 0:
                logger.info(f"[ProcessManager] Попытка {attempt}: CS2 ещё не запущен...")
                
            time.sleep(check_interval)
        
        logger.error(f"[ProcessManager] ❌ CS2 не запущен за {timeout} секунд")
        return False

    @staticmethod
    def set_process_priority(pid: int, priority: str = "high"):
        """Установка приоритета процесса"""
        try:
            proc = psutil.Process(pid)
            priorities = {
                "low": psutil.BELOW_NORMAL_PRIORITY_CLASS,
                "normal": psutil.NORMAL_PRIORITY_CLASS,
                "high": psutil.HIGH_PRIORITY_CLASS,
                "realtime": psutil.REALTIME_PRIORITY_CLASS
            }
            proc.nice(priorities.get(priority, psutil.NORMAL_PRIORITY_CLASS))
            logger.info(f"[ProcessManager] ✅ Приоритет PID {pid} установлен: {priority}")
            return True
        except Exception as e:
            logger.warning(f"[ProcessManager] ⚠️ Не удалось установить приоритет: {e}")
            return False