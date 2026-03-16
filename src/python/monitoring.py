"""
Monitoring Classes - ConsoleCapture + SystemMonitor
"""
import sys
import threading
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import deque


class ConsoleCapture:
    """Перехват вывода консоли"""
    
    def __init__(self, callback):
        self.callback = callback
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.buffer = ""
        self.lock = threading.Lock()
    
    def write(self, text):
        with self.lock:
            self.buffer += text
            while '\n' in self.buffer:
                line, self.buffer = self.buffer.split('\n', 1)
                if line.strip():
                    self.callback(line)
            self.original_stdout.write(text)
    
    def flush(self):
        self.original_stdout.flush()
    
    def start(self):
        sys.stdout = self
        sys.stderr = self
    
    def stop(self):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr


class PerformanceMonitor:
    """Мониторинг производительности"""
    
    def __init__(self):
        self.cpu_history = deque(maxlen=120)
        self.memory_history = deque(maxlen=120)
        self.network_history = deque(maxlen=100)
        self.start_time = datetime.now()
        self.last_net_counters = None
    
    def get_cpu_info(self) -> Dict:
        try:
            return {
                'percent': psutil.cpu_percent(interval=0.2),
                'per_core': psutil.cpu_percent(percpu=True, interval=0.1)
            }
        except:
            return {'percent': 0, 'per_core': []}
    
    def get_memory_info(self) -> Dict:
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            return {
                'percent': mem.percent,
                'used': mem.used,
                'swap_percent': swap.percent
            }
        except:
            return {'percent': 0, 'used': 0, 'swap_percent': 0}
    
    def get_network_info(self) -> Dict:
        try:
            net = psutil.net_io_counters()
            current = {'bytes_sent': net.bytes_sent, 'bytes_recv': net.bytes_recv}
            upload = download = 0
            if self.last_net_counters:
                upload = (current['bytes_sent'] - self.last_net_counters['bytes_sent']) // 1024
                download = (current['bytes_recv'] - self.last_net_counters['bytes_recv']) // 1024
            self.last_net_counters = current
            return {'upload_kb': upload, 'download_kb': download, 'total_kb': upload + download}
        except:
            return {'upload_kb': 0, 'download_kb': 0, 'total_kb': 0}
    
    def update_history(self, cpu: float, memory: float, disk: float, network: Dict):
        self.cpu_history.append(cpu)
        self.memory_history.append(memory)
    
    def get_uptime(self) -> timedelta:
        return datetime.now() - self.start_time


class SystemMonitor:
    """Главный монитор системы"""
    
    def __init__(self, callback):
        self.callback = callback
        self.running = False
        self.cs2_pids: List[int] = []
        self.perf_monitor = PerformanceMonitor()
        self.history = deque(maxlen=120)
    
    def start(self):
        self.running = True
        threading.Thread(target=self._monitor_loop, daemon=True).start()
    
    def stop(self):
        self.running = False
    
    def update_cs2_pids(self, pids: List[int]):
        self.cs2_pids = pids
    
    def _monitor_loop(self):
        while self.running:
            try:
                cpu_info = self.perf_monitor.get_cpu_info()
                mem_info = self.perf_monitor.get_memory_info()
                net_info = self.perf_monitor.get_network_info()
                
                cs2_loads = []
                for pid in self.cs2_pids:
                    try:
                        proc = psutil.Process(pid)
                        cs2_loads.append({
                            'pid': pid,
                            'cpu': proc.cpu_percent(interval=0.1),
                            'memory': proc.memory_info().rss // 1024 // 1024,
                            'threads': proc.num_threads()
                        })
                    except:
                        pass
                
                data = {
                    'timestamp': time.time(),
                    'uptime': self.perf_monitor.get_uptime(),
                    'cpu': cpu_info['percent'],
                    'cpu_per_core': cpu_info['per_core'],
                    'memory_percent': mem_info['percent'],
                    'memory_used_gb': mem_info['used'] // 1024 // 1024 // 1024,
                    'swap_percent': mem_info['swap_percent'],
                    'net_total_kb': net_info['total_kb'],
                    'cs2_count': len(cs2_loads),
                    'cs2_loads': cs2_loads
                }
                
                self.perf_monitor.update_history(data['cpu'], data['memory_percent'], 0, net_info)
                self.history.append(data)
                self.callback(data)
            except:
                pass
            
            time.sleep(1)