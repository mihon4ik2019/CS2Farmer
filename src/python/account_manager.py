import os
import time
import threading
import json
import subprocess
import pyautogui
import win32gui
import win32con
import win32process
import win32api
import base64
import hmac
import hashlib
import struct
import psutil
import random
import shutil
import tempfile
import winreg
from datetime import datetime, timedelta
from typing import List, Optional, Dict

from .database import Database
from .process_manager import ProcessManager
from .ban_checker import BanChecker
from .models import Account, AccountStatus

class AccountManager:
    def __init__(self, db: Database, pm: ProcessManager, ban_checker: BanChecker):
        self.db = db
        self.pm = pm
        self.ban_checker = ban_checker
        self._stop_flags = {}
        self._last_attempt = {}
        self._rate_limit_delay = timedelta(minutes=10)
        self.bes_path = self._find_bes()
        self.steam_instances = {}

    def _find_bes(self) -> Optional[str]:
        possible_paths = [
            r"C:\Users\mihon\Desktop\CS2Farmer\BES\BES.exe",
            r"C:\Program Files\BES\BES.exe",
            r"C:\Program Files (x86)\BES\BES.exe",
            os.path.join(os.path.dirname(__file__), '..', '..', 'BES', 'BES.exe'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'bes', 'BES.exe'),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                print(f"[AccountManager] ✅ BES найден: {path}")
                return path
        print(f"[AccountManager] ⚠️ BES не найден. CPU не будет ограничиваться.")
        return None

    def _apply_bes_to_process(self, process_name: str = "cs2.exe", limit: int = 50):
        if not self.bes_path:
            return False
        try:
            subprocess.Popen([self.bes_path, "--process", process_name, "--limit", str(limit)],
                           shell=True,
                           creationflags=subprocess.CREATE_NO_WINDOW)
            print(f"[AccountManager] ✅ BES применён к {process_name} (лимит {limit}%)")
            return True
        except Exception as e:
            print(f"[AccountManager] ❌ Ошибка запуска BES: {e}")
            return False

    def _generate_2fa_code(self, shared_secret: str) -> str:
        time.sleep(random.uniform(0.1, 0.5))
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

    def _fix_steamwebhelper(self):
        print(f"[AccountManager] 🔧 Проверка steamwebhelper...")
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and 'steamwebhelper' in proc.info['name'].lower():
                    print(f"[AccountManager] Завершение steamwebhelper PID: {proc.info['pid']}")
                    proc.terminate()
                    time.sleep(1)
                    if proc.is_running():
                        proc.kill()
        except Exception as e:
            print(f"[AccountManager] Ошибка при завершении steamwebhelper: {e}")
        print(f"[AccountManager] ✅ Проверка завершена")

    def _fix_steam_protocol(self):
        """Исправление ассоциации протокола steam:// в реестре Windows"""
        print(f"[AccountManager] 🔧 Проверка протокола steam://...")
        steam_path = self.pm.find_steam_path()
        if steam_path:
            try:
                subprocess.run([steam_path, "-register"], check=True, capture_output=True)
                print(f"[AccountManager] ✅ Протокол steam:// перерегистрирован")
            except Exception as e:
                print(f"[AccountManager] ⚠️ Ошибка перерегистрации протокола: {e}")

    def _check_vc_redist(self) -> bool:
        """Проверка наличия Visual C++ Redistributable (x64)"""
        try:
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    subkey_name = winreg.EnumKey(key, i)
                    with winreg.OpenKey(key, subkey_name) as subkey:
                        try:
                            display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                            if "Microsoft Visual C++ 2015-2022 Redistributable (x64)" in display_name:
                                print(f"[AccountManager] ✅ Visual C++ Redistributable найден")
                                return True
                        except:
                            continue
            print(f"[AccountManager] ⚠️ Visual C++ Redistributable не найден")
            return False
        except Exception as e:
            print(f"[AccountManager] ❌ Ошибка проверки VC++: {e}")
            return False

    def _verify_cs2_binary(self) -> bool:
        """Проверка, что cs2.exe существует и доступен для запуска"""
        steam_path = self.pm.find_steam_path()
        if not steam_path:
            return False
        steam_dir = os.path.dirname(steam_path)
        cs2_path = os.path.join(steam_dir, "steamapps", "common", "Counter-Strike Global Offensive",
                                "game", "bin", "win64", "cs2.exe")
        if not os.path.exists(cs2_path):
            print(f"[AccountManager] ❌ cs2.exe не найден по пути: {cs2_path}")
            return False
        if not os.access(cs2_path, os.X_OK):
            print(f"[AccountManager] ⚠️ Нет прав на выполнение cs2.exe")
            return False
        print(f"[AccountManager] ✅ cs2.exe доступен: {cs2_path}")
        return True

    def _ensure_cs2_normal_privileges(self):
        """Убирает флаг 'Запуск от имени администратора' для cs2.exe, если он был установлен"""
        steam_path = self.pm.find_steam_path()
        if not steam_path:
            return False
        steam_dir = os.path.dirname(steam_path)
        cs2_path = os.path.join(steam_dir, "steamapps", "common", "Counter-Strike Global Offensive",
                                "game", "bin", "win64", "cs2.exe")
        if not os.path.exists(cs2_path):
            return False
        try:
            # Удаляем запись из реестра, если она есть
            reg_path = f"HKCU\\Software\\Microsoft\\Windows NT\\CurrentVersion\\AppCompatFlags\\Layers"
            cmd = f'reg delete "{reg_path}" /v "{cs2_path}" /f 2>nul'
            subprocess.run(cmd, shell=True)
            print(f"[AccountManager] ✅ Флаг администратора для cs2.exe снят")
            return True
        except Exception as e:
            print(f"[AccountManager] ⚠️ Не удалось снять флаг администратора: {e}")
            return False

    def _find_window_by_title_contains(self, texts, timeout=60, interval=2):
        print(f"[AccountManager] 🔍 Поиск окна по заголовкам {texts} (таймаут {timeout} сек)")
        start = time.time()
        attempt = 0
        while time.time() - start < timeout:
            attempt += 1
            all_windows = []
            def debug_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title:
                        windows.append(f"HWND {hwnd}: {title}")
            win32gui.EnumWindows(debug_callback, all_windows)
            if attempt % 5 == 0:
                print(f"[AccountManager] Текущие видимые окна (первые 10): {all_windows[:10]}")

            def enum_callback(hwnd, windows):
                title = win32gui.GetWindowText(hwnd).lower()
                for t in texts:
                    if t.lower() in title:
                        windows.append((hwnd, title))
                        return
            windows = []
            win32gui.EnumWindows(enum_callback, windows)
            if windows:
                hwnd, title = windows[0]
                print(f"[AccountManager] ✅ Окно найдено на попытке {attempt}: HWND {hwnd}, заголовок: '{title}'")
                return hwnd
            time.sleep(interval)
        print(f"[AccountManager] ❌ Окно не найдено за {timeout} секунд")
        return None

    def _find_login_window(self, timeout=60):
        return self._find_window_by_title_contains(["войдите", "steam", "login"], timeout)

    def _find_library_window(self, timeout=60):
        return self._find_window_by_title_contains(["библиотека", "library", "steam"], timeout)

    def _enter_credentials(self, username, password, code):
        print(f"[AccountManager] 👤 Начинаем ввод данных")
        time.sleep(3)
        print(f"[AccountManager] ⌨️ Ввод логина: '{username}'")
        pyautogui.write(username, interval=0.1)
        time.sleep(1)
        pyautogui.press('tab')
        print(f"[AccountManager] ⏹️ Tab")
        time.sleep(1)
        print(f"[AccountManager] ⌨️ Ввод пароля: {'*' * len(password)}")
        pyautogui.write(password, interval=0.1)
        time.sleep(1)
        pyautogui.press('enter')
        print(f"[AccountManager] ↵ Нажатие Enter (отправка логина)")
        print(f"[AccountManager] ⏳ Ожидание 15 секунд для появления запроса 2FA...")
        time.sleep(15)
        for i in range(4):
            pyautogui.press('tab')
            print(f"[AccountManager] Tab {i+1}/4")
            time.sleep(0.5)
        print(f"[AccountManager] ⌨️ Ввод 2FA кода: {code}")
        pyautogui.write(code, interval=0.1)
        time.sleep(1)
        pyautogui.press('enter')
        print(f"[AccountManager] ✅ 2FA код отправлен")
        return True

    def _scan_mafiles(self) -> Dict[str, Dict[str, str]]:
        result = {}
        mafiles_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'mafiles')
        if not os.path.exists(mafiles_dir):
            print(f"[AccountManager] mafiles directory not found: {mafiles_dir}")
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
                    print(f"[AccountManager] maFile {filename} has no account_name")
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
                print(f"[AccountManager] Found maFile for {username} with SteamID {steam_id}")
            except Exception as e:
                print(f"[AccountManager] Error reading maFile {filename}: {e}")
                continue
        return result

    def import_from_file(self, file_path: str) -> int:
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
                    acc = existing[0]
                    need_update = False
                    if steam_id and acc.steam_id != steam_id:
                        acc.steam_id = steam_id
                        need_update = True
                    if ma_file_path and acc.ma_file_path != ma_file_path:
                        acc.ma_file_path = ma_file_path
                        need_update = True
                    if need_update:
                        self.db.update_account(acc)
                        print(f"[AccountManager] Updated existing account {username}")
                    continue
                acc_id = self.db.add_account(username, password, ma_file_path)
                if steam_id:
                    acc = self.get_account(acc_id)
                    if acc:
                        acc.steam_id = steam_id
                        self.db.update_account(acc)
                count += 1
                print(f"[AccountManager] Imported new account {username}")
        return count

    def get_all(self) -> List[Account]:
        return self.db.get_accounts()

    def get_account(self, account_id: int) -> Optional[Account]:
        for acc in self.get_all():
            if acc.id == account_id:
                return acc
        return None

    def start_accounts_sequential(self, account_ids: List[int], progress_callback=None):
        def run_sequential():
            total = len(account_ids)
            for i, acc_id in enumerate(account_ids):
                print(f"[AccountManager] ===== Запуск аккаунта {i+1}/{total} =====")
                self._fix_steamwebhelper()
                self._fix_steam_protocol()
                # Убираем флаг администратора для cs2.exe (важно!)
                self._ensure_cs2_normal_privileges()
                success = self.start_account(acc_id)
                if progress_callback:
                    progress_callback(i + 1, total)
                if i < total - 1:
                    wait_time = 40
                    print(f"[AccountManager] Ожидание {wait_time} секунд перед следующим запуском...")
                    time.sleep(wait_time)
            print(f"[AccountManager] ✅ Все {total} аккаунтов обработаны")
        threading.Thread(target=run_sequential, daemon=True).start()

    def _launch_cs2_secure(self, steam_path, ipc_name, steam_data_dir) -> bool:
        """
        Запуск CS2 с обычными правами (не от администратора), чтобы избежать IPC-конфликтов.
        """
        steam_dir = os.path.dirname(steam_path)
        cs2_exe = os.path.join(steam_dir, "steamapps", "common", "Counter-Strike Global Offensive",
                               "game", "bin", "win64", "cs2.exe")
        
        # Способ 1: Запуск через Steam с параметрами (игра запускается с обычными правами)
        try:
            print(f"[AccountManager] 🎮 Способ 1: Запуск через Steam с параметрами")
            cs2_cmd = [
                steam_path,
                "-master_ipc_name_override", ipc_name,
                "-fulldir", steam_data_dir,
                "-applaunch", "730",
                "+engine_no_focus_sleep", "120"
            ]
            subprocess.Popen(cs2_cmd, shell=False)
            print(f"[AccountManager] ✅ Команда запуска CS2 выполнена")
            return True
        except Exception as e:
            print(f"[AccountManager] ⚠️ Способ 1 не сработал: {e}")

        # Способ 2: Прямой запуск cs2.exe с обычными правами (если способ 1 не сработал)
        if os.path.exists(cs2_exe):
            try:
                print(f"[AccountManager] 🎮 Способ 2: Прямой запуск cs2.exe (обычные права)")
                cs2_params = "-windowed -w 640 -h 480 -novid -nojoy -nosound +engine_no_focus_sleep 120"
                # Запускаем без runas, чтобы игра имела обычные права
                subprocess.Popen([cs2_exe] + cs2_params.split())
                print(f"[AccountManager] ✅ Прямой запуск выполнен")
                return True
            except Exception as e:
                print(f"[AccountManager] ⚠️ Способ 2 не сработал: {e}")

        # Способ 3: Steam URL с параметрами (запасной)
        try:
            print(f"[AccountManager] 🎮 Способ 3: Запуск через steam:// с параметрами")
            cs2_options = "-swapcores -noqueuedload -vrdisable -windowed -nopreload -limitvsconst -softparticlesdefaultoff -nohltv -noaafonts -nosound -novid +violence_hblood 0 +sethdmodels 0 +mat_disable_fancy_blending 1 +r_dynamic 0 +engine_no_focus_sleep 120"
            encoded_options = cs2_options.replace(' ', '/')
            steam_uri = f"steam://rungameid/730//{encoded_options}"
            cmd = f'cmd /c start "" "{steam_uri}"'
            subprocess.Popen(cmd, shell=True)
            print(f"[AccountManager] ✅ Steam URL запущен")
            return True
        except Exception as e:
            print(f"[AccountManager] ❌ Все способы запуска не удались: {e}")
            return False

    def start_account(self, account_id: int) -> bool:
        account = self.get_account(account_id)
        if not account:
            print(f"[AccountManager] ❌ Account {account_id} not found")
            return False
        if account.status != AccountStatus.STOPPED:
            print(f"[AccountManager] ⚠️ Account {account.username} is not stopped (status={account.status})")
            return False

        last = self._last_attempt.get(account_id)
        if last and datetime.now() - last < self._rate_limit_delay:
            print(f"[AccountManager] ⏳ Too many attempts for {account.username}, please wait")
            account.status = AccountStatus.ERROR
            account.status_message = "Превышен лимит запросов Steam. Подождите 10 минут."
            self.db.update_account(account)
            return False

        if account.steam_id:
            banned = self.ban_checker.check_account(account.steam_id)
            if banned:
                account.status = AccountStatus.BANNED
                self.db.update_account(account)
                print(f"[AccountManager] 🚫 Account {account.username} is banned")
                return False

        # Предварительные проверки
        self._check_vc_redist()
        self._verify_cs2_binary()

        account.status = AccountStatus.STARTING
        self.db.update_account(account)
        print(f"[AccountManager] 🚀 Starting account {account.username}")

        if not account.ma_file_path:
            print(f"[AccountManager] ❌ No maFile for {account.username}, cannot login with 2FA")
            account.status = AccountStatus.ERROR
            account.status_message = "No maFile provided"
            self.db.update_account(account)
            return False

        try:
            with open(account.ma_file_path, 'r', encoding='utf-8') as f:
                ma_data = json.load(f)
            shared_secret = ma_data.get('shared_secret')
            if not shared_secret:
                raise ValueError("No shared_secret in maFile")
        except Exception as e:
            print(f"[AccountManager] ❌ Failed to read maFile: {e}")
            account.status = AccountStatus.ERROR
            account.status_message = f"Invalid maFile: {e}"
            self.db.update_account(account)
            return False

        twofactor_code = self._generate_2fa_code(shared_secret)
        print(f"[AccountManager] ✅ 2FA code generated: {twofactor_code}")

        self._last_attempt[account_id] = datetime.now()

        steam_path = self.pm.find_steam_path()
        if not steam_path:
            print(f"[AccountManager] ❌ Steam not found")
            account.status = AccountStatus.ERROR
            account.status_message = "Steam not found"
            self.db.update_account(account)
            return False

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        steam_data_dir = os.path.join(base_dir, 'steam_data', account.username)
        os.makedirs(steam_data_dir, exist_ok=True)
        print(f"[AccountManager] 📁 Папка данных Steam: {steam_data_dir}")

        windows_username = os.getlogin()
        random_suffix = random.randint(1000, 9999)
        raw_ipc = f"steam_{windows_username}_{account.username}_{account_id}_{random_suffix}"
        ipc_name = raw_ipc[:60]

        # Запуск Steam через bat-файл с правами администратора
        bat_content = f'start "" "{steam_path}" -master_ipc_name_override {ipc_name} -fulldir "{steam_data_dir}" -no-cef-sandbox'
        if random.choice([True, False]):
            bat_content += " -nofriendsui"
        if random.choice([True, False]):
            bat_content += " -vgui"
        bat_path = os.path.join(tempfile.gettempdir(), f"steam_launch_{account_id}.bat")
        with open(bat_path, "w") as f:
            f.write(bat_content)

        print(f"[AccountManager] 🖥️ Запуск изолированного Steam с IPC: {ipc_name} (от имени администратора)")
        pid = None
        try:
            win32api.ShellExecute(0, "runas", bat_path, None, None, win32con.SW_SHOW)
            print(f"[AccountManager] ✅ Команда запуска Steam выполнена (runas)")
        except Exception as e:
            print(f"[AccountManager] ❌ Ошибка запуска через runas: {e}, пробуем обычный Popen")
            cmd = f'"{steam_path}" -master_ipc_name_override {ipc_name} -fulldir "{steam_data_dir}" -no-cef-sandbox'
            if random.choice([True, False]):
                cmd += " -nofriendsui"
            if random.choice([True, False]):
                cmd += " -vgui"
            process = subprocess.Popen(cmd, shell=True)
            pid = process.pid
            self.steam_instances[account_id] = (process, ipc_name, pid)

        if pid is None:
            time.sleep(5)
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['name'] and proc.info['name'].lower() == 'steam.exe':
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if ipc_name in cmdline:
                        pid = proc.info['pid']
                        print(f"[AccountManager] Найден Steam с PID {pid} для IPC {ipc_name}")
                        break

        if pid:
            self.steam_instances[account_id] = (None, ipc_name, pid)

        print(f"[AccountManager] ✅ Изолированный Steam запущен, PID: {pid}")
        time.sleep(15)

        if not psutil.pid_exists(pid):
            print(f"[AccountManager] ❌ Процесс Steam с PID {pid} внезапно завершился")
            account.status = AccountStatus.ERROR
            account.status_message = "Steam process died"
            self.db.update_account(account)
            return False

        # ПОИСК ОКНА ВХОДА
        print(f"[AccountManager] 🔍 Начинаем поиск окна входа по заголовку...")
        login_window = None
        for attempt in range(6):
            login_window = self._find_login_window(timeout=10)
            if login_window:
                break
            print(f"[AccountManager] Попытка {attempt+1}/6: окно входа не найдено, ждём...")
            time.sleep(10)
        if not login_window:
            print(f"[AccountManager] ❌ Окно входа не найдено после 60 секунд, прекращаем")
            account.status = AccountStatus.ERROR
            account.status_message = "Login window not found"
            self.db.update_account(account)
            return False

        print(f"[AccountManager] ✅ Окно входа найдено, активируем его")
        win32gui.ShowWindow(login_window, win32con.SW_RESTORE)
        win32gui.SetForegroundWindow(login_window)
        time.sleep(3)
        try:
            self._enter_credentials(account.username, account.password, twofactor_code)
            print(f"[AccountManager] ✅ Данные введены, ожидание входа...")
            time.sleep(20)
        except Exception as e:
            print(f"[AccountManager] ❌ Ошибка при вводе данных: {e}")
            account.status = AccountStatus.ERROR
            account.status_message = str(e)
            self.db.update_account(account)
            return False

        if not psutil.pid_exists(pid):
            print(f"[AccountManager] ❌ Процесс Steam с PID {pid} завершился после входа")
            account.status = AccountStatus.ERROR
            account.status_message = "Steam crashed after login"
            self.db.update_account(account)
            return False

        print(f"[AccountManager] 🔍 Ожидание окна библиотеки Steam...")
        library_window = None
        for attempt in range(12):
            library_window = self._find_library_window(timeout=5)
            if library_window:
                break
            print(f"[AccountManager] Попытка {attempt+1}/12: окно библиотеки не найдено, ждём...")
            time.sleep(5)
        if library_window:
            print(f"[AccountManager] ✅ Окно библиотеки найдено, вход выполнен")
        else:
            print(f"[AccountManager] ⚠️ Окно библиотеки не найдено, но продолжаем...")

        print(f"[AccountManager] ⏳ Дополнительное ожидание 30 секунд для полной загрузки Steam...")
        time.sleep(30)

        # ЗАПУСК CS2 - ТЕПЕРЬ С ОБЫЧНЫМИ ПРАВАМИ
        cs2_started = self._launch_cs2_secure(steam_path, ipc_name, steam_data_dir)

        # Ожидание появления процесса CS2
        print(f"[AccountManager] ⏳ Ожидание запуска CS2 (до 60 секунд)...")
        cs2_found = False
        for attempt in range(30):
            time.sleep(2)
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and proc.info['name'].lower() == 'cs2.exe':
                    cs2_found = True
                    print(f"[AccountManager] ✅ Процесс CS2 обнаружен на попытке {attempt+1} (PID {proc.info['pid']})")
                    break
            if cs2_found:
                break
            print(f"[AccountManager] Попытка {attempt+1}/30: CS2 не обнаружен, ждём...")

        if not cs2_found:
            print(f"[AccountManager] ⚠️ Процесс CS2 не обнаружен после запуска")
            time.sleep(5)
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] and proc.info['name'].lower() == 'cs2.exe':
                    cs2_found = True
                    print(f"[AccountManager] ✅ Процесс CS2 найден при повторной проверке (PID {proc.info['pid']})")
                    break
            if not cs2_found:
                print(f"[AccountManager] ❌ CS2 действительно не запустился")

        account.status = AccountStatus.IN_GAME
        account.last_login = datetime.now()
        self.db.update_account(account)
        print(f"[AccountManager] ✅ Account {account.username} started successfully (Steam PID {pid})")

        time.sleep(8)
        self._apply_bes_to_process("cs2.exe", 50)

        stop_event = threading.Event()
        self._stop_flags[account_id] = stop_event
        def update_time():
            while not stop_event.wait(60):
                account.play_time_minutes += 1
                self.db.update_account(account)
        threading.Thread(target=update_time, daemon=True).start()
        return True

    def stop_account(self, account_id: int):
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
                    print(f"[AccountManager] 🛑 Завершён экземпляр Steam для {account.username} (PID {pid})")
                except:
                    pass
                del self.steam_instances[account_id]

            if account_id in self._stop_flags:
                self._stop_flags[account_id].set()
                del self._stop_flags[account_id]

    def stop_all(self):
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
        print(f"[AccountManager] All accounts stopped")