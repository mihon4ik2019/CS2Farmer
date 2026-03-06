import sqlite3
from datetime import datetime
from typing import List, Optional
from .models import Account, AccountStatus, LobbyRole, MatchScoreMode
from .crypto_utils import CryptoUtils

class Database:
    def __init__(self, db_path: str, master_password: str):
        self.db_path = db_path
        self.master_password = master_password
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    ma_file_path TEXT,
                    steam_id TEXT,
                    status TEXT NOT NULL,
                    status_message TEXT,
                    last_login TEXT,
                    play_time_minutes INTEGER DEFAULT 0,
                    drop_today INTEGER DEFAULT 0,
                    drop_week INTEGER DEFAULT 0,
                    drop_month INTEGER DEFAULT 0,
                    drop_total INTEGER DEFAULT 0,
                    lobby_role TEXT DEFAULT 'none',
                    lobby_code TEXT,
                    team_index INTEGER DEFAULT -1,
                    anti_afk_enabled INTEGER DEFAULT 1,
                    match_score_mode TEXT DEFAULT '8:8'
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            cur = conn.execute("SELECT value FROM settings WHERE key = 'master_hash'")
            row = cur.fetchone()
            if not row:
                master_hash = CryptoUtils.hash_master_password(self.master_password)
                conn.execute("INSERT INTO settings (key, value) VALUES (?, ?)",
                             ('master_hash', master_hash))
                conn.commit()
            else:
                if not CryptoUtils.verify_master_password(self.master_password, row[0]):
                    raise ValueError("Неверный мастер-пароль")

    def change_master_password(self, new_password: str):
        accounts = self.get_accounts(decrypt=False)
        with sqlite3.connect(self.db_path) as conn:
            for acc in accounts:
                plain = CryptoUtils.decrypt(acc.password, self.master_password)
                new_enc = CryptoUtils.encrypt(plain, new_password)
                conn.execute("UPDATE accounts SET password = ? WHERE id = ?",
                             (new_enc, acc.id))
            new_hash = CryptoUtils.hash_master_password(new_password)
            conn.execute("UPDATE settings SET value = ? WHERE key = 'master_hash'",
                         (new_hash,))
            conn.commit()
        self.master_password = new_password

    def add_account(self, username: str, password: str,
                    ma_file_path: Optional[str] = None) -> int:
        encrypted = CryptoUtils.encrypt(password, self.master_password)
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "INSERT INTO accounts (username, password, ma_file_path, status) VALUES (?, ?, ?, ?)",
                (username, encrypted, ma_file_path, AccountStatus.STOPPED.value)
            )
            conn.commit()
            return cur.lastrowid

    def get_accounts(self, decrypt: bool = True) -> List[Account]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM accounts").fetchall()
            accounts = []
            for row in rows:
                password = row[2]
                if decrypt:
                    password = CryptoUtils.decrypt(password, self.master_password)
                status = AccountStatus.STOPPED
                if len(row) > 5 and row[5]:
                    try:
                        status = AccountStatus(row[5])
                    except ValueError:
                        pass
                status_message = row[6] if len(row) > 6 else None
                lobby_role = LobbyRole.NONE
                if len(row) > 13 and row[13]:
                    try:
                        lobby_role = LobbyRole(row[13])
                    except ValueError:
                        pass
                match_score_mode = MatchScoreMode.TIE_8_8
                if len(row) > 17 and row[17]:
                    try:
                        match_score_mode = MatchScoreMode(row[17])
                    except ValueError:
                        pass
                acc = Account(
                    id=row[0],
                    username=row[1],
                    password=password,
                    ma_file_path=row[3],
                    steam_id=row[4],
                    status=status,
                    status_message=status_message,
                    last_login=datetime.fromisoformat(row[7]) if len(row) > 7 and row[7] else None,
                    play_time_minutes=row[8] if len(row) > 8 else 0,
                    drop_today=row[9] if len(row) > 9 else 0,
                    drop_week=row[10] if len(row) > 10 else 0,
                    drop_month=row[11] if len(row) > 11 else 0,
                    drop_total=row[12] if len(row) > 12 else 0,
                    lobby_role=lobby_role,
                    lobby_code=row[14] if len(row) > 14 else None,
                    team_index=row[15] if len(row) > 15 else -1,
                    anti_afk_enabled=bool(row[16]) if len(row) > 16 else True,
                    match_score_mode=match_score_mode
                )
                accounts.append(acc)
            return accounts

    def update_account(self, account: Account):
        password = account.password
        try:
            CryptoUtils.decrypt(password, self.master_password)
        except Exception:
            password = CryptoUtils.encrypt(password, self.master_password)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE accounts SET
                    password = ?,
                    ma_file_path = ?,
                    steam_id = ?,
                    status = ?,
                    status_message = ?,
                    last_login = ?,
                    play_time_minutes = ?,
                    drop_today = ?,
                    drop_week = ?,
                    drop_month = ?,
                    drop_total = ?,
                    lobby_role = ?,
                    lobby_code = ?,
                    team_index = ?,
                    anti_afk_enabled = ?,
                    match_score_mode = ?
                WHERE id = ?
            """, (
                password,
                account.ma_file_path,
                account.steam_id,
                account.status.value,
                account.status_message,
                account.last_login.isoformat() if account.last_login else None,
                account.play_time_minutes,
                account.drop_today,
                account.drop_week,
                account.drop_month,
                account.drop_total,
                account.lobby_role.value,
                account.lobby_code,
                account.team_index,
                int(account.anti_afk_enabled),
                account.match_score_mode.value,
                account.id
            ))
            conn.commit()

    def set_setting(self, key: str, value: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                         (key, value))
            conn.commit()

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
            return row[0] if row else default