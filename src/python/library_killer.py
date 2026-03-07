"""
Library Killer - ГАРАНТИРОВАННОЕ ЗАКРЫТИЕ (10 попыток)
"""
import win32gui
import win32con
import win32api
import time
import subprocess
import psutil
from typing import List


class LibraryKiller:
    def __init__(self):
        self.library_titles = ['библиотека', 'library', 'steam']
    
    def find_all_library_windows(self) -> List[int]:
        windows = []
        
        def enum_callback(hwnd, _):
            try:
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd).lower()
                    if any(t in title for t in self.library_titles):
                        if 'login' not in title and 'войдите' not in title and 'cs2' not in title:
                            windows.append(hwnd)
            except:
                pass
        
        win32gui.EnumWindows(enum_callback, None)
        return windows
    
    def close_all_guaranteed(self, timeout: int = 20) -> bool:
        """
        ✅ ГАРАНТИРОВАННОЕ ЗАКРЫТИЕ (10 попыток, 5 методов)
        """
        from . import config
        
        max_attempts = config.MAX_LIBRARY_CLOSE_ATTEMPTS
        
        for attempt in range(max_attempts):
            print(f"[LibraryKiller] 🗑️ Попытка {attempt + 1}/{max_attempts}...")
            
            windows = self.find_all_library_windows()
            
            if not windows:
                print(f"[LibraryKiller] ✅ Библиотек не найдено")
                return True
            
            print(f"[LibraryKiller] 📋 Найдено окон: {len(windows)}")
            
            # МЕТОД 1: PostMessage WM_CLOSE
            for hwnd in windows:
                try:
                    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                    print(f"[LibraryKiller]   Метод 1: WM_CLOSE → {hwnd}")
                except:
                    pass
            
            time.sleep(1)
            
            windows = self.find_all_library_windows()
            if not windows:
                print(f"[LibraryKiller] ✅ Закрыто с попытки {attempt + 1}")
                return True
            
            # МЕТОД 2: SendMessage WM_CLOSE
            for hwnd in windows:
                try:
                    win32gui.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                    print(f"[LibraryKiller]   Метод 2: SendMessage → {hwnd}")
                except:
                    pass
            
            time.sleep(1)
            
            windows = self.find_all_library_windows()
            if not windows:
                print(f"[LibraryKiller] ✅ Закрыто с попытки {attempt + 1}")
                return True
            
            # МЕТОД 3: taskkill steamwebhelper
            try:
                subprocess.run(
                    ['taskkill', '/f', '/im', 'steamwebhelper.exe'],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                print(f"[LibraryKiller]   Метод 3: taskkill steamwebhelper")
            except:
                pass
            
            time.sleep(1)
            
            windows = self.find_all_library_windows()
            if not windows:
                print(f"[LibraryKiller] ✅ Закрыто с попытки {attempt + 1}")
                return True
            
            # МЕТОД 4: Завершение процессов
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and 'steamwebhelper' in proc.info['name'].lower():
                        proc.terminate()
                        print(f"[LibraryKiller]   Метод 4: terminate {proc.info['pid']}")
                except:
                    pass
            
            time.sleep(1)
            
            windows = self.find_all_library_windows()
            if not windows:
                print(f"[LibraryKiller] ✅ Закрыто с попытки {attempt + 1}")
                return True
            
            # МЕТОД 5: Принудительное закрытие
            for hwnd in windows:
                try:
                    win32gui.DestroyWindow(hwnd)
                    print(f"[LibraryKiller]   Метод 5: DestroyWindow → {hwnd}")
                except:
                    pass
            
            time.sleep(1)
        
        windows = self.find_all_library_windows()
        if windows:
            print(f"[LibraryKiller] ⚠️ Осталось окон: {len(windows)}")
            return False
        
        print(f"[LibraryKiller] ✅ Все библиотеки закрыты")
        return True
    
    def wait_for_no_libraries(self, timeout: int = 20) -> bool:
        print(f"[LibraryKiller] ⏳ Ожидание закрытия библиотек...")
        start = time.time()
        
        while time.time() - start < timeout:
            windows = self.find_all_library_windows()
            
            if not windows:
                elapsed = time.time() - start
                print(f"[LibraryKiller] ✅ Библиотеки закрыты за {elapsed:.2f}s")
                return True
            
            time.sleep(0.2)
        
        print(f"[LibraryKiller] ⚠️ Таймаут ожидания библиотек")
        return False


killer = LibraryKiller()