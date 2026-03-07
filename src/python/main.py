"""
CS2Farmer - ТОЧКА ВХОДА
"""
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from src.python.ui.app import App

def main():
    try:
        print("=" * 60)
        print("🎮 CS2Farmer - Запуск")
        print("=" * 60)
        
        app = App()
        app.mainloop()
        
    except Exception as e:
        print(f"[Main] ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("Нажмите Enter...")
        sys.exit(1)

if __name__ == "__main__":
    main()