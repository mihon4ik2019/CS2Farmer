#!/usr/bin/env python3
import os
import time
import threading
import json
import subprocess
import pyautogui
import win32gui
import win32con
import win32api
import psutil
import random
import winreg
from datetime import datetime, timedelta
from typing import List, Optional, Dict

from .database import Database
from .process_manager import ProcessManager
from .ban_checker import BanChecker
from .models import Account, AccountStatus
from .logger import logger

class AccountManager:
    """Менеджер аккаунтов для управления входом и запуском CS2"""
    
    def __init__(self, db: Database, pm: ProcessManager, ban_checker: BanChecker):
        self.db = db
        self.pm = pm
        self.ban_checker = ban_checker
        self._stop_flags = {}
        self._last_attempt = {}
        self._rate_limit_delay = timedelta(minutes=10)
        self.bes_path = self._find_bes()
        self.steam_instances = {}
        logger.info("[AccountManager] Инициализация завершена")

    def _find_bes(self) -> Optional[str]:
        """Поиск пути к BES.exe"""
        possible_paths = [
            r"C:\Users\mihon\Desktop\CS2Farmer\BES\BES.exe",
            r"C:\Program Files\BES\BES.exe",
            r"C:\Program Files (x86)\BES\BES.exe",
            os.path.join(os.path.dirname(__file__), '..', '..', 'BES', 'BES.exe'),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"[AccountManager] ✅ BES найден: {path}")
                return path
        logger.warning(f"[AccountManager] ⚠️ BES не найден")
        return None

    def _apply_bes_to_process(self, process_name: str = "cs2.exe", limit: int = 50):
        """Применение ограничения CPU через BES"""
        if not self.bes_path:
            return False
        try:
            subprocess.Popen([self.bes_path, "--process", process_name, "--limit", str(limit)],
                           shell=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
            logger.info(f"[AccountManager] ✅ BES применён к {process_name}")
            return True
        except Exception as e:
            logger.error(f"[AccountManager] ❌ Ошибка BES: {e}")
            return False

    def _generate_2fa_code(self, shared_secret: str) -> str:
        """Генерация 2FA кода"""
        import hmac, hashlib, struct, base64
        time_buffer = struct.pack('>Q', int(time.time()) // 30)
        hmac_hash = hmac.new(base64.b64decode(shared_secret), time_buffer, hashlib.sha1).digest()
        start = hmac_hash[19] & 0x0F
        code_int = struct.unpack('>I', hmac_hash[start:start+4])[0] & 0x7FFFFFFF
        chars = '23456789BCDFGHJKMNPQRTVWXY'
        code = ''
        for _ in range(5):
            code += chars[code_int % len(chars)]
            code_int //= len(chars)
        return code

    def _kill_steam_processes(self):
        """Полное завершение всех процессов Steam перед запуском"""
        logger.info("[AccountManager] 🔧 Завершение всех процессов Steam...")
        os.system("taskkill /f /im steam.exe 2>nul")
        os.system("taskkill /f /im steamwebhelper.exe 2>nul")
        time.sleep(3)
        logger.info("[AccountManager] ✅ Все процессы Steam завершены")

    def _find_window_by_title_contains(self, texts: List[str], timeout: int = 30, 
                                        interval: int = 1) -> Optional[int]:
        """Поиск окна по частичному совпадению заголовка"""
        logger.info(f"[AccountManager] 🔍 Поиск окна: {texts} (таймаут {timeout} сек)")
        start = time.time()
        attempt = 0
        
        while time.time() - start < timeout:
            attempt += 1
            windows = []
            
            def enum_callback(hwnd, _):
                try:
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd)
                        if title:
                            for t in texts:
                                if t.lower() in title.lower():
                                    windows.append((hwnd, title))
                                    return
                except:
                    pass
            
            win32gui.EnumWindows(enum_callback, None)
            
            if windows:
                hwnd, title = windows[0]
                logger.info(f"[AccountManager] ✅ Окно найдено: '{title}' (HWND: {hwnd})")
                return hwnd
            
            if attempt % 10 == 0:
                logger.debug(f"[AccountManager] Попытка {attempt}...")
                
            time.sleep(interval)
            
        logger.error(f"[AccountManager] ❌ Окно не найдено за {timeout} секунд")
        return None

    def _find_login_window(self, timeout: int = 30) -> Optional[int]:
        """Поиск окна входа Steam (РАСШИРЕННЫЙ СПИСОК ЗАГОЛОВКОВ)"""
        titles = [
            "войдите", "вход", "steam", "login", "sign in",
            "авторизация", "авторизуйтесь", "authorize", "authentication",
            "steam guard", "guard", "код", "code", "подтверждение",
            "welcome", "добро пожаловать", "продолжить", "continue"
        ]
        return self._find_window_by_title_contains(titles, timeout)

    def _find_library_window(self, timeout: int = 30) -> Optional[int]:
        """Поиск окна библиотеки Steam"""
        titles = [
            "библиотека", "library", "steam", "store", "магазин",
            "сообщество", "community", "профиль", "profile"
        ]
        return self._find_window_by_title_contains(titles, timeout)

    def _find_any_steam_window(self, timeout: int = 30) -> Optional[int]:
        """Поиск ЛЮБОГО окна Steam"""
        titles = ["steam"]
        return self._find_window_by_title_contains(titles, timeout)

    def _enter_credentials(self, username: str, password: str, code: str) -> bool:
        """Ввод учётных данных"""
        logger.info(f"[AccountManager] 👤 Ввод данных для: {username}")
        time.sleep(2)
        
        try:
            # Ввод логина
            pyautogui.write(username, interval=0.05)
            time.sleep(0.5)
            
            # Переход к паролю
            pyautogui.press('tab')
            time.sleep(0.5)
            
            # Ввод пароля
            pyautogui.write(password, interval=0.05)
            time.sleep(0.5)
            
            # Отправка
            pyautogui.press('enter')
            logger.info(f"[AccountManager] ✅ Логин и пароль введены")
            
            # Ожидание 2FA поля
            time.sleep(10)
            
            # Переход к 2FA (обычно 3-4 tab)
            for i in range(4):
                pyautogui.press('tab')
                time.sleep(0.3)
            
            # Ввод 2FA
            pyautogui.write(code, interval=0.05)
            time.sleep(0.5)
            pyautogui.press('enter')
            logger.info(f"[AccountManager] ✅ 2FA код введён: {code}")
            
            return True
        except Exception as e:
            logger.error(f"[AccountManager] ❌ Ошибка ввода: {e}")
            return False

    def _scan_mafiles(self) -> Dict[str, Dict[str, str]]:
        """Сканирование mafiles"""
        result = {}
        mafiles_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'mafiles')
        
        if not os.path.exists(mafiles_dir):
            logger.warning(f"[AccountManager] ⚠️ mafiles не найдена: {mafiles_dir}")
            return result

        for filename in os.listdir(mafiles_dir):
            if not filename.endswith('.maFile'):
                continue
            file_path = os.path.join(mafiles_dir, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                username = data.get('account_name')
                if not username:
                    continue
                steam_id = None
                session = data.get('Session')
                if session and isinstance(session, dict):
                    steam_id = session.get('SteamID')
                result[username] = {
                    'path': file_path,
                    'steam_id': steam_id,
                    'shared_secret': data.get('shared_secret')
                }
            except Exception as e:
                logger.error(f"[AccountManager] ❌ Ошибка maFile {filename}: {e}")
        return result

    def import_from_file(self, file_path: str) -> int:
        """Импорт аккаунтов"""
        mafiles_map = self._scan_mafiles()
        count = 0
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or ':' not in line:
                    continue
                username, password = line.split(':', 1)
                
                ma_file_info = mafiles_map.get(username)
                ma_file_path = ma_file_info['path'] if ma_file_info else None
                steam_id = ma_file_info['steam_id'] if ma_file_info else None
                
                existing = [a for a in self.db.get_accounts() if a.username == username]
                if existing:
                    continue
                    
                acc_id = self.db.add_account(username, password, ma_file_path)
                if steam_id:
                    acc = self.get_account(acc_id)
                    if acc:
                        acc.steam_id = steam_id
                        self.db.update_account(acc)
                count += 1
        return count

    def get_all(self) -> List[Account]:
        return self.db.get_accounts()

    def get_account(self, account_id: int) -> Optional[Account]:
        for acc in self.get_all():
            if acc.id == account_id:
                return acc
        return None

    def start_accounts_sequential(self, account_ids: List[int], 
                                   progress_callback=None):
        """Последовательный запуск"""
        def run_sequential():
            total = len(account_ids)
            for i, acc_id in enumerate(account_ids):
                logger.info(f"[AccountManager] ===== Запуск {i+1}/{total} =====")
                
                # СБРОС СТАТУСА ПЕРЕД ЗАПУСКОМ
                acc = self.get_account(acc_id)
                if acc:
                    acc.status = AccountStatus.STOPPED
                    acc.status_message = ""
                    self.db.update_account(acc)
                    logger.info(f"[AccountManager] 🔄 Статус сброшен для {acc.username}")
                
                self._kill_steam_processes()
                success = self.start_account(acc_id)
                
                if progress_callback:
                    progress_callback(i + 1, total)
                    
                if i < total - 1:
                    wait_time = 45
                    logger.info(f"[AccountManager] ⏳ Ожидание {wait_time} сек...")
                    time.sleep(wait_time)
                    
            logger.info(f"[AccountManager] ✅ Все {total} аккаунтов обработаны")
            
        threading.Thread(target=run_sequential, daemon=True).start()

    def _launch_cs2_secure(self, steam_path: str, ipc_name: str, 
                           steam_data_dir: str) -> bool:
        """Запуск CS2"""
        steam_dir = os.path.dirname(steam_path)
        
        try:
            logger.info(f"[AccountManager] 🎮 Запуск CS2 через Steam")
            cmd = [
                steam_path,
                "-master_ipc_name_override", ipc_name,
                "-fulldir", steam_data_dir,
                "-applaunch", "730"
            ] + self.pm.CS2_LAUNCH_OPTIONS
            
            subprocess.Popen(cmd, cwd=steam_dir,
                           creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            logger.info(f"[AccountManager] ✅ Команда запуска CS2 выполнена")
            return True
        except Exception as e:
            logger.error(f"[AccountManager] ❌ Ошибка запуска CS2: {e}")
            
        # Фолбэк
        cs2_exe = os.path.join(
            steam_dir, "steamapps", "common", "Counter-Strike Global Offensive",
            "game", "bin", "win64", "cs2.exe"
        )
        if os.path.exists(cs2_exe):
            try:
                cmd = [cs2_exe] + self.pm.CS2_LAUNCH_OPTIONS
                subprocess.Popen(cmd, cwd=os.path.dirname(cs2_exe),
                               creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                return True
            except Exception as e:
                logger.error(f"[AccountManager] ❌ Фолбэк не удался: {e}")
        
        return False

    def start_account(self, account_id: int) -> bool:
        """Запуск аккаунта"""
        account = self.get_account(account_id)
        if not account:
            logger.error(f"[AccountManager] ❌ Аккаунт {account_id} не найден")
            return False
        
        # === СБРОС СТАТУСА ===
        account.status = AccountStatus.STOPPED
        account.status_message = ""
        self.db.update_account(account)
        logger.info(f"[AccountManager] 🔄 Статус сброшен: {account.username}")
        
        if account.status != AccountStatus.STOPPED:
            logger.warning(f"[AccountManager] ⚠️ Аккаунт не в статусе STOPPED")
            return False

        # Проверка лимита
        last = self._last_attempt.get(account_id)
        if last and datetime.now() - last < self._rate_limit_delay:
            logger.warning(f"[AccountManager] ⏳ Лимит запросов для {account.username}")
            account.status = AccountStatus.ERROR
            account.status_message = "Лимит запросов Steam"
            self.db.update_account(account)
            return False

        # Проверка бана
        if account.steam_id:
            banned = self.ban_checker.check_account(account.steam_id)
            if banned:
                account.status = AccountStatus.BANNED
                self.db.update_account(account)
                logger.warning(f"[AccountManager] 🚫 Аккаунт забанен: {account.username}")
                return False

        account.status = AccountStatus.STARTING
        self.db.update_account(account)
        logger.info(f"[AccountManager] 🚀 Запуск: {account.username}")

        # Проверка maFile
        if not account.ma_file_path:
            logger.error(f"[AccountManager] ❌ Нет maFile для {account.username}")
            account.status = AccountStatus.ERROR
            account.status_message = "No maFile"
            self.db.update_account(account)
            return False

        try:
            with open(account.ma_file_path, 'r', encoding='utf-8') as f:
                ma_data = json.load(f)
            shared_secret = ma_data.get('shared_secret')
            if not shared_secret:
                raise ValueError("No shared_secret")
        except Exception as e:
            logger.error(f"[AccountManager] ❌ Ошибка maFile: {e}")
            account.status = AccountStatus.ERROR
            account.status_message = f"Invalid maFile: {e}"
            self.db.update_account(account)
            return False

        twofactor_code = self._generate_2fa_code(shared_secret)
        logger.info(f"[AccountManager] ✅ 2FA код: {twofactor_code}")

        self._last_attempt[account_id] = datetime.now()

        # Поиск Steam
        steam_path = self.pm.find_steam_path()
        if not steam_path:
            logger.error(f"[AccountManager] ❌ Steam не найден")
            account.status = AccountStatus.ERROR
            account.status_message = "Steam not found"
            self.db.update_account(account)
            return False

        # Подготовка папки данных
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        steam_data_dir = os.path.join(base_dir, 'steam_data', account.username)
        os.makedirs(steam_data_dir, exist_ok=True)
        logger.info(f"[AccountManager] 📁 Steam data: {steam_data_dir}")

        # Генерация IPC
        windows_username = os.getlogin()
        random_suffix = random.randint(1000, 9999)
        ipc_name = f"steam_{windows_username}_{account.username}_{account_id}_{random_suffix}"[:60]

        # === ЗАПУСК STEAM ===
        logger.info(f"[AccountManager] 🖥️ Запуск Steam (IPC: {ipc_name})")
        cmd = [
            steam_path,
            "-master_ipc_name_override", ipc_name,
            "-fulldir", steam_data_dir,
            "-no-cef-sandbox",
            "-nofriendsui"
        ]
        
        try:
            process = subprocess.Popen(cmd, cwd=os.path.dirname(steam_path),
                                      creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            pid = process.pid
            self.steam_instances[account_id] = (process, ipc_name, pid)
            logger.info(f"[AccountManager] ✅ Steam запущен (PID: {pid})")
        except Exception as e:
            logger.error(f"[AccountManager] ❌ Ошибка запуска Steam: {e}")
            account.status = AccountStatus.ERROR
            account.status_message = f"Steam launch failed: {e}"
            self.db.update_account(account)
            return False

        # === ОЖИДАНИЕ ЗАПУСКА STEAM ===
        logger.info(f"[AccountManager] ⏳ Ожидание запуска Steam (25 сек)...")
        time.sleep(25)
        
        if not psutil.pid_exists(pid):
            logger.error(f"[AccountManager] ❌ Steam процесс умер")
            account.status = AccountStatus.ERROR
            account.status_message = "Steam process died"
            self.db.update_account(account)
            return False

        # === ПОИСК ОКНА ВХОДА ===
        logger.info(f"[AccountManager] 🔍 Поиск окна входа...")
        login_window = self._find_login_window(timeout=30)
        
        # Если окно входа не найдено, ищем библиотеку (уже авторизован)
        if not login_window:
            logger.info(f"[AccountManager] 🔍 Окно входа не найдено, поиск библиотеки...")
            login_window = self._find_library_window(timeout=30)
        
        # Если всё ещё не найдено, ищем любое окно Steam
        if not login_window:
            logger.info(f"[AccountManager] 🔍 Поиск любого окна Steam...")
            login_window = self._find_any_steam_window(timeout=30)
        
        if not login_window:
            logger.error(f"[AccountManager] ❌ Ни одно окно Steam не найдено")
            account.status = AccountStatus.ERROR
            account.status_message = "Steam window not found"
            self.db.update_account(account)
            return False

        # Активация окна
        logger.info(f"[AccountManager] ✅ Окно найдено, активация...")
        try:
            win32gui.ShowWindow(login_window, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(login_window)
            time.sleep(2)
        except Exception as e:
            logger.warning(f"[AccountManager] ⚠️ Ошибка активации окна: {e}")

        # Ввод данных
        if not self._enter_credentials(account.username, account.password, twofactor_code):
            account.status = AccountStatus.ERROR
            account.status_message = "Credential input failed"
            self.db.update_account(account)
            return False

        # Ожидание входа
        logger.info(f"[AccountManager] ⏳ Ожидание авторизации (30 сек)...")
        time.sleep(30)

        if not psutil.pid_exists(pid):
            logger.error(f"[AccountManager] ❌ Steam упал после входа")
            account.status = AccountStatus.ERROR
            account.status_message = "Steam crashed"
            self.db.update_account(account)
            return False

        # === ЗАПУСК CS2 ===
        logger.info(f"[AccountManager] 🎮 ЗАПУСК CS2...")
        self._launch_cs2_secure(steam_path, ipc_name, steam_data_dir)

        # Ожидание CS2
        cs2_found = self.pm.wait_for_cs2(timeout=60, check_interval=2)
        
        if not cs2_found:
            logger.warning(f"[AccountManager] ⚠️ CS2 не обнаружен")

        account.status = AccountStatus.IN_GAME
        account.last_login = datetime.now()
        self.db.update_account(account)
        logger.info(f"[AccountManager] ✅ Аккаунт запущен: {account.username} (PID: {pid})")

        # BES
        time.sleep(8)
        self._apply_bes_to_process("cs2.exe", 50)

        # Счётчик времени
        stop_event = threading.Event()
        self._stop_flags[account_id] = stop_event
        
        def update_time():
            while not stop_event.wait(60):
                account.play_time_minutes += 1
                self.db.update_account(account)
                
        threading.Thread(target=update_time, daemon=True).start()
        return True

    def stop_account(self, account_id: int):
        """Остановка аккаунта"""
        account = self.get_account(account_id)
        if account:
            account.status = AccountStatus.STOPPED
            self.db.update_account(account)

            if account_id in self.steam_instances:
                process, ipc_name, pid = self.steam_instances[account_id]
                try:
                    parent = psutil.Process(pid)
                    for child in parent.children(recursive=True):
                        child.terminate()
                    parent.terminate()
                    logger.info(f"[AccountManager] 🛑 Steam остановлен: {account.username}")
                except:
                    pass
                del self.steam_instances[account_id]

            if account_id in self._stop_flags:
                self._stop_flags[account_id].set()
                del self._stop_flags[account_id]

    def stop_all(self):
        """Остановка всех"""
        for acc_id, (process, ipc_name, pid) in list(self.steam_instances.items()):
            try:
                parent = psutil.Process(pid)
                for child in parent.children(recursive=True):
                    child.terminate()
                parent.terminate()
            except:
                pass
        self.steam_instances.clear()
        os.system("taskkill /f /im cs2.exe 2>nul")
        for acc in self.get_all():
            acc.status = AccountStatus.STOPPED
            self.db.update_account(acc)
        self._stop_flags.clear()
        logger.info(f"[AccountManager] Все аккаунты остановлены")