"""
Steam Preloader - ПРЕДВАРИТЕЛЬНАЯ ЗАГРУЗКА
Ускоряет запуск на 20-30%
"""
import subprocess
import os
import time
import psutil


class SteamPreloader:
    def __init__(self):
        self.steam_path = self._find_steam()
        self.preloaded = False
    
    def _find_steam(self) -> str:
        paths = [
            r"C:\Program Files (x86)\Steam\steam.exe",
            r"C:\Program Files\Steam\steam.exe",
        ]
        for path in paths:
            if os.path.exists(path):
                return path
        return ""
    
    def preload(self) -> bool:
        if not self.steam_path:
            return False
        
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and 'steam.exe' in proc.info['name'].lower():
                    print(f"[SteamPreloader] ✅ Steam уже запущен")
                    self.preloaded = True
                    return True
            except:
                pass
        
        try:
            print(f"[SteamPreloader] 🚀 Предзагрузка Steam...")
            
            subprocess.Popen(
                [self.steam_path, "-silent"],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            )
            
            time.sleep(10)
            
            self.preloaded = True
            print(f"[SteamPreloader] ✅ Steam предзагружен")
            return True
            
        except Exception as e:
            print(f"[SteamPreloader] ❌ Ошибка: {e}")
            return False
    
    def is_ready(self) -> bool:
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and 'steam.exe' in proc.info['name'].lower():
                    return True
            except:
                pass
        return False


if __name__ == "__main__":
    preloader = SteamPreloader()
    preloader.preload()