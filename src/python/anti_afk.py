import threading
import time

class AntiAFKManager:
    def __init__(self, node_bridge):
        self.node = node_bridge
        self._threads = {}
        self._stop_flags = {}

    def start_for_account(self, account_id: int, interval: int = 60):
        if account_id in self._threads:
            self.stop_for_account(account_id)
        stop_event = threading.Event()
        self._stop_flags[account_id] = stop_event
        def run():
            while not stop_event.wait(interval):
                self.node.anti_afk_action(account_id)
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        self._threads[account_id] = thread

    def stop_for_account(self, account_id: int):
        if account_id in self._stop_flags:
            self._stop_flags[account_id].set()
            del self._stop_flags[account_id]
        if account_id in self._threads:
            del self._threads[account_id]