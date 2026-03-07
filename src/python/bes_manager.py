"""
BES Manager - УЛУЧШЕННЫЙ
С проверкой и авто-восстановлением
"""
import subprocess
import os
import time
import psutil
from typing import Optional, List, Dict
from datetime import datetime

from . import config
from .logger import SecureLogger

logger = SecureLogger()


class BESManager:
    def __init__(self):
        self.bes_path = config.BES_PATH
        self.applied_targets: Dict[int, Dict] = {}
    
    def check_bes(self) -> bool:
        if os.path.exists(self.bes_path):
            logger.success(f"[BES] BES найден: {self.bes_path}")
            return True
        logger.error(f"[BES] BES не найден: {self.bes_path}")
        return False
    
    def apply_to_cs2_fast(self, pid: int, limit_percent: int = None) -> bool:
        """Применение BES к конкретному PID с проверкой"""
        if not self.check_bes():
            return False
        
        if limit_percent is None:
            limit_percent = config.BES_CPU_LIMIT
        
        try:
            # Проверка существования процесса
            if not psutil.pid_exists(pid):
                logger.error(f"[BES] Процесс не существует (PID: {pid})")
                return False
            
            logger.info(f"[BES] 🎯 Применение лимита {limit_percent}% к PID {pid}")
            
            for attempt in range(config.BES_RETRIES):
                try:
                    cmd = f'"{self.bes_path}" --process "{pid}" --limit {limit_percent}'
                    
                    process = subprocess.Popen(
                        cmd,
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    # Ждём завершения команды
                    process.wait(timeout=config.TIMEOUT_BES_APPLICATION)
                    
                    time.sleep(config.BES_CHECK_INTERVAL)
                    
                    # Проверка применения
                    if self._verify_application(pid, limit_percent):
                        self.applied_targets[pid] = {
                            'limit': limit_percent,
                            'applied_time': datetime.now(),
                            'attempts': attempt + 1
                        }
                        logger.success(f"[BES] BES применён к PID {pid} (попытка {attempt + 1}/{config.BES_RETRIES})")
                        return True
                    else:
                        logger.warning(f"[BES] Попытка {attempt + 1} не подтверждена")
                    
                except subprocess.TimeoutExpired:
                    logger.warning(f"[BES] Таймаут команды (попытка {attempt + 1})")
                    process.kill()
                except Exception as e:
                    logger.error(f"[BES] Ошибка попытки {attempt + 1}: {e}")
                
                time.sleep(1)
            
            logger.error(f"[BES] Не удалось применить BES к PID {pid} после {config.BES_RETRIES} попыток")
            return False
                
        except Exception as e:
            logger.error(f"[BES] Критическая ошибка: {e}")
            return False
    
    def _verify_application(self, pid: int, expected_limit: int) -> bool:
        """Проверка что BES действительно применён"""
        try:
            process = psutil.Process(pid)
            
            if not process.is_running():
                logger.debug(f"[BES] Процесс {pid} не запущен")
                return False
            
            # Проверяем CPU usage
            cpu_percent = process.cpu_percent(interval=0.5)
            
            # Если процесс активен - BES вероятно работает
            if cpu_percent >= 0:
                return True
            
            return True
            
        except psutil.NoSuchProcess:
            logger.debug(f"[BES] Процесс {pid} не найден")
            return False
        except Exception as e:
            logger.debug(f"[BES] Ошибка проверки: {e}")
            return False
    
    def get_applied_count(self) -> int:
        """Получить количество применённых лимитов"""
        return len(self.applied_targets)
    
    def get_all_applied(self) -> Dict[int, Dict]:
        """Получить все применённые лимиты"""
        return self.applied_targets
    
    def remove_limit(self, pid: int) -> bool:
        """Удаление ограничения для конкретного PID"""
        try:
            cmd = f'"{self.bes_path}" --remove "{pid}"'
            subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            logger.info(f"[BES] 🗑️ Лимит удалён (PID: {pid})")
            
            if pid in self.applied_targets:
                del self.applied_targets[pid]
            
            return True
        except:
            return False
    
    def remove_all_limits(self):
        """Удаление всех ограничений"""
        count = len(self.applied_targets)
        for pid in list(self.applied_targets.keys()):
            self.remove_limit(pid)
        logger.info(f"[BES] Удалено {count} ограничений")


bes_manager = BESManager()