#!/usr/bin/env python3
import subprocess
import time
import os
import urllib.parse
import psutil
from typing import Optional, List, Tuple

class ProcessManager:
    """Менеджер процессов для управления Steam и CS2"""
    
    # Параметры запуска Steam (минимальные, чтобы не мешать работе)
    STEAM_LAUNCH_OPTIONS = [
        "-nofriendsui",
        "-noreactlogin",
        "-no-cef-sandbox"
    ]
    
    # Параметры запуска CS2 (оптимизированные для фарма)
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
        "+violence_hblood", "0"
    ]

    @staticmethod
    def find_steam_path() -> Optional[str]:
        """
        Поиск пути к steam.exe
        Возвращает полный путь или None если не найден
        """
        # Стандартные пути установки
        paths = [
            r"C:\Program Files (x86)\Steam\steam.exe",
            r"C:\Program Files\Steam\steam.exe",
            r"D:\Steam\steam.exe",
            r"E:\Steam\steam.exe",
        ]
        
        # Проверка из реестра Windows
        try:
            import winreg
            # Пробуем HKLM
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam") as key:
                    steam_path = winreg.QueryValueEx(key, "SteamPath")[0]
                    steam_exe = os.path.join(steam_path, "steam.exe")
                    if os.path.exists(steam_exe):
                        print(f"[ProcessManager] ✅ Steam найден в реестре: {steam_exe}")
                        return steam_exe
            except FileNotFoundError:
                pass
            
            # Пробуем HKCU
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Valve\Steam") as key:
                    steam_path = winreg.QueryValueEx(key, "SteamPath")[0]
                    steam_exe = os.path.join(steam_path, "steam.exe")
                    if os.path.exists(steam_exe):
                        print(f"[ProcessManager] ✅ Steam найден в реестре (HKCU): {steam_exe}")
                        return steam_exe
            except FileNotFoundError:
                pass
        except Exception as e:
            print(f"[ProcessManager] ⚠️ Ошибка чтения реестра: {e}")
        
        # Проверка стандартных путей
        for path in paths:
            if os.path.exists(path):
                print(f"[ProcessManager] ✅ Steam найден: {path}")
                return path
        
        print(f"[ProcessManager] ❌ Steam не найден ни в одном из стандартных расположений")
        return None

    @staticmethod
    def kill_all_steam():
        """Завершение всех процессов Steam"""
        print("[ProcessManager] Завершение всех процессов Steam...")
        os.system("taskkill /f /im steam.exe 2>nul")
        os.system("taskkill /f /im steamwebhelper.exe 2>nul")
        time.sleep(3)
        print("[ProcessManager] ✅ Процессы Steam завершены")

    @staticmethod
    def is_steam_running() -> bool:
        """Проверка, запущен ли Steam"""
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == 'steam.exe':
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

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
        """
        Запуск CS2 через Steam с корректными параметрами.
        
        Args:
            steam_path: Путь к steam.exe
            ipc_name: Имя IPC для изоляции экземпляра Steam (для мультиаккаунта)
            steam_data_dir: Папка данных Steam для этого аккаунта
            
        Returns:
            True при успешном запуске команды
        """
        try:
            steam_dir = os.path.dirname(steam_path)
            
            if ipc_name and steam_data_dir:
                # === ЗАПУСК ЧЕРЕЗ STEAM С ПАРАМЕТРАМИ ИЗОЛЯЦИИ ===
                print(f"[ProcessManager] 🎮 Запуск CS2 через Steam с IPC: {ipc_name}")
                cmd = [
                    steam_path,
                    "-master_ipc_name_override", ipc_name,
                    "-fulldir", steam_data_dir,
                    "-applaunch", "730"
                ] + ProcessManager.CS2_LAUNCH_OPTIONS
                
                print(f"[ProcessManager] Команда: {' '.join(cmd)}")
                subprocess.Popen(cmd, cwd=steam_dir, 
                               creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                print(f"[ProcessManager] ✅ CS2 запущен через Steam с параметрами изоляции")
                return True
            else:
                # === ПРОСТОЙ ЗАПУСК ЧЕРЕЗ STEAM URI ===
                print(f"[ProcessManager] 🎮 Запуск CS2 через Steam URI")
                params = " ".join(ProcessManager.CS2_LAUNCH_OPTIONS)
                encoded_params = urllib.parse.quote(params)
                steam_uri = f"steam://rungameid/730/{encoded_params}"
                
                # Используем os.startfile для правильного handling URI
                os.startfile(steam_uri)
                print(f"[ProcessManager] ✅ CS2 запущен через URI: {steam_uri}")
                return True
                
        except Exception as e:
            print(f"[ProcessManager] ❌ Ошибка запуска CS2 через Steam: {e}")
            # Фолбэк: прямой запуск cs2.exe
            return ProcessManager._fallback_launch(steam_path)

    @staticmethod
    def _fallback_launch(steam_path: str) -> bool:
        """
        Резервный метод запуска через прямой вызов cs2.exe
        Используется если запуск через Steam не удался
        """
        try:
            steam_dir = os.path.dirname(steam_path)
            cs2_exe = os.path.join(
                steam_dir, "steamapps", "common", 
                "Counter-Strike Global Offensive", "game", "bin", "win64", "cs2.exe"
            )
            
            if os.path.exists(cs2_exe):
                print(f"[ProcessManager] 🎮 Фолбэк: прямой запуск cs2.exe")
                cmd = [cs2_exe] + ProcessManager.CS2_LAUNCH_OPTIONS
                subprocess.Popen(cmd, cwd=os.path.dirname(cs2_exe),
                               creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                print(f"[ProcessManager] ✅ CS2 запущен напрямую")
                return True
            else:
                print(f"[ProcessManager] ❌ cs2.exe не найден: {cs2_exe}")
                
        except Exception as e:
            print(f"[ProcessManager] ❌ Фолбэк-запуск не удался: {e}")
        
        return False

    @staticmethod
    def kill_all():
        """Завершение всех процессов CS2"""
        print("[ProcessManager] Завершение всех процессов CS2...")
        os.system("taskkill /f /im cs2.exe 2>nul")
        time.sleep(2)
        print("[ProcessManager] ✅ Процессы CS2 завершены")

    @staticmethod
    def wait_for_cs2(timeout: int = 60, check_interval: int = 2) -> bool:
        """
        Ожидание появления процесса CS2
        
        Args:
            timeout: Максимальное время ожидания в секундах
            check_interval: Интервал между проверками в секундах
            
        Returns:
            True если CS2 запущен, False если таймаут
        """
        print(f"[ProcessManager] ⏳ Ожидание запуска CS2 (таймаут {timeout} сек)...")
        start_time = time.time()
        attempt = 0
        
        while time.time() - start_time < timeout:
            attempt += 1
            pids = ProcessManager.get_cs2_pids()
            if pids:
                print(f"[ProcessManager] ✅ CS2 обнаружен на попытке {attempt} (PID: {pids})")
                return True
            print(f"[ProcessManager] Попытка {attempt}: CS2 ещё не запущен...")
            time.sleep(check_interval)
        
        print(f"[ProcessManager] ❌ CS2 не запущен за {timeout} секунд")
        return False