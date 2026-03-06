#!/usr/bin/env python3
import os
import logging
from datetime import datetime

class Logger:
    """Система логирования для CS2 Farmer"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Имя файла лога с датой
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file = os.path.join(log_dir, f"farmer_{date_str}.log")
        
        # Настройка логгера
        self.logger = logging.getLogger("CS2Farmer")
        self.logger.setLevel(logging.DEBUG)
        
        # Очистка старых хендлеров
        self.logger.handlers.clear()
        
        # Файловый хендлер
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
        
        # Консольный хендлер
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
    
    def debug(self, msg):
        self.logger.debug(msg)
    
    def info(self, msg):
        self.logger.info(msg)
    
    def warning(self, msg):
        self.logger.warning(msg)
    
    def error(self, msg):
        self.logger.error(msg)
    
    def critical(self, msg):
        self.logger.critical(msg)
    
    def get_log_file(self) -> str:
        """Возвращает путь к текущему файлу лога"""
        return self.log_file

# Глобальный экземпляр
logger = Logger()