import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MAFILES_DIR = os.path.join(BASE_DIR, 'mafiles')
NODE_SCRIPT = os.path.join(BASE_DIR, 'src', 'node', 'index.js')
DB_PATH = os.path.join(DATA_DIR, 'cs2farmer.db')
LOG_FILE = os.path.join(DATA_DIR, 'secure.log')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MAFILES_DIR, exist_ok=True)