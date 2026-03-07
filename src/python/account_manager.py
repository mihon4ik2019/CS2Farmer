"""
Account Manager - ИСПРАВЛЕННАЯ АКТИВАЦИЯ ОКОН
Каждый аккаунт активирует своё окно
"""
import os
import time
import threading
import json
import subprocess
import pyautogui
import win32gui
import win32con
import psutil
import hmac
import hashlib
import struct
import base64
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple

from .database import Database
from .process_manager import ProcessManager
from .ban_checker import BanChecker
from .session_manager import SessionManager
from .window_finder import WindowFinder
from .models import Account, AccountStatus
from .logger import SecureLogger
from . import config

logger = SecureLogger()


class AccountManager:
    def __init__(self, db: Database, pm: ProcessManager, ban_checker: BanChecker):
        self.db = db
        self.pm = pm
        self.ban_checker = ban_checker
        self.session_manager = SessionManager()
        self.window_finder = WindowFinder()  # ✅ Отдельный finder для каждого менеджера
        self._stop_flags = {}
        self._last_attempt = {}
        self._rate_limit_delay = timedelta(minutes=config.RATE_LIMIT_DELAY_MINUTES)
        self.steam_instances = {}

    def _generate_2fa_code(self, shared_secret: str) -> str:
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

    def _activate_window_for_account(self, account_id: int) -> bool:
        """
        ✅ АКТИВАЦИЯ ОКНА ДЛЯ КОНКРЕТНОГО АККАУНТА
        """
        logger.step("Активация", f"окна для аккаунта {account_id}...")
        
        # Очищаем кэш перед поиском (чтобы найти новое окно)
        self.window_finder.clear_account_window(account_id)
        
        success = self.window_finder.activate_window_for_account(account_id, timeout=30)
        
        if success:
            logger.success(f"Окно для аккаунта {account_id} активировано")
        else:
            logger.warning(f"Не удалось активировать окно для аккаунта {account_id}")
        
        return success

    def _enter_credentials(self, account_id: int, username: str, password: str, code: str, hwnd: int) -> bool:
        logger.info(f"Ввод: {username}")
        
        try:
            # ✅ АКТИВАЦИЯ ОКНА ПЕРЕД ВВОДОМ
            logger.step("Активация", "...")
            
            if not self.window_finder.activate_window(hwnd):
                logger.warning("Активация не удалась, пробуем ввод...")
            
            time.sleep(0.3)
            
            # Быстрый ввод
            logger.debug("Ввод логина...")
            pyautogui.write(username, interval=0.03)
            time.sleep(0.2)
            pyautogui.press('tab')
            time.sleep(0.2)
            
            logger.debug("Ввод пароля...")
            pyautogui.write(password, interval=0.03)
            time.sleep(0.2)
            pyautogui.press('enter')
            
            logger.success("Логин/пароль введены")
            
            # ✅ УМЕНЬШЕНА ЗАДЕРЖКА
            time.sleep(config.DELAY_AFTER_LOGIN)
            
            # Переход к 2FA
            logger.debug("Переход к 2FA...")
            for i in range(4):
                pyautogui.press('tab')
                time.sleep(0.15)
            
            # Ввод 2FA
            logger.debug(f"Ввод 2FA: {code}")
            pyautogui.write(code, interval=0.03)
            time.sleep(0.2)
            pyautogui.press('enter')
            
            logger.success("2FA введён")
            return True

        except Exception as e:
            logger.error(f"Ввод данных: {e}")
            return False

    def _save_session_after_login(self, username: str):
        if not config.SAVE_SESSIONS:
            return
        
        try:
            session_data = {
                'username': username,
                'login_time': datetime.now().isoformat(),
                'steam_guard_required': config.STEAM_GUARD_REQUIRED,
            }
            
            if self.session_manager.save_session(username, session_data):
                logger.debug("Session сохранён")
            
        except Exception as e:
            logger.error(f"Ошибка session: {e}")

    def _try_load_session(self, username: str) -> bool:
        if not config.LOAD_SESSIONS:
            return False
        
        try:
            session = self.session_manager.load_session(username)
            
            if session:
                age = self.session_manager.get_session_age(username)
                logger.info(f"Session загружен ({age})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка session: {e}")
            return False

    def _wait_for_cs2_for_account(self, account_id: int, timeout: int = 180) -> bool:
        return self.pm.wait_for_cs2_and_close_library(account_id, timeout)

    def _scan_mafiles(self) -> Dict[str, Dict[str, str]]:
        result = {}
        mafiles_dir = config.MAFILES_DIR
        if not os.path.exists(mafiles_dir):
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
                logger.error(f"maFile {filename}: {e}")
        return result

    def import_from_logpass(self, logpass_file: str = None) -> int:
        if logpass_file is None:
            logpass_file = os.path.join(config.BASE_DIR, 'logpass.txt')
        if not os.path.exists(logpass_file):
            logger.error("logpass.txt не найден")
            return 0
        mafiles_map = self._scan_mafiles()
        count = 0
        with open(logpass_file, 'r', encoding='utf-8') as f:
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
                    logger.info(f"Уже в базе: {username}")
                    continue
                acc_id = self.db.add_account(username, password, ma_file_path, steam_id)
                if acc_id > 0:
                    mafile_status = " + maFile" if ma_file_path else " ⚠️ без maFile"
                    logger.info(f"Импорт: {username}{mafile_status}")
                    count += 1
        logger.success(f"Импортировано: {count}")
        return count

    def start_accounts_sequential(self, account_ids: List[int], progress_callback=None):
        def run_sequential():
            total = len(account_ids)
            logger.info(f"Запуск {total} аккаунтов (ПОСЛЕДОВАТЕЛЬНО)...")
            
            # Оптимизация
            logger.step("Оптимизация", "...")
            self.pm.optimize_once()
            
            # Очистка ТОЛЬКО CS2 (Steam оставляем!)
            logger.step("Очистка", "CS2...")
            self.pm.kill_all_cs2()
            time.sleep(2)
            
            # Очистка трекера процессов И ОКОН
            self.pm.clear_cs2_tracker()
            self.window_finder.clear_all_windows()  # ✅ Очистка кэша окон
            
            for i, acc_id in enumerate(account_ids):
                logger.info("=" * 60)
                logger.info(f"АККАУНТ {i+1}/{total}")
                logger.info("=" * 60)
                
                acc = self.get_account(acc_id)
                if acc:
                    acc.status = AccountStatus.STARTING
                    self.db.update_account(acc)
                
                # Запуск с авто-восстановлением
                success = self._start_account_with_retry(acc_id, account_index=i)
                
                if not success:
                    logger.error(f"Аккаунт {i+1} НЕ запущен")
                    continue
                
                # ОЖИДАНИЕ CS2 ПЕРЕД СЛЕДУЮЩИМ
                logger.info(f"Ожидание CS2 для аккаунта {i+1} ({config.CS2_LOAD_SECONDS}с)...")
                cs2_success = self._wait_for_cs2_for_account(acc_id, timeout=180)
                
                if cs2_success:
                    logger.success(f"Аккаунт {i+1} ПОЛНОСТЬЮ готов")
                    logger.success("Библиотека закрыта")
                    logger.success("Окно позиционировано")
                    
                    if config.VERIFY_BES_APPLICATION:
                        logger.success("BES применён")
                else:
                    logger.error(f"CS2 для аккаунта {i+1} не загрузился")
                
                # Задержка перед следующим
                if i < total - 1:
                    logger.info(f"Ожидание перед следующим ({config.ACCOUNTS_LAUNCH_DELAY}s)...")
                    time.sleep(config.ACCOUNTS_LAUNCH_DELAY)
            
            # ФИНАЛ
            logger.info("=" * 60)
            logger.success(f"ВСЕ {total} АККАУНТОВ ОБРАБОТАНЫ!")
            
            total_cs2 = self.pm.get_total_cs2_count()
            logger.info(f"Процессы CS2: {total_cs2}/{total}")
            
            if total_cs2 == total:
                logger.success("Все процессы CS2 запущены")
            else:
                logger.warning(f"Ожидается {total}, найдено {total_cs2}")
            
            # Проверка окон
            window_verification = self.pm.verify_all_windows()
            verified_count = sum(1 for v in window_verification.values() if v)
            logger.info(f"Окна проверены: {verified_count}/{total}")
            
            logger.info("=" * 60)
            
            active_cs2 = sum(1 for proc in psutil.process_iter(['name']) if proc.info['name'] and 'cs2' in proc.info['name'].lower())
            logger.info(f"Активных CS2: {active_cs2}")
        
        threading.Thread(target=run_sequential, daemon=True).start()

    def _start_account_with_retry(self, account_id: int, account_index: int = 0, max_retries: int = None) -> bool:
        """Запуск аккаунта с авто-восстановлением"""
        if max_retries is None:
            max_retries = config.MAX_ACCOUNT_RETRIES
        
        for attempt in range(max_retries + 1):
            success = self.start_account(account_id, account_index)
            
            if success:
                return True
            
            if attempt < max_retries:
                logger.warning(f"Попытка {attempt + 1} не удалась, повтор...")
                time.sleep(5)
        
        return False

    def start_account(self, account_id: int, account_index: int = 0) -> bool:
        account = self.get_account(account_id)
        if not account:
            return False
        
        account.status = AccountStatus.STARTING
        self.db.update_account(account)
        logger.info(f"Запуск: {account.username}")
        
        # Проверка session
        if self._try_load_session(account.username):
            logger.info("Session найден")
        
        if not account.ma_file_path:
            logger.error("Нет maFile")
            account.status = AccountStatus.ERROR
            self.db.update_account(account)
            return False
        
        try:
            with open(account.ma_file_path, 'r', encoding='utf-8') as f:
                ma_data = json.load(f)
            shared_secret = ma_data.get('shared_secret')
        except Exception as e:
            logger.error(f"Ошибка maFile: {e}")
            account.status = AccountStatus.ERROR
            self.db.update_account(account)
            return False
        
        twofactor_code = self._generate_2fa_code(shared_secret)
        logger.info(f"2FA: {twofactor_code}")
        
        steam_path = self.pm.find_steam_path()
        if not steam_path:
            logger.error("Steam не найден")
            return False
        
        steam_data_dir = os.path.join(config.BASE_DIR, 'steam_data', account.username)
        os.makedirs(steam_data_dir, exist_ok=True)
        
        ipc_name = self.pm.generate_ipc_name(account_id, account.username)
        logger.info(f"IPC: {ipc_name}")
        
        steam_id = int(account.steam_id) if account.steam_id else None
        
        window_position = self.pm.get_account_window_position(account_index)
        logger.info(f"Позиция сетки: {window_position}")
        
        logger.step("Запуск", "Steam + CS2...")
        
        try:
            process, pid = self.pm.start_steam_with_cs2(
                account_id=account_id,
                ipc_name=ipc_name,
                steam_data_dir=steam_data_dir,
                username=account.username,
                steam_id=steam_id,
                window_position=window_position
            )
            if not pid:
                return False
            self.steam_instances[account_id] = (process, ipc_name, pid)
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return False
        
        # ✅ ПОИСК И АКТИВАЦИЯ ОКНА ДЛЯ ЭТОГО АККАУНТА
        logger.step("Поиск", "окна входа...")
        login_window = self.window_finder.find_login_window_for_account(account_id, timeout=config.TIMEOUT_STEAM_WINDOW)
        
        if not login_window:
            logger.error("Окно не найдено")
            return False
        
        logger.success("Окно найдено")
        
        # ✅ АКТИВАЦИЯ ОКНА
        if not self.window_finder.activate_window(login_window):
            logger.warning("Активация не удалась, пробуем ввод...")
        
        logger.step("Ввод", "данных...")
        if not self._enter_credentials(account_id, account.username, account.password, twofactor_code, login_window):
            return False
        
        logger.info(f"Ожидание после 2FA ({config.DELAY_AFTER_2FA}s)...")
        time.sleep(config.DELAY_AFTER_2FA)
        
        # Сохранение session
        self._save_session_after_login(account.username)
        
        logger.success(f"Аккаунт {account.username} запущен")
        return True

    def get_all(self) -> List[Account]:
        return self.db.get_accounts()

    def get_account(self, account_id: int) -> Optional[Account]:
        for acc in self.get_all():
            if acc.id == account_id:
                return acc
        return None

    def stop_all(self):
        logger.step("Остановка", "...")
        self.pm.kill_all_instances()
        for acc in self.get_all():
            acc.status = AccountStatus.STOPPED
            self.db.update_account(acc)
        self._stop_flags.clear()
        logger.success("Остановлено")
    
    def get_launch_stats(self) -> Dict:
        return {}


account_manager = AccountManager(None, None, None)