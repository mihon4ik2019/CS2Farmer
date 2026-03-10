"""
Window Finder - ИСПРАВЛЕННЫЙ + find_cs2_window
"""
import win32gui
import win32con
import time
from typing import Optional, List, Dict

from . import config
from .logger import SecureLogger

logger = SecureLogger()


class WindowFinder:
    def __init__(self):
        self.window_cache: Dict[str, int] = {}
        self.account_windows: Dict[int, int] = {}
        self.last_search_time = 0
        self.search_count = 0
    
    def find_by_titles(self, titles: List[str], timeout: int = 30, interval: float = 0.1) -> Optional[int]:
        """Быстрый поиск окна"""
        cache_key = "_".join(titles[:2])
        
        if cache_key in self.window_cache:
            hwnd = self.window_cache[cache_key]
            if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
                return hwnd
            if cache_key in self.window_cache:
                del self.window_cache[cache_key]
        
        start = time.time()
        
        while time.time() - start < timeout:
            self.search_count += 1
            found = []
            
            def enum_callback(hwnd, _):
                try:
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd)
                        if title:
                            title_lower = title.lower()
                            for t in titles:
                                if t.lower() in title_lower:
                                    found.append((hwnd, title))
                                    return
                except:
                    pass
            
            win32gui.EnumWindows(enum_callback, None)
            
            if found:
                hwnd, title = found[0]
                self.window_cache[cache_key] = hwnd
                logger.debug(f"[WindowFinder] ✅ Найдено: '{title}'")
                return hwnd
            
            time.sleep(interval)
        
        return None
    
    def find_login_window_for_account(self, account_id: int, timeout: int = 30) -> Optional[int]:
        """Поиск окна входа"""
        if account_id in self.account_windows:
            hwnd = self.account_windows[account_id]
            if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
                return hwnd
            if account_id in self.account_windows:
                del self.account_windows[account_id]
        
        titles = ['steam', 'войдите', 'вход', 'login', 'sign in', 'авторизация']
        hwnd = self.find_by_titles(titles, timeout=timeout, interval=0.1)
        
        if hwnd:
            self.account_windows[account_id] = hwnd
        
        return hwnd
    
    def find_cs2_window_for_account(self, account_id: int, timeout: int = 30) -> Optional[int]:
        """Поиск окна CS2"""
        titles = ['counter-strike', 'cs2', 'counter strike']
        return self.find_by_titles(titles, timeout=timeout, interval=0.1)
    
    def find_cs2_window(self, timeout: int = 30) -> Optional[int]:
        """
        ✅ ИСПРАВЛЕНО: Поиск окна CS2 (публичный метод)
        """
        titles = ['counter-strike', 'cs2', 'counter strike']
        return self.find_by_titles(titles, timeout=timeout, interval=0.1)
    
    def find_steam_login(self, timeout: int = 30) -> Optional[int]:
        """Поиск окна входа Steam"""
        titles = ['steam', 'войдите', 'вход', 'login', 'sign in', 'авторизация']
        return self.find_by_titles(titles, timeout=timeout, interval=0.1)
    
    def find_steam_library(self, timeout: int = 30) -> Optional[int]:
        """Поиск библиотеки Steam"""
        titles = ['библиотека', 'library', 'steam']
        return self.find_by_titles(titles, timeout=timeout, interval=0.1)
    
    def activate_window_for_account(self, account_id: int, timeout: int = 30) -> bool:
        """Активация окна для аккаунта"""
        hwnd = self.find_login_window_for_account(account_id, timeout)
        if not hwnd:
            return False
        return self.activate_window(hwnd)
    
    def activate_window(self, hwnd: int) -> bool:
        """Активация окна"""
        try:
            if not win32gui.IsWindow(hwnd):
                return False
            
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.3)
            
            for i in range(3):
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                time.sleep(0.2)
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.2)
                
                if win32gui.GetForegroundWindow() == hwnd:
                    time.sleep(0.3)
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"[WindowFinder] Ошибка активации: {e}")
            return False
    
    def position_window(self, hwnd: int, x: int, y: int, width: int, height: int) -> bool:
        """Позиционирование окна"""
        try:
            win32gui.MoveWindow(hwnd, x, y, width, height, True)
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            return True
        except Exception as e:
            logger.debug(f"[WindowFinder] Ошибка позиции: {e}")
            return False
    
    def clear_account_window(self, account_id: int):
        """Очистить кэш окна"""
        if account_id in self.account_windows:
            del self.account_windows[account_id]
    
    def clear_all_windows(self):
        """Очистить все кэши"""
        count = len(self.account_windows)
        self.account_windows.clear()
        self.window_cache.clear()
        logger.debug(f"[WindowFinder] 🗑️ Кэши очищены ({count})")
    
    def get_status(self) -> Dict:
        """Статус"""
        return {
            'cached_windows': len(self.window_cache),
            'account_windows': len(self.account_windows),
            'search_count': self.search_count
        }


window_finder = WindowFinder()