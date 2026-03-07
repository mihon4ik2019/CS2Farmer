"""
Popup Closer - ИСПРАВЛЕННОЕ ЗАКРЫТИЕ POPUP
Закрывает новости, обновления, Premier Season
"""
import win32gui
import win32con
import time
from typing import List, Optional

from . import config
from .logger import SecureLogger

logger = SecureLogger()


class PopupCloser:
    def __init__(self):
        self.popup_titles = config.POPUP_TITLES
        self.closed_popups = []
        self.running = False
        self.popup_buttons = ['CLOSE', 'OK', 'ЗАКРЫТЬ', 'X', '✕']  # ✅ Кнопки для закрытия
    
    def find_popup_windows(self) -> List[int]:
        """Поиск popup окон для закрытия"""
        popups = []
        
        def enum_callback(hwnd, _):
            try:
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title:
                        title_lower = title.lower()
                        for popup_title in self.popup_titles:
                            if popup_title in title_lower:
                                # Проверяем что это не главное окно Steam/CS2
                                if 'steam' not in title_lower and 'counter-strike' not in title_lower and 'cs2' not in title_lower:
                                    popups.append(hwnd)
                                    return
            except:
                pass
        
        win32gui.EnumWindows(enum_callback, None)
        return popups
    
    def close_popup(self, hwnd: int) -> bool:
        """Закрытие popup окна"""
        try:
            title = win32gui.GetWindowText(hwnd)
            
            # Метод 1: WM_CLOSE
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            time.sleep(0.3)
            
            # Проверка что окно закрылось
            if not win32gui.IsWindow(hwnd):
                logger.info(f"[PopupCloser] 🗑️ Закрыто: {title[:50]}")
                return True
            
            # Метод 2: Поиск кнопки закрытия
            def find_button_callback(hwnd_child, _):
                try:
                    class_name = win32gui.GetClassName(hwnd_child)
                    if 'button' in class_name.lower() or 'Button' in class_name:
                        button_title = win32gui.GetWindowText(hwnd_child)
                        if button_title.upper() in self.popup_buttons or button_title == '':
                            win32gui.PostMessage(hwnd_child, win32con.BM_CLICK, 0, 0)
                except:
                    pass
            
            win32gui.EnumChildWindows(hwnd, find_button_callback, None)
            time.sleep(0.3)
            
            if not win32gui.IsWindow(hwnd):
                logger.info(f"[PopupCloser] 🗑️ Закрыто (кнопка): {title[:50]}")
                return True
            
            # Метод 3: Enter key
            try:
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.2)
                win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
                win32gui.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
                time.sleep(0.3)
                
                if not win32gui.IsWindow(hwnd):
                    logger.info(f"[PopupCloser] 🗑️ Закрыто (Enter): {title[:50]}")
                    return True
            except:
                pass
            
            return not win32gui.IsWindow(hwnd)
            
        except Exception as e:
            logger.debug(f"[PopupCloser] Ошибка закрытия: {e}")
            return False
    
    def close_all_popups(self) -> int:
        """Закрытие всех popup окон"""
        if not config.AUTO_CLOSE_POPUPS:
            return 0
        
        popups = self.find_popup_windows()
        closed_count = 0
        
        for hwnd in popups:
            if hwnd not in self.closed_popups:
                if self.close_popup(hwnd):
                    self.closed_popups.append(hwnd)
                    closed_count += 1
        
        if closed_count > 0:
            logger.info(f"[PopupCloser] Закрыто {closed_count} popup окон")
        
        return closed_count
    
    def start_monitoring(self, interval: float = None):
        """Запуск мониторинга popup окон"""
        if interval is None:
            interval = config.POPUP_CHECK_INTERVAL
        
        self.running = True
        logger.debug(f"[PopupCloser] Мониторинг запущен (интервал: {interval}s)")
        
        while self.running:
            try:
                self.close_all_popups()
            except:
                pass
            time.sleep(interval)
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.running = False
        logger.debug("[PopupCloser] Мониторинг остановлен")
    
    def close_popup_on_launch(self):
        """Закрытие popup при запуске аккаунта"""
        if config.POPUP_AUTO_CLOSE_ON_LAUNCH:
            time.sleep(2)  # Ждём появления popup
            closed = self.close_all_popups()
            if closed > 0:
                logger.info(f"[PopupCloser] Закрыто {closed} popup при запуске")


popup_closer = PopupCloser()