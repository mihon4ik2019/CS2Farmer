#!/usr/bin/env python3
import sys
import os
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Перезапуск текущего скрипта с правами администратора."""
    if is_admin():
        return True
    if getattr(sys, 'frozen', False):
        executable = sys.executable
        params = ' '.join(sys.argv[1:])
    else:
        executable = sys.executable
        script_path = os.path.abspath(sys.argv[0])
        params = f'"{script_path}" ' + ' '.join(sys.argv[1:])
    ret = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", executable, params, None, 1
    )
    if ret <= 32:
        print(f"Не удалось запустить с правами администратора (код ошибки: {ret})")
        return False
    sys.exit(0)

# Запрос прав администратора при запуске
run_as_admin()

print("=" * 60)
print("CS2 Farmer Panel - Запуск")
print("=" * 60)
if is_admin():
    print("✅ Программа запущена от имени администратора")
else:
    print("⚠️ Программа НЕ запущена от имени администратора")
    print("    pyautogui может работать некорректно без прав администратора.")
    print("    Продолжение невозможно, перезапустите вручную.")
    sys.exit(1)
print("=" * 60)

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../..'))
sys.path.insert(0, project_root)

from src.python.ui.app import App

def main():
    app = App()
    app.mainloop()

if __name__ == '__main__':
    main()