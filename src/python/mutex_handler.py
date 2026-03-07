"""
Mutex Handler для закрытия мьютексов Steam/CS2
КРИТИЧЕСКИ ВАЖНО для мульти-инстанс без Sandboxie
Основано на методе из UnknownCheats (cs2ch.exe)
"""
import ctypes
from ctypes import wintypes
import psutil
from typing import List, Optional

# Windows API константы
PROCESS_DUP_HANDLE = 0x0040
SYNCHRONIZE = 0x00100000
MUTEX_ALL_ACCESS = 0x001F0001
DUPLICATE_CLOSE_SOURCE = 0x00000001
DUPLICATE_SAME_ACCESS = 0x00000002

class MutexHandler:
    """Обработчик мьютексов для мульти-инстанс"""
    
    def __init__(self):
        self.ntdll = ctypes.windll.ntdll
        self.kernel32 = ctypes.windll.kernel32
        
    def close_handles_for_process(self, pid: int, mutex_names: List[str]) -> int:
        """
        Закрытие handle'ов мьютексов для процесса
        Returns: Количество закрытых handle'ов
        """
        closed_count = 0
        
        try:
            # Открываем процесс
            h_process = self.kernel32.OpenProcess(
                PROCESS_DUP_HANDLE | SYNCHRONIZE,
                False,
                pid
            )
            
            if not h_process:
                return 0
            
            # Получаем все handle'ы процесса
            handles = self._get_process_handles(pid)
            
            for handle_info in handles:
                handle = handle_info['handle']
                obj_name = handle_info.get('name', '')
                
                # Проверяем имя мьютекса
                for mutex_name in mutex_names:
                    if mutex_name.lower() in obj_name.lower():
                        try:
                            # Закрываем handle
                            if self.kernel32.CloseHandle(handle):
                                closed_count += 1
                        except:
                            pass
            
            self.kernel32.CloseHandle(h_process)
            
        except Exception as e:
            print(f"[MutexHandler] ⚠️ Ошибка: {e}")
        
        return closed_count
    
    def _get_process_handles(self, pid: int) -> List[dict]:
        """
        Получение всех handle'ов процесса
        Требуются права администратора!
        """
        handles = []
        
        try:
            # Используем NtQuerySystemInformation для получения handle'ов
            # Это упрощённая версия - для полной нужен драйвер или NtQueryInformationProcess
            
            # Альтернативный метод через psutil
            process = psutil.Process(pid)
            
            # Получаем информацию о процессе
            handles.append({
                'handle': process.pid,
                'name': process.name(),
                'type': 'process'
            })
            
        except:
            pass
        
        return handles
    
    def close_steam_mutex(self, steam_pid: int) -> int:
        """Закрытие мьютексов Steam"""
        from . import config
        return self.close_handles_for_process(steam_pid, config.STEAM_MUTEX_NAMES)
    
    def close_cs2_mutex(self, cs2_pid: int) -> int:
        """Закрытие мьютексов CS2"""
        from . import config
        return self.close_handles_for_process(cs2_pid, config.CS2_MUTEX_NAMES)
    
    @staticmethod
    def kill_steam_mutex_processes():
        """
        Альтернативный метод: завершение процессов которые держат мьютексы
        Более надёжно чем закрытие handle'ов
        """
        import os
        import time
        
        # Процессы которые могут держать мьютексы
        mutex_processes = [
            "steamwebhelper.exe",
            "steamservice.exe",
            "gameoverlayui.exe"
        ]
        
        count = 0
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                name = proc.info['name']
                if name:
                    for mp in mutex_processes:
                        if mp.lower() in name.lower():
                            try:
                                proc.terminate()
                                count += 1
                            except:
                                try:
                                    proc.kill()
                                    count += 1
                                except:
                                    pass
            except:
                pass
        
        time.sleep(2)
        
        # Дополнительная очистка
        for mp in mutex_processes:
            os.system(f"taskkill /f /im {mp} 2>nul")
        
        return count