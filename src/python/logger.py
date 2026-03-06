#!/usr/bin/env python3
import os
import logging
from datetime import datetime
from typing import Optional

class SecureLogger:
    """Система логирования для CS2 Farmer"""
    
    _instance: Optional['SecureLogger'] = None
    
    def __new__(cls, log_file: str = "logs/farmer.log", master_password: str = ""):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, log_file: str = "logs/farmer.log", master_password: str = ""):
        if self._initialized:
            return
        
        self.log_file = log_file
        self.master_password = master_password
        
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        
        if not log_file or log_file == "logs/farmer.log":
            date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.log_file = os.path.join("logs", f"farmer_{date_str}.log")
        
        self._logger = logging.getLogger("CS2Farmer")
        self._logger.setLevel(logging.DEBUG)
        self._logger.handlers.clear()
        
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        self._logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_format)
        self._logger.addHandler(console_handler)
        
        self._initialized = True
        self.info("=" * 60)
        self.info("CS2 Farmer Panel - Логирование запущено")
        self.info(f"Файл лога: {self.log_file}")
        self.info("=" * 60)
    
    def log(self, level: str, msg: str):
        level = level.upper()
        if level == 'DEBUG':
            self.debug(msg)
        elif level == 'INFO':
            self.info(msg)
        elif level == 'WARNING':
            self.warning(msg)
        elif level == 'ERROR':
            self.error(msg)
        elif level == 'CRITICAL':
            self.critical(msg)
        else:
            self.info(msg)
    
    def debug(self, msg: str):
        if self._logger:
            self._logger.debug(msg)
    
    def info(self, msg: str):
        if self._logger:
            self._logger.info(msg)
    
    def warning(self, msg: str):
        if self._logger:
            self._logger.warning(msg)
    
    def error(self, msg: str):
        if self._logger:
            self._logger.error(msg)
    
    def critical(self, msg: str):
        if self._logger:
            self._logger.critical(msg)
    
    def get_log_file(self) -> str:
        return self.log_file
    
    def get_log_dir(self) -> str:
        return os.path.dirname(self.log_file) or "logs"

logger = SecureLogger()