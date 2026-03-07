"""
CS2Farmer - Быстрый запуск
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.python.ui.app import App

if __name__ == "__main__":
    print("=" * 60)
    print("🎮 CS2Farmer - Запуск")
    print("=" * 60)
    app = App()
    app.mainloop()