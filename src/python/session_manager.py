"""
Session Manager - SESSION FILES (как в FSM Panel)
Сохранение и загрузка сессий Steam для быстрой загрузки
"""
import os
import pickle
import time
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from . import config


class SessionManager:
    """
    УПРАВЛЕНИЕ SESSION FILES
    Аналогично FSM Panel (.pkl файлы в папке sessions/)
    """
    
    def __init__(self):
        self.sessions_dir = config.SESSIONS_DIR
        os.makedirs(self.sessions_dir, exist_ok=True)
    
    def _get_session_path(self, username: str) -> str:
        """Получить путь к session файлу"""
        # Безопасное имя файла
        safe_username = hashlib.md5(username.encode()).hexdigest()[:16]
        return os.path.join(self.sessions_dir, f"{username}.pkl")
    
    def save_session(self, username: str, session_data: Dict[str, Any]) -> bool:
        """
        ✅ СОХРАНЕНИЕ SESSION ПОСЛЕ УСПЕШНОГО ВХОДА
        """
        try:
            session_path = self._get_session_path(username)
            
            # Данные сессии
            session = {
                'username': username,
                'timestamp': datetime.now(),
                'data': session_data,
                'version': 1,
            }
            
            # Сохранение в .pkl файл
            with open(session_path, 'wb') as f:
                pickle.dump(session, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            print(f"[SessionManager] ✅ Session сохранён: {session_path}")
            return True
            
        except Exception as e:
            print(f"[SessionManager] ❌ Ошибка сохранения: {e}")
            return False
    
    def load_session(self, username: str) -> Optional[Dict[str, Any]]:
        """
        ✅ ЗАГРУЗКА SESSION ПЕРЕД ВХОДОМ
        Returns: session_data или None
        """
        try:
            session_path = self._get_session_path(username)
            
            if not os.path.exists(session_path):
                print(f"[SessionManager] ℹ️ Session не найден: {username}")
                return None
            
            # Загрузка из .pkl файла
            with open(session_path, 'rb') as f:
                session = pickle.load(f)
            
            # Проверка срока действия (7 дней)
            timestamp = session.get('timestamp')
            if timestamp:
                age = datetime.now() - timestamp
                if age > timedelta(hours=config.SESSION_TIMEOUT_HOURS):
                    print(f"[SessionManager] ⚠️ Session устарел: {username}")
                    os.remove(session_path)
                    return None
            
            print(f"[SessionManager] ✅ Session загружен: {username}")
            return session.get('data')
            
        except Exception as e:
            print(f"[SessionManager] ❌ Ошибка загрузки: {e}")
            return None
    
    def delete_session(self, username: str) -> bool:
        """Удаление session файла"""
        try:
            session_path = self._get_session_path(username)
            if os.path.exists(session_path):
                os.remove(session_path)
                print(f"[SessionManager] 🗑️ Session удалён: {username}")
            return True
        except:
            return False
    
    def get_session_age(self, username: str) -> Optional[timedelta]:
        """Получить возраст сессии"""
        try:
            session_path = self._get_session_path(username)
            if not os.path.exists(session_path):
                return None
            
            with open(session_path, 'rb') as f:
                session = pickle.load(f)
            
            timestamp = session.get('timestamp')
            if timestamp:
                return datetime.now() - timestamp
            
            return None
        except:
            return None
    
    def list_sessions(self) -> list:
        """Список всех сохранённых сессий"""
        sessions = []
        try:
            for filename in os.listdir(self.sessions_dir):
                if filename.endswith('.pkl'):
                    username = filename[:-4]  # Убрать .pkl
                    age = self.get_session_age(username)
                    sessions.append({
                        'username': username,
                        'age': age,
                        'path': os.path.join(self.sessions_dir, filename)
                    })
        except:
            pass
        return sessions
    
    def clear_old_sessions(self) -> int:
        """Очистка устаревших сессий"""
        cleared = 0
        for session in self.list_sessions():
            if session['age'] and session['age'] > timedelta(hours=config.SESSION_TIMEOUT_HOURS):
                if self.delete_session(session['username']):
                    cleared += 1
        return cleared
    
    def is_session_valid(self, username: str) -> bool:
        """Проверка валидности сессии"""
        session = self.load_session(username)
        return session is not None


session_manager = SessionManager()