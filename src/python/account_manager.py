"""
Account Manager - БЫСТРЫЙ + 100% НАДЁЖНЫЙ
Оптимизированный поиск + быстрый ввод
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
from typing import List, Optional, Dict

from .database import Database
from .process_manager import ProcessManager
from .ban_checker import BanChecker
from .models import Account, AccountStatus
from .logger import SecureLogger
from . import config

logger = SecureLogger()


class AccountManager:
    def __init__(self, db: Database, pm: ProcessManager, ban_checker: BanChecker):
        self.db = db
        self.pm = pm
        self.ban_checker = ban_checker
        self._stop_flags = {}
        self._rate_limit_delay = timedelta(minutes=config.RATE_LIMIT_DELAY_MINUTES)
        self.steam_instances = {}

    def _generate_2fa_code(self, shared_secret: str) -> str:
        """Генерация 2FA кода"""
        try:
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
        except Exception as e:
            logger.error(f"Ошибка 2FA: {e}")
            return ""

    def _activate_window_fast(self, hwnd: int) -> bool:
        """
        ✅ БЫСТРАЯ АКТИВАЦИЯ (3 попытки, 0.2с)
        """
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
                    logger.info(f"✅ Окно активировано")
                    time.sleep(0.3)
                    return True
            
            return False
        except:
            return False

    def _find_login_window_fast(self, timeout: int = 30) -> Optional[int]:
        """
        ✅ БЫСТРЫЙ ПОИСК ОКНА (30с, 0.1с интервал)
        """
        logger.info(f"🔍 Поиск окна входа ({timeout}s)...")
        
        start_time = time.time()
        titles = ['steam', 'войдите', 'вход', 'login', 'sign in', 'авторизация']
        
        while time.time() - start_time < timeout:
            found = []
            
            def enum_callback(hwnd, _):
                try:
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd).lower()
                        for t in titles:
                            if t in title:
                                found.append(hwnd)
                                return
                except:
                    pass
            
            win32gui.EnumWindows(enum_callback, None)
            
            if found:
                hwnd = found[0]
                if win32gui.IsWindowVisible(hwnd):
                    window_title = win32gui.GetWindowText(hwnd)
                    logger.info(f"✅ Окно найдено: '{window_title}'")
                    return hwnd
            
            time.sleep(0.1)  # ✅ БЫСТРЫЙ ИНТЕРВАЛ
        
        logger.error(f"❌ Окно не найдено за {timeout}s")
        return None

    def _enter_credentials_fast(self, username: str, password: str, code: str, hwnd: int) -> bool:
        """
        ✅ БЫСТРЫЙ ВВОД ДАННЫХ
        """
        logger.info(f"👤 Ввод: {username}")
        
        try:
            # 1. Активация
            logger.info("🔑 Активация...")
            self._activate_window_fast(hwnd)
            time.sleep(0.5)  # ✅ МИНИМАЛЬНАЯ ПАУЗА
            
            # 2. Логин
            logger.info("⌨️ Логин...")
            pyautogui.write(username, interval=0.03)  # ✅ БЫСТРЫЙ ВВОД
            time.sleep(0.3)
            pyautogui.press('tab')
            time.sleep(0.3)
            
            # 3. Пароль
            logger.info("⌨️ Пароль...")
            pyautogui.write(password, interval=0.03)
            time.sleep(0.3)
            pyautogui.press('enter')
            
            logger.info("✅ Логин/пароль введены")
            
            # 4. Ожидание 2FA
            time.sleep(config.DELAY_AFTER_LOGIN)
            
            # 5. 2FA
            logger.info("⌨️ 2FA...")
            for i in range(4):
                pyautogui.press('tab')
                time.sleep(0.2)
            
            pyautogui.write(code, interval=0.03)
            time.sleep(0.3)
            pyautogui.press('enter')
            
            logger.info("✅ 2FA введён")
            return True

        except Exception as e:
            logger.error(f"❌ Ввод: {e}")
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
                    logger.info(f"Уже: {username}")
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
            logger.info(f"🚀 Запуск {total} аккаунтов...")
            
            logger.info("⚡ Оптимизация...")
            self.pm.optimize_once()
            
            logger.info("🔧 Очистка CS2...")
            self.pm.kill_all_cs2()
            time.sleep(3)
            
            self.pm.clear_cs2_tracker()
            
            for i, acc_id in enumerate(account_ids):
                logger.info("=" * 60)
                logger.info(f"АККАУНТ {i+1}/{total}")
                logger.info("=" * 60)
                
                acc = self.get_account(acc_id)
                if acc:
                    acc.status = AccountStatus.STARTING
                    self.db.update_account(acc)
                
                success = self.start_account(acc_id, account_index=i)
                
                if not success:
                    logger.error(f"❌ Аккаунт {i+1} НЕ запущен")
                    continue
                
                if progress_callback:
                    progress_callback(i + 1, total)
                
                logger.info(f"⏳ Ожидание CS2 ({config.CS2_LOAD_SECONDS}с)...")
                cs2_success = self._wait_for_cs2_for_account(acc_id, timeout=180)
                
                if cs2_success:
                    logger.success(f"✅ Аккаунт {i+1} готов")
                    logger.success("🗑️ Библиотека закрыта")
                    logger.success("🪟 Окно позиционировано")
                else:
                    logger.error(f"❌ CS2 не загрузился")
                
                if i < total - 1:
                    logger.info(f"⏳ Ожидание ({config.ACCOUNTS_LAUNCH_DELAY}s)...")
                    time.sleep(config.ACCOUNTS_LAUNCH_DELAY)
            
            logger.info("=" * 60)
            logger.success(f"✅ ВСЕ {total} ЗАПУЩЕНЫ!")
            
            total_cs2 = self.pm.get_total_cs2_count()
            logger.info(f"📊 CS2: {total_cs2}/{total}")
            
            if total_cs2 == total:
                logger.success("✅ Все CS2 запущены")
            else:
                logger.warning(f"⚠️ {total_cs2}/{total}")
            
            logger.info("=" * 60)
            
            active_cs2 = sum(1 for proc in psutil.process_iter(['name']) 
                           if proc.info['name'] and 'cs2' in proc.info['name'].lower())
            logger.info(f"📊 Активных CS2: {active_cs2}")
        
        threading.Thread(target=run_sequential, daemon=True).start()

    def start_account(self, account_id: int, account_index: int = 0) -> bool:
        account = self.get_account(account_id)
        if not account:
            return False
        
        account.status = AccountStatus.STARTING
        self.db.update_account(account)
        logger.info(f"🚀 Запуск: {account.username}")
        
        if not account.ma_file_path:
            logger.error("❌ Нет maFile")
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
        logger.info(f"✅ 2FA: {twofactor_code}")
        
        steam_path = self.pm.find_steam_path()
        if not steam_path:
            return False
        
        steam_data_dir = os.path.join(config.BASE_DIR, 'steam_data', account.username)
        os.makedirs(steam_data_dir, exist_ok=True)
        
        ipc_name = self.pm.generate_ipc_name(account_id, account.username)
        logger.info(f"🏷️ IPC: {ipc_name}")
        
        steam_id = int(account.steam_id) if account.steam_id else None
        
        window_position = self.pm.get_account_window_position(account_index)
        logger.info(f"🪟 Позиция: {window_position}")
        
        logger.info("🎮 Запуск Steam + CS2...")
        
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
        
        # ✅ БЫСТРЫЙ ПОИСК ОКНА (30с)
        logger.info("🔍 Поиск окна входа...")
        login_window = self._find_login_window_fast(timeout=30)
        
        if not login_window:
            logger.error("❌ Окно не найдено")
            return False
        
        logger.info("✅ Окно найдено")
        
        # ✅ АКТИВАЦИЯ
        self._activate_window_fast(login_window)
        
        # ✅ ВВОД ДАННЫХ
        logger.info("🔐 Ввод данных...")
        if not self._enter_credentials_fast(account.username, account.password, twofactor_code, login_window):
            return False
        
        logger.info(f"⏳ Ожидание после 2FA ({config.DELAY_AFTER_2FA}s)...")
        time.sleep(config.DELAY_AFTER_2FA)
        
        logger.info(f"✅ {account.username} запущен")
        return True

    def get_all(self) -> List[Account]:
        return self.db.get_accounts()

    def get_account(self, account_id: int) -> Optional[Account]:
        for acc in self.get_all():
            if acc.id == account_id:
                return acc
        return None

    def stop_all(self):
        logger.info("⏹️ Остановка...")
        self.pm.kill_all_instances()
        for acc in self.get_all():
            acc.status = AccountStatus.STOPPED
            self.db.update_account(acc)
        self._stop_flags.clear()
        logger.success("✅ Остановлено")