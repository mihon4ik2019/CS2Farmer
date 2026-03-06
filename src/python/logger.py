import os
import json
from datetime import datetime
from .crypto_utils import CryptoUtils

class SecureLogger:
    def __init__(self, log_file: str, master_password: str):
        self.log_file = log_file
        self.master_password = master_password

    def log(self, level: str, message: str):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        encrypted = CryptoUtils.encrypt(json.dumps(entry), self.master_password)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(encrypted + '\n')

    def read_logs(self, count: int = 100) -> list:
        if not os.path.exists(self.log_file):
            return []
        entries = []
        with open(self.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-count:]
            for line in lines:
                try:
                    decrypted = CryptoUtils.decrypt(line.strip(), self.master_password)
                    entries.append(json.loads(decrypted))
                except Exception:
                    continue
        return entries