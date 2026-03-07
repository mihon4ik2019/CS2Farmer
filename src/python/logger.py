"""
Secure Logger - УЛУЧШЕННЫЙ
С ротацией и детализацией
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Optional

from . import config


class SecureLogger:
    def __init__(self, name: str = 'CS2Farmer'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Очистка старых handlers
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # File handler с ротацией
        if config.LOG_TO_FILE:
            try:
                os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)
                
                file_handler = RotatingFileHandler(
                    config.LOG_FILE,
                    maxBytes=config.MAX_LOG_SIZE_MB * 1024 * 1024,
                    backupCount=5,
                    encoding='utf-8'
                )
                file_handler.setLevel(logging.DEBUG)
                file_format = logging.Formatter(
                    '%(asctime)s | %(levelname)s | %(name)s | %(funcName)s | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(file_format)
                self.logger.addHandler(file_handler)
            except Exception as e:
                print(f"[Logger] ⚠️ Ошибка создания файла лога: {e}")
    
    def info(self, message: str):
        self.logger.info(message)
    
    def debug(self, message: str):
        if config.ENABLE_DETAILED_LOGS:
            self.logger.debug(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def error(self, message: str):
        self.logger.error(message)
        if config.LOG_TO_UI:
            print(f"[ERROR] {message}")
    
    def critical(self, message: str):
        self.logger.critical(message)
    
    def success(self, message: str):
        self.logger.info(f"✅ {message}")
    
    def step(self, step_name: str, message: str = ''):
        self.logger.info(f"▶️ {step_name} {message}")


logger = SecureLogger() 