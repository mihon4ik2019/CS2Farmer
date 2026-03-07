"""
CS2 Waiter - 30С ПОСЛЕ НАХОЖДЕНИЯ ПРОЦЕССА
"""
import psutil
import time
from typing import Optional, Tuple, List, Set


class CS2Waiter:
    def __init__(self):
        self.cs2_names = ['cs2.exe', 'cs2', 'counter-strike']
        self.known_pids: Set[int] = set()
    
    def clear_known_pids(self):
        """Очистить список известных процессов"""
        self.known_pids.clear()
        print(f"[CS2Waiter] 🗑️ Известные процессы очищены")
    
    def check_cs2_processes(self) -> List[int]:
        """Поиск всех процессов CS2"""
        pids = []
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                name = proc.info['name']
                if name:
                    name_lower = name.lower()
                    for cs2_name in self.cs2_names:
                        if cs2_name in name_lower:
                            pids.append(proc.info['pid'])
                            break
            except:
                pass
        
        return pids
    
    def get_new_cs2_processes(self) -> List[int]:
        """Получить только НОВЫЕ процессы CS2"""
        all_pids = self.check_cs2_processes()
        new_pids = [pid for pid in all_pids if pid not in self.known_pids]
        return new_pids
    
    def add_known_pids(self, pids: List[int]):
        """Добавить процессы в список известных"""
        for pid in pids:
            self.known_pids.add(pid)
        if pids:
            print(f"[CS2Waiter] 📝 Добавлено {len(pids)} процессов в известные")
    
    def get_total_cs2_count(self) -> int:
        """Получить общее количество процессов CS2"""
        return len(self.check_cs2_processes())
    
    def wait_for_new_cs2_process(self, timeout: int = 180, load_seconds: int = 30) -> Tuple[bool, Optional[int]]:
        """
        ✅ ОЖИДАНИЕ НОВОГО ПРОЦЕССА CS2 + 30С ЗАГРУЗКИ
        Returns: (success, pid)
        """
        from . import config
        
        print(f"[CS2Waiter] ⏳ Ожидание НОВОГО процесса CS2...")
        print(f"[CS2Waiter] 📋 Ожидание загрузки: {load_seconds}s")
        print(f"[CS2Waiter] 📊 Уже известно процессов: {len(self.known_pids)}")
        
        start = time.time()
        new_pid = None
        load_start = None
        
        while time.time() - start < timeout:
            # Ищем новые процессы
            current_new_pids = self.get_new_cs2_processes()
            
            if current_new_pids:
                if new_pid is None:
                    new_pid = current_new_pids[0]
                    print(f"[CS2Waiter] ✅ НОВЫЙ процесс CS2 найден (PID: {new_pid})")
                    print(f"[CS2Waiter] ⏳ Начало отсчёта загрузки ({load_seconds}s)...")
                    load_start = time.time()
                
                # Просто ждём 30 секунд (не проверяем стабильность)
                elapsed_load = time.time() - load_start
                
                if elapsed_load >= load_seconds:
                    total_elapsed = time.time() - start
                    print(f"[CS2Waiter] ✅ CS2 загрузился за {load_seconds}s (всего: {total_elapsed:.2f}s)")
                    
                    try:
                        proc = psutil.Process(new_pid)
                        mem_mb = proc.memory_info().rss // 1024 // 1024
                        threads = proc.num_threads()
                        print(f"[CS2Waiter]   PID {new_pid}: {mem_mb}MB, {threads} потоков")
                    except:
                        pass
                    
                    # Добавляем в известные
                    self.add_known_pids([new_pid])
                    
                    return True, new_pid
                else:
                    remaining = load_seconds - elapsed_load
                    if int(elapsed_load) % 10 == 0:
                        print(f"[CS2Waiter]   Загрузка: {int(elapsed_load)}/{load_seconds}s (осталось: {int(remaining)}s)")
            else:
                all_pids = self.check_cs2_processes()
                if all_pids:
                    print(f"[CS2Waiter] 📊 Найдено {len(all_pids)} процессов CS2 (ожидаем новый)...")
            
            time.sleep(1)
        
        print(f"[CS2Waiter] ❌ Таймаут ожидания нового CS2 ({timeout}s)")
        return False, None
    
    def wait_for_expected_cs2_count(self, expected_count: int, timeout: int = 180, load_seconds: int = 30) -> Tuple[bool, List[int]]:
        """
        ✅ ОЖИДАНИЕ НУЖНОГО КОЛИЧЕСТВА ПРОЦЕССОВ CS2
        Returns: (success, list_of_pids)
        """
        from . import config
        
        print(f"[CS2Waiter] ⏳ Ожидание {expected_count} процесс(ов) CS2...")
        print(f"[CS2Waiter] 📋 Ожидание загрузки: {load_seconds}s")
        
        start = time.time()
        found_pids = []
        load_start = None
        
        while time.time() - start < timeout:
            all_pids = self.check_cs2_processes()
            
            if len(all_pids) >= expected_count:
                if not found_pids:
                    found_pids = all_pids[:expected_count]
                    print(f"[CS2Waiter] ✅ Найдено {len(found_pids)} процесс(ов) CS2")
                    for pid in found_pids:
                        print(f"[CS2Waiter]   PID: {pid}")
                    print(f"[CS2Waiter] ⏳ Начало отсчёта загрузки ({load_seconds}s)...")
                    load_start = time.time()
                
                elapsed_load = time.time() - load_start
                
                if elapsed_load >= load_seconds:
                    total_elapsed = time.time() - start
                    print(f"[CS2Waiter] ✅ Все {len(found_pids)} CS2 загрузились за {load_seconds}s")
                    print(f"[CS2Waiter] ⏱️ Всего: {total_elapsed:.2f}s")
                    
                    for pid in found_pids:
                        try:
                            proc = psutil.Process(pid)
                            mem_mb = proc.memory_info().rss // 1024 // 1024
                            threads = proc.num_threads()
                            print(f"[CS2Waiter]   PID {pid}: {mem_mb}MB, {threads} потоков")
                        except:
                            pass
                    
                    self.add_known_pids(found_pids)
                    return True, found_pids
                else:
                    remaining = load_seconds - elapsed_load
                    if int(elapsed_load) % 10 == 0:
                        print(f"[CS2Waiter]   Загрузка: {int(elapsed_load)}/{load_seconds}s (осталось: {int(remaining)}s)")
            else:
                load_start = None
                if all_pids:
                    print(f"[CS2Waiter] 📊 Найдено {len(all_pids)}/{expected_count} процессов...")
            
            time.sleep(1)
        
        print(f"[CS2Waiter] ❌ Таймаут ожидания CS2 ({timeout}s)")
        print(f"[CS2Waiter] 📊 Найдено: {len(found_pids)}/{expected_count}")
        return False, []


waiter = CS2Waiter()