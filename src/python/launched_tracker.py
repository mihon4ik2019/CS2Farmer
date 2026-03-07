"""
Launched Tracker - ОТСЛЕЖИВАНИЕ ЗАПУЩЕННЫХ АККАУНТОВ
Аналог launched_accounts.json из FSM Panel
"""
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

from . import config


class LaunchedTracker:
    """
    ОТСЛЕЖИВАНИЕ ЗАПУЩЕННЫХ АККАУНТОВ
    Как в FSM Panel (launched_accounts.json)
    """
    
    def __init__(self):
        self.tracker_file = os.path.join(config.DATA_DIR, 'launched_accounts.json')
        self.data = self._load()
    
    def _load(self) -> Dict:
        """Загрузка данных трекера"""
        try:
            if os.path.exists(self.tracker_file):
                with open(self.tracker_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {'accounts': [], 'last_launch': None}
    
    def _save(self):
        """Сохранение данных трекера"""
        try:
            with open(self.tracker_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def mark_launched(self, username: str, account_id: int):
        """Отметить аккаунт как запущенный"""
        account_info = {
            'username': username,
            'account_id': account_id,
            'launch_time': datetime.now().isoformat(),
            'timestamp': time.time(),
        }
        
        # Удаляем старую запись если есть
        self.data['accounts'] = [
            acc for acc in self.data['accounts'] 
            if acc.get('username') != username
        ]
        
        # Добавляем новую
        self.data['accounts'].append(account_info)
        self.data['last_launch'] = datetime.now().isoformat()
        
        self._save()
        print(f"[LaunchedTracker] ✅ Отмечен: {username}")
    
    def is_launched(self, username: str) -> bool:
        """Проверка запущен ли аккаунт"""
        for acc in self.data['accounts']:
            if acc.get('username') == username:
                # Проверяем не слишком ли старая запись
                timestamp = acc.get('timestamp', 0)
                if time.time() - timestamp < 3600:  # 1 час
                    return True
        return False
    
    def get_launched_count(self) -> int:
        """Получить количество запущенных аккаунтов"""
        return len(self.data['accounts'])
    
    def get_launched_accounts(self) -> List[str]:
        """Получить список запущенных аккаунтов"""
        return [acc.get('username') for acc in self.data['accounts']]
    
    def clear_old(self, max_age_hours: int = 24):
        """Очистка старых записей"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        self.data['accounts'] = [
            acc for acc in self.data['accounts']
            if current_time - acc.get('timestamp', 0) < max_age_seconds
        ]
        
        self._save()
    
    def clear_all(self):
        """Очистка всех записей"""
        self.data = {'accounts': [], 'last_launch': None}
        self._save()
        print(f"[LaunchedTracker] 🗑️ Все записи очищены")


tracker = LaunchedTracker()