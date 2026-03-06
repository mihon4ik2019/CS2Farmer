#!/usr/bin/env python3
import sys
import os
import ctypes
import time

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Принудительный запуск от админа"""
    if is_admin():
        print("[Main] ✅ Запущено от имени администратора")
        return True
    
    print("[Main] ⚠️ Требуются права администратора")
    print("[Main] 🔄 Перезапуск...")
    time.sleep(2)
    
    if getattr(sys, 'frozen', False):
        executable = sys.executable
        params = ' '.join(f'"{arg}"' for arg in sys.argv[1:])
    else:
        executable = sys.executable
        script_path = os.path.abspath(sys.argv[0])
        params = f'"{script_path}" ' + ' '.join(f'"{arg}"' for arg in sys.argv[1:])
    
    ret = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", executable, params, None, 1
    )
    
    if ret <= 32:
        print(f"[Main] ❌ Не удалось получить права (код: {ret})")
        input("Нажмите Enter для выхода...")
        sys.exit(1)
    
    sys.exit(0)

# === ЗАПУСК ОТ АДМИНА ===
run_as_admin()

print("=" * 70)
print("  CS2 Farmer Panel - Multi-Account Manager")
print("=" * 70)
print("✅ Запущено от имени администратора")
print("=" * 70)

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.insert(0, project_root)

from src.python.ui.app import App

def main():
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        print(f"\n[Main] ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")

if __name__ == '__main__':
    main()