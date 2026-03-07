"""
Window Finder - ИСПРАВЛЕННАЯ АКТИВАЦИЯ ОКОН
Отслеживает окна для каждого аккаунта отдельно
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
        self.account_windows: Dict[int, int] = {}  # ✅ account_id -> hwnd
        self.last_search_time = 0
    
    def find_by_titles(self, titles: List[str], timeout: int = 45, interval: float = 0.03) -> Optional[int]:
        cache_key = "_".join(titles[:2])
        
        if cache_key in self.window_cache:
            hwnd = self.window_cache[cache_key]
            if win32gui.IsWindow(hwnd):
                return hwnd
            del self.window_cache[cache_key]
        
        start = time.time()
        
        while time.time() - start < timeout:
            found = []
            
            def enum_callback(hwnd, _):
                try:
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd)
                        if title:
                            title_lower = title.lower()
                            for t in titles:
                                if t in title_lower:
                                    found.append(hwnd)
                                    return
                except:
                    pass
            
            win32gui.EnumWindows(enum_callback, None)
            
            if found:
                return found[0]
            
            time.sleep(interval)
        
        return None
    
    def find_login_window_for_account(self, account_id: int, timeout: int = 45) -> Optional[int]:
        """
        ✅ ПОИСК ОКНА ВХОДА ДЛЯ КОНКРЕТНОГО АККАУНТА
        """
        # Проверяем кэш для этого аккаунта
        if account_id in self.account_windows:
            hwnd = self.account_windows[account_id]
            if win32gui.IsWindow(hwnd):
                logger.debug(f"[WindowFinder] Найдено в кэше окно для аккаунта {account_id}")
                return hwnd
        
        # Ищем новое окно
        titles = ['steam', 'войдите', 'вход', 'login', 'sign in', 'авторизация', 'sign into']
        hwnd = self.find_by_titles(titles, timeout)
        
        if hwnd:
            # Сохраняем для этого аккаунта
            self.account_windows[account_id] = hwnd
            logger.debug(f"[WindowFinder] Сохранено окно {hwnd} для аккаунта {account_id}")
        
        return hwnd
    
    def find_cs2_window_for_account(self, account_id: int, timeout: int = 30) -> Optional[int]:
        """
        ✅ ПОИСК ОКНА CS2 ДЛЯ КОНКРЕТНОГО АККАУНТА
        """
        titles = ['counter-strike', 'cs2', 'counter strike']
        return self.find_by_titles(titles, timeout)
    
    def activate_window_for_account(self, account_id: int, timeout: int = 45) -> bool:
        """
        ✅ АКТИВАЦИЯ ОКНА ДЛЯ КОНКРЕТНОГО АККАУНТА
        """
        hwnd = self.find_login_window_for_account(account_id, timeout)
        
        if not hwnd:
            logger.warning(f"[WindowFinder] Окно для аккаунта {account_id} не найдено")
            return False
        
        return self.activate_window(hwnd)
    
    def activate_window(self, hwnd: int) -> bool:
        """Активация окна"""
        try:
            if not win32gui.IsWindow(hwnd):
                logger.debug(f"[WindowFinder] Окно {hwnd} не существует")
                return False
            
            # Развернуть если свёрнуто
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.2)
            
            # Показать окно
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            time.sleep(0.1)
            
            # Активация (несколько попыток)
            for i in range(3):
                try:
                    win32gui.SetForegroundWindow(hwnd)
                    win32gui.SetFocus(hwnd)
                    time.sleep(0.1)
                except:
                    pass
            
            time.sleep(0.2)
            logger.debug(f"[WindowFinder] Окно {hwnd} активировано")
            return True
            
        except Exception as e:
            logger.debug(f"[WindowFinder] Ошибка активации: {e}")
            return False
    
    def clear_account_window(self, account_id: int):
        """Очистить кэш окна для аккаунта"""
        if account_id in self.account_windows:
            del self.account_windows[account_id]
            logger.debug(f"[WindowFinder] Очищено окно для аккаунта {account_id}")
    
    def clear_all_windows(self):
        """Очистить все кэшированные окна"""
        self.account_windows.clear()
        self.window_cache.clear()
        logger.debug("[WindowFinder] Все окна очищены")


window_finder = WindowFinder()