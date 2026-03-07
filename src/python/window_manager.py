"""
Window Manager - ИСПРАВЛЕННОЕ ПОЗИЦИОНИРОВАНИЕ
Не позволяет окнам возвращаться в середину
"""
import win32gui
import win32con
import time
from typing import Optional, Tuple, List, Dict

from . import config
from .logger import SecureLogger

logger = SecureLogger()


class WindowManager:
    def __init__(self):
        self.positioned_windows: Dict[int, Dict] = {}
        self.window_positions: Dict[int, Tuple[int, int]] = {}  # ✅ account_index -> (x, y)
        self.last_position_check = {}
    
    def position_cs2_window(self, account_index: int, timeout: int = 30) -> bool:
        """Позиционирование окна CS2 с защитой от сброса"""
        titles = ['counter-strike', 'cs2', 'counter strike']
        
        expected_position = self._get_expected_position(account_index)
        x, y = expected_position
        width = config.CS_WIDTH
        height = config.CS_HEIGHT
        
        logger.info(f"[WindowManager] 🪟 Позиционирование окна {account_index}...")
        logger.info(f"[WindowManager] 📐 Ожидаемая позиция: ({x}, {y}) [{width}x{height}]")
        
        for attempt in range(config.WINDOW_POSITION_RETRIES):
            try:
                hwnd = self._find_cs2_window(titles, timeout)
                
                if not hwnd:
                    logger.warning(f"[WindowManager] Окно не найдено (попытка {attempt + 1})")
                    time.sleep(2)
                    continue
                
                # ✅ УСТАНОВКА ПОЗИЦИИ
                success = self._set_window_position(hwnd, x, y, width, height)
                
                if success:
                    # ✅ СОХРАНЕНИЕ ПОЗИЦИИ
                    self.window_positions[account_index] = (x, y)
                    
                    if config.VERIFY_WINDOW_POSITION:
                        # ✅ ПРОВЕРКА ПОЗИЦИИ (несколько раз)
                        verified = False
                        for check_attempt in range(3):
                            time.sleep(0.5)
                            verified = self._verify_window_position(hwnd, x, y, width, height)
                            if verified:
                                break
                            else:
                                logger.debug(f"[WindowManager] Проверка {check_attempt + 1} не удалась, повторяю...")
                                # ✅ ПОВТОРНАЯ УСТАНОВКА ЕСЛИ СБРОСИЛОСЬ
                                self._set_window_position(hwnd, x, y, width, height)
                        
                        if verified:
                            logger.success(f"[WindowManager] Окно {account_index} позиционировано и проверено")
                            self.positioned_windows[account_index] = {
                                'hwnd': hwnd,
                                'position': (x, y),
                                'size': (width, height),
                                'verified': True,
                                'time': time.time()
                            }
                            return True
                        else:
                            logger.warning(f"[WindowManager] Позиция не подтверждена после 3 проверок")
                    else:
                        logger.success(f"[WindowManager] Окно {account_index} позиционировано")
                        return True
                
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"[WindowManager] Ошибка: {e}")
                time.sleep(2)
        
        logger.error(f"[WindowManager] Не удалось позиционировать окно {account_index}")
        return False
    
    def _find_cs2_window(self, titles: List[str], timeout: int = 30) -> Optional[int]:
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
            
            time.sleep(0.5)
        
        return None
    
    def _set_window_position(self, hwnd: int, x: int, y: int, width: int, height: int) -> bool:
        try:
            # ✅ НЕСКОЛЬКО ПОПЫТОК УСТАНОВКИ ПОЗИЦИИ
            for i in range(3):
                win32gui.MoveWindow(hwnd, x, y, width, height, True)
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.SetForegroundWindow(hwnd)
                time.sleep(0.3)
            
            return True
        except Exception as e:
            logger.debug(f"[WindowManager] Ошибка позиционирования: {e}")
            return False
    
    def _verify_window_position(self, hwnd: int, expected_x: int, expected_y: int, 
                                 expected_width: int, expected_height: int) -> bool:
        try:
            rect = win32gui.GetWindowRect(hwnd)
            
            actual_x = rect[0]
            actual_y = rect[1]
            actual_width = rect[2] - rect[0]
            actual_height = rect[3] - rect[1]
            
            tolerance = config.WINDOW_POSITION_TOLERANCE
            
            x_ok = abs(actual_x - expected_x) < tolerance
            y_ok = abs(actual_y - expected_y) < tolerance
            width_ok = abs(actual_width - expected_width) < tolerance
            height_ok = abs(actual_height - expected_height) < tolerance
            
            if config.LOG_WINDOW_POSITION:
                logger.info(f"[WindowManager] 📐 Проверка позиции:")
                logger.info(f"[WindowManager]   Ожидалось: ({expected_x}, {expected_y}) [{expected_width}x{expected_height}]")
                logger.info(f"[WindowManager]   Фактически: ({actual_x}, {actual_y}) [{actual_width}x{actual_height}]")
                logger.info(f"[WindowManager]   X: {'✅' if x_ok else '❌'} Y: {'✅' if y_ok else '❌'} W: {'✅' if width_ok else '❌'} H: {'✅' if height_ok else '❌'}")
            
            return x_ok and y_ok
            
        except Exception as e:
            logger.debug(f"[WindowManager] Ошибка проверки: {e}")
            return False
    
    def _get_expected_position(self, account_index: int) -> Tuple[int, int]:
        col = account_index % 2
        row = account_index // 2
        x = col * config.WINDOW_OFFSET_X
        y = row * config.WINDOW_OFFSET_Y
        return (x, y)
    
    def get_all_positioned(self) -> Dict[int, Dict]:
        return self.positioned_windows
    
    def verify_all_windows(self) -> Dict[int, bool]:
        results = {}
        for account_index, info in self.positioned_windows.items():
            hwnd = info.get('hwnd')
            if hwnd:
                verified = self._verify_window_position(
                    hwnd,
                    info['position'][0],
                    info['position'][1],
                    info['size'][0],
                    info['size'][1]
                )
                results[account_index] = verified
            else:
                results[account_index] = False
        return results
    
    def reposition_failed_windows(self) -> int:
        """Повторное позиционирование неудачных окон"""
        verification = self.verify_all_windows()
        repositioned = 0
        
        for account_index, verified in verification.items():
            if not verified:
                logger.info(f"[WindowManager] 🔄 Попытка репозиционирования окна {account_index}...")
                if self.position_cs2_window(account_index):
                    repositioned += 1
        
        return repositioned
    
    def clear_position(self, account_index: int):
        """Очистить позицию для аккаунта"""
        if account_index in self.window_positions:
            del self.window_positions[account_index]
        if account_index in self.positioned_windows:
            del self.positioned_windows[account_index]
        logger.debug(f"[WindowManager] Позиция {account_index} очищена")
    
    def clear_all_positions(self):
        """Очистить все позиции"""
        self.window_positions.clear()
        self.positioned_windows.clear()
        self.last_position_check.clear()
        logger.debug("[WindowManager] Все позиции очищены")


window_manager = WindowManager()