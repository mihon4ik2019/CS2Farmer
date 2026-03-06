#!/usr/bin/env python3
import sys
import os
import ctypes

def is_admin():
    """Проверка прав администратора"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """
    Перезапуск с правами администратора ТОЛЬКО если необходимо.
    Для CS2 лучше запускать БЕЗ прав администратора чтобы избежать IPC конфликтов.
    """
    if is_admin():
        print("[Main] ✅ Уже запущено от имени администратора")
        return True
    
    # Проверяем, нужен ли admin для pyautogui
    admin_required = False
    try:
        import pyautogui
        # Пробуем минимальное действие
        pyautogui.position()
    except Exception as e:
        print(f"[Main] ⚠️ pyautogui требует прав администратора: {e}")
        admin_required = True
    
    if not admin_required:
        print("[Main] ⚠️ Запуск БЕЗ прав администратора (рекомендуется для CS2)")
        return True
    
    # Запрос прав администратора
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
        print(f"[Main] ⚠️ Не удалось получить права администратора (код: {ret})")
        print("[Main]    Программа продолжит работу, но могут быть ограничения.")
        return False
    
    sys.exit(0)

# Запрос прав (не критичный)
run_as_admin()

print("=" * 60)
print("CS2 Farmer Panel - Запуск")
print("=" * 60)
if is_admin():
    print("✅ Запущено от имени администратора")
    print("⚠️ Примечание: Для лучшего запуска CS2 рекомендуется запускать БЕЗ прав админа")
else:
    print("⚠️ Запущено без прав администратора (это нормально для CS2)")
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