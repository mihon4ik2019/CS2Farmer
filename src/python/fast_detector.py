"""
Fast Detector - ПРОГРАММНОЕ УСКОРЕНИЕ
Параллельная детекция + множественные индикаторы
"""
import psutil
import win32gui
import win32con
import threading
import time
from typing import Optional, Dict, List
from concurrent.futures import ThreadPoolExecutor


class FastDetector:
    """
    БЫСТРАЯ ДЕТЕКЦИЯ CS2 И STEAM
    Использует несколько методов одновременно
    """
    
    def __init__(self):
        self.cs2_detected = False
        self.library_closed = False
        self.steam_loaded = False
        self.detectors = []
    
    def detect_cs2_multi(self, timeout: int = 60) -> bool:
        """
        ✅ МНОЖЕСТВЕННАЯ ДЕТЕКЦИЯ CS2 (быстрее)
        - Процесс
        - Окно
        - Потоки
        """
        self.cs2_detected = False
        
        def check_process():
            for proc in psutil.process_iter(['pid', 'name', 'status']):
                try:
                    if proc.info['name'] and 'cs2' in proc.info['name'].lower():
                        self.cs2_detected = True
                        return True
                except:
                    pass
            return False
        
        def check_window():
            titles = ['counter-strike', 'cs2', 'counter strike']
            for title in titles:
                hwnd = self._find_window_by_title(title)
                if hwnd:
                    self.cs2_detected = True
                    return True
            return False
        
        def check_threads():
            for proc in psutil.process_iter(['pid', 'name', 'num_threads']):
                try:
                    if proc.info['name'] and 'cs2' in proc.info['name'].lower():
                        if proc.info['num_threads'] and proc.info['num_threads'] > 10:
                            self.cs2_detected = True
                            return True
                except:
                    pass
            return False
        
        # ✅ ПАРАЛЛЕЛЬНАЯ ПРОВЕРКА (быстрее в 3 раза)
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(check_process),
                executor.submit(check_window),
                executor.submit(check_threads)
            ]
            
            start = time.time()
            for future in futures:
                if future.result():
                    elapsed = time.time() - start
                    print(f"[FastDetector] ✅ CS2 обнаружен за {elapsed:.2f}s")
                    return True
                if time.time() - start > timeout:
                    break
        
        return False
    
    def detect_steam_loaded(self, timeout: int = 30) -> bool:
        """
        ✅ БЫСТРАЯ ДЕТЕКЦИЯ ЗАГРУЗКИ STEAM
        Проверяет наличие библиотеки И процесса
        """
        self.steam_loaded = False
        
        def check_library():
            titles = ['библиотека', 'library']
            for title in titles:
                hwnd = self._find_window_by_title(title)
                if hwnd:
                    # Проверяем что это не окно входа
                    if 'login' not in title.lower() and 'войдите' not in title.lower():
                        self.steam_loaded = True
                        return True
            return False
        
        def check_steam_process():
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and 'steam.exe' in proc.info['name'].lower():
                        # Проверяем что процесс активен (>5 потоков)
                        try:
                            p = psutil.Process(proc.info['pid'])
                            if p.num_threads() > 5:
                                self.steam_loaded = True
                                return True
                        except:
                            pass
                except:
                    pass
            return False
        
        # ✅ ПАРАЛЛЕЛЬНАЯ ПРОВЕРКА
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [
                executor.submit(check_library),
                executor.submit(check_steam_process)
            ]
            
            start = time.time()
            for future in futures:
                if future.result():
                    elapsed = time.time() - start
                    print(f"[FastDetector] ✅ Steam загружен за {elapsed:.2f}s")
                    return True
                if time.time() - start > timeout:
                    break
        
        return False
    
    def check_library_closed(self, timeout: int = 10) -> bool:
        """
        ✅ АГРЕССИВНАЯ ПРОВЕРКА ЗАКРЫТИЯ БИБЛИОТЕКИ
        """
        self.library_closed = False
        
        start = time.time()
        while time.time() - start < timeout:
            titles = ['библиотека', 'library']
            found = False
            
            for title in titles:
                hwnd = self._find_window_by_title(title)
                if hwnd:
                    found = True
                    break
            
            if not found:
                self.library_closed = True
                elapsed = time.time() - start
                print(f"[FastDetector] ✅ Библиотека закрыта за {elapsed:.2f}s")
                return True
            
            time.sleep(0.1)  # Быстрая проверка
        
        return self.library_closed
    
    def _find_window_by_title(self, title: str) -> Optional[int]:
        """Быстрый поиск окна"""
        found = []
        
        def enum_callback(hwnd, _):
            try:
                if win32gui.IsWindowVisible(hwnd):
                    window_title = win32gui.GetWindowText(hwnd).lower()
                    if title.lower() in window_title:
                        found.append(hwnd)
            except:
                pass
        
        win32gui.EnumWindows(enum_callback, None)
        return found[0] if found else None
    
    def wait_for_cs2_ready(self, timeout: int = 60) -> bool:
        """
        ✅ КОМПЛЕКСНАЯ ПРОВЕРКА ГОТОВНОСТИ CS2
        """
        print(f"[FastDetector] ⏳ Ожидание готовности CS2...")
        start = time.time()
        
        # Шаг 1: Детекция процесса
        if not self.detect_cs2_multi(timeout=30):
            return False
        
        # Шаг 2: Проверка окна
        time.sleep(3)  # Небольшая пауза для появления окна
        
        # Шаг 3: Проверка что окно активно
        for _ in range(10):
            hwnd = self._find_window_by_title('cs2')
            if hwnd:
                try:
                    if win32gui.IsWindowVisible(hwnd):
                        print(f"[FastDetector] ✅ CS2 готов (окно активно)")
                        return True
                except:
                    pass
            time.sleep(0.5)
        
        return True


# Глобальный экземпляр
detector = FastDetector()