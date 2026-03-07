"""
Database - УПРОЩЁННЫЙ (без мастер-пароля)
"""
import sqlite3
import os
import threading
from typing import List, Optional
from .models import Account, AccountStatus


class Database:
    def __init__(self, db_path: str, master_password: str = "cs2farmer"):
        self.db_path = db_path
        self.master_password = master_password
        self.lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        """Инициализация базы данных"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица аккаунтов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                steam_id TEXT,
                ma_file_path TEXT,
                status TEXT DEFAULT 'STOPPED',
                status_message TEXT,
                play_time_minutes INTEGER DEFAULT 0,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица логов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER,
                message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_account(self, username: str, password: str, ma_file_path: str = None, steam_id: str = None) -> int:
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO accounts (username, password, ma_file_path, steam_id, status, play_time_minutes)
                    VALUES (?, ?, ?, ?, ?, 0)
                ''', (username, password, ma_file_path, steam_id, AccountStatus.STOPPED.value))
                
                conn.commit()
                account_id = cursor.lastrowid
                return account_id
            except sqlite3.IntegrityError:
                return -1
            finally:
                conn.close()
    
    def get_accounts(self) -> List[Account]:
        """Получение всех аккаунтов"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM accounts')
            rows = cursor.fetchall()
            conn.close()
            
            accounts = []
            for row in rows:
                account = Account(
                    id=row[0],
                    username=row[1],
                    password=row[2],
                    steam_id=row[3],
                    ma_file_path=row[4],
                    status=AccountStatus(row[5]),
                    status_message=row[6],
                    play_time_minutes=row[7],
                    last_login=row[8]
                )
                accounts.append(account)
            
            return accounts
    
    def get_account(self, account_id: int) -> Optional[Account]:
        """Получение аккаунта по ID"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM accounts WHERE id = ?', (account_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return Account(
                    id=row[0],
                    username=row[1],
                    password=row[2],
                    steam_id=row[3],
                    ma_file_path=row[4],
                    status=AccountStatus(row[5]),
                    status_message=row[6],
                    play_time_minutes=row[7],
                    last_login=row[8]
                )
            return None
    
    def update_account(self, account: Account):
        """Обновление аккаунта"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE accounts SET
                    status = ?,
                    status_message = ?,
                    play_time_minutes = ?,
                    last_login = ?,
                    steam_id = ?,
                    ma_file_path = ?
                WHERE id = ?
            ''', (
                account.status.value,
                account.status_message,
                account.play_time_minutes,
                account.last_login,
                account.steam_id,
                account.ma_file_path,
                account.id
            ))
            
            conn.commit()
            conn.close()
    
    def delete_account(self, account_id: int) -> bool:
        """Удаление аккаунта"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM accounts WHERE id = ?', (account_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
            conn.close()
            
            return deleted
    
    def clear_all(self):
        """Очистка всех аккаунтов"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM accounts')
            conn.commit()
            conn.close()