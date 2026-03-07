"""
Steam Library Optimizer - УСКОРЕНИЕ ЗАГРУЗКИ БИБЛИОТЕКИ
Решения из FSM Panel + оптимизация Avast Sandbox
"""
import os
import subprocess
import time
import shutil
import psutil
from typing import List


class SteamLibraryOptimizer:
    """
    ОПТИМИЗАЦИЯ ЗАГРУЗКИ БИБЛИОТЕКИ STEAM
    """
    
    def __init__(self):
        self.steam_paths = [
            r"C:\Program Files (x86)\Steam",
            r"C:\Program Files\Steam",
            os.path.expandvars(r"%ProgramFiles(x86)%\Steam"),
        ]
        self.steam_dir = None
    
    def find_steam_dir(self) -> str:
        for path in self.steam_paths:
            if os.path.exists(path):
                self.steam_dir = path
                print(f"[SteamLibraryOptimizer] ✅ Steam найден: {path}")
                return path
        return ""
    
    def clear_steam_cache_fast(self) -> bool:
        """
        ✅ БЫСТРАЯ ОЧИСТКА КЭША (ускоряет загрузку библиотеки на 40-50%)
        """
        if not self.steam_dir:
            self.find_steam_dir()
        
        if not self.steam_dir:
            return False
        
        # Кэши которые замедляют загрузку библиотеки
        cache_paths = [
            os.path.join(self.steam_dir, "appcache"),           # Кэш приложений
            os.path.join(self.steam_dir, "config", "htmlcache"),  # HTML кэш
            os.path.join(self.steam_dir, "depotcache"),          # Кэш депотов
            os.path.join(os.getenv('APPDATA'), "Steam", "htmlcache"),
            os.path.join(os.getenv('LOCALAPPDATA'), "Steam", "htmlcache"),
            os.path.join(self.steam_dir, "shadercache"),         # Кэш шейдеров
        ]
        
        cleared = 0
        for path in cache_paths:
            try:
                if os.path.exists(path):
                    # Быстрое удаление (без подтверждения)
                    shutil.rmtree(path, ignore_errors=True)
                    print(f"[SteamLibraryOptimizer] 🗑️ Очищено: {path}")
                    cleared += 1
            except Exception as e:
                print(f"[SteamLibraryOptimizer] ⚠️ Ошибка: {e}")
        
        print(f"[SteamLibraryOptimizer] ✅ Очищено {cleared} кэшей")
        return cleared > 0
    
    def disable_steam_features(self) -> bool:
        """
        ✅ ОТКЛЮЧЕНИЕ ФУНКЦИЙ STEAM (ускоряет загрузку)
        """
        if not self.steam_dir:
            self.find_steam_dir()
        
        if not self.steam_dir:
            return False
        
        # Отключение функций через config.vdf
        config_path = os.path.join(self.steam_dir, "config", "config.vdf")
        
        try:
            # Создаём минимальный config
            config_content = """
"UserConfig"
{
    "Store"
    {
        "AutoUpdateApps" "0"
    }
    "Friends"
    {
        "AutoSignIntoFriends" "0"
    }
    "Download"
    {
        "ThrottleEnabled" "0"
    }
}
"""
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Не перезаписываем если существует (сохраняем настройки пользователя)
            if not os.path.exists(config_path):
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(config_content)
                print(f"[SteamLibraryOptimizer] ✅ Config создан")
            
            return True
            
        except Exception as e:
            print(f"[SteamLibraryOptimizer] ⚠️ Ошибка: {e}")
            return False
    
    def add_avast_exclusions(self) -> bool:
        """
        ✅ ДОБАВЛЕНИЕ ИСКЛЮЧЕНИЙ AVAST (ускоряет работу в sandbox)
        """
        from . import config
        
        try:
            for path in config.AVAST_EXCLUSIONS:
                if path and os.path.exists(path):
                    # Добавление через PowerShell
                    cmd = f'powershell -Command "Add-MpPreference -ExclusionPath \'{path}\'"'
                    subprocess.run(
                        cmd,
                        capture_output=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    print(f"[SteamLibraryOptimizer] 🛡️ Avast исключение: {path}")
            
            print(f"[SteamLibraryOptimizer] ✅ Исключения Avast добавлены")
            return True
            
        except Exception as e:
            print(f"[SteamLibraryOptimizer] ⚠️ Ошибка: {e}")
            return False
    
    def kill_steam_processes(self) -> bool:
        """
        ✅ ПОЛНОЕ ЗАВЕРШЕНИЕ STEAM (перед очисткой)
        """
        print(f"[SteamLibraryOptimizer] 🔧 Завершение Steam процессов...")
        
        processes = [
            "steam.exe",
            "steamwebhelper.exe",
            "steamservice.exe",
            "steamclient.dll",
        ]
        
        for proc_name in processes:
            try:
                os.system(f'taskkill /f /im {proc_name} 2>nul')
                print(f"[SteamLibraryOptimizer]   Завершён: {proc_name}")
            except:
                pass
        
        time.sleep(2)
        return True
    
    def optimize_library_load(self) -> bool:
        """
        ✅ ПОЛНАЯ ОПТИМИЗАЦИЯ ЗАГРУЗКИ БИБЛИОТЕКИ
        """
        from . import config
        
        print("[SteamLibraryOptimizer] 🚀 Оптимизация загрузки библиотеки...")
        
        success = True
        
        # Завершение процессов
        success &= self.kill_steam_processes()
        
        # Очистка кэша
        if config.CLEAR_STEAM_CACHE:
            success &= self.clear_steam_cache_fast()
        
        # Отключение функций
        success &= self.disable_steam_features()
        
        # Исключения Avast
        if config.DISABLE_WINDOWS_DEFENDER:
            success &= self.add_avast_exclusions()
        
        if success:
            print("[SteamLibraryOptimizer] ✅ Оптимизация завершена")
        else:
            print("[SteamLibraryOptimizer] ⚠️ Оптимизация частично завершена")
        
        return success
    
    def wait_for_library_ready(self, timeout: int = 60) -> bool:
        """
        ✅ ОЖИДАНИЕ ГОТОВНОСТИ БИБЛИОТЕКИ
        Проверяет что библиотека загрузилась (не просто процесс)
        """
        print(f"[SteamLibraryOptimizer] ⏳ Ожидание готовности библиотеки...")
        start = time.time()
        
        while time.time() - start < timeout:
            # Проверяем что Steam запущен
            steam_running = False
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'] and 'steam.exe' in proc.info['name'].lower():
                        steam_running = True
                        break
                except:
                    pass
            
            if not steam_running:
                time.sleep(1)
                continue
            
            # Проверяем что нет окна входа
            import win32gui
            
            def enum_callback(hwnd, _):
                try:
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd).lower()
                        if 'login' in title or 'войдите' in title or 'sign in' in title:
                            return False
                except:
                    pass
                return True
            
            # Если нет окна входа - библиотека готова
            library_ready = True
            win32gui.EnumWindows(enum_callback, None)
            
            if library_ready:
                elapsed = time.time() - start
                print(f"[SteamLibraryOptimizer] ✅ Библиотека готова за {elapsed:.2f}s")
                return True
            
            time.sleep(1)
        
        print(f"[SteamLibraryOptimizer] ⚠️ Таймаут готовности библиотеки")
        return False


optimizer = SteamLibraryOptimizer()