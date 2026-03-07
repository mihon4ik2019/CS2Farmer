"""
CS2Farmer UI - ОБНОВЛЁННЫЙ
"""
import customtkinter as ctk
import threading
import os
import sys
from datetime import datetime
from typing import Dict
from ..database import Database
from ..process_manager import ProcessManager
from ..account_manager import AccountManager
from ..ban_checker import BanChecker
from ..models import AccountStatus, Account
from .. import config

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ConsoleCapture:
    def __init__(self, callback):
        self.callback = callback
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.buffer = ""
    
    def write(self, text):
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


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("CS2Farmer - 640x480 | Мин RAM | BES")
        self.geometry("1000x750")
        
        self.db = Database(config.DB_PATH, "cs2farmer")
        self.pm = ProcessManager()
        
        try:
            self.ban_checker = BanChecker(api_key="")
        except:
            self.ban_checker = self._create_dummy_ban_checker()
        
        self.am = AccountManager(self.db, self.pm, self.ban_checker)
        
        self.selected_accounts: Dict[int, bool] = {}
        self.is_running = False
        
        self.console_capture = ConsoleCapture(self._log)
        self.console_capture.start()
        
        self._create_ui()
        self._auto_import_accounts()
        self._load_accounts()
    
    def _create_dummy_ban_checker(self):
        class DummyBanChecker:
            def check_account(self, steam_id: str) -> bool:
                return False
        return DummyBanChecker()
    
    def _create_ui(self):
        left_frame = ctk.CTkFrame(self, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=(20, 10), pady=20)
        
        header = ctk.CTkFrame(left_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(header, text="🎮 CS2Farmer", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        ctk.CTkLabel(header, text="640×480 | Мин RAM | BES 25%", font=ctk.CTkFont(size=11), text_color="#666666").pack(side="right", pady=10)
        
        status = ctk.CTkFrame(left_frame, fg_color="#1a1a1a", corner_radius=8)
        status.pack(fill="x", pady=(0, 15))
        
        self.status_dot = ctk.CTkLabel(status, text="●", font=ctk.CTkFont(size=16), text_color="#4CAF50")
        self.status_dot.pack(side="left", padx=12, pady=8)
        
        self.status_text = ctk.CTkLabel(status, text="Готов", font=ctk.CTkFont(size=12, weight="bold"), text_color="#4CAF50")
        self.status_text.pack(side="left", padx=5, pady=8)
        
        self.selected_lbl = ctk.CTkLabel(status, text="✓ 0", font=ctk.CTkFont(size=12), text_color="#FF9800")
        self.selected_lbl.pack(side="right", padx=15, pady=8)
        
        self.total_lbl = ctk.CTkLabel(status, text="📊 0", font=ctk.CTkFont(size=12), text_color="#2196F3")
        self.total_lbl.pack(side="right", padx=15, pady=8)
        
        table = ctk.CTkFrame(left_frame, fg_color="#1a1a1a", corner_radius=8)
        table.pack(fill="both", expand=True, pady=(0, 15))
        
        hdr = ctk.CTkFrame(table, fg_color="#2a2a2a", height=30)
        hdr.pack(fill="x", padx=8, pady=(8, 0))
        
        ctk.CTkLabel(hdr, text="✓", width=28, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(hdr, text="Аккаунт", width=150, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(hdr, text="Статус", width=90, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(hdr, text="maFile", width=50, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        ctk.CTkLabel(hdr, text="Время", width=65, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
        
        self.accounts_frame = ctk.CTkScrollableFrame(table, fg_color="transparent")
        self.accounts_frame.pack(fill="both", expand=True, padx=8, pady=8)
        
        btns = ctk.CTkFrame(left_frame, fg_color="transparent")
        btns.pack(fill="x")
        
        self.start_btn = ctk.CTkButton(btns, text="▶️ Запустить", font=ctk.CTkFont(size=13, weight="bold"), height=40, width=140, fg_color="#4CAF50", hover_color="#45a049", command=self._start_selected)
        self.start_btn.pack(side="left", padx=(0, 6))
        
        self.stop_btn = ctk.CTkButton(btns, text="⏹️ Стоп", font=ctk.CTkFont(size=13, weight="bold"), height=40, width=90, fg_color="#f44336", hover_color="#da190b", command=self._stop_all)
        self.stop_btn.pack(side="left", padx=(0, 6))
        
        ctk.CTkButton(btns, text="🔄", font=ctk.CTkFont(size=13), height=40, width=45, fg_color="#2196F3", hover_color="#1976D2", command=self._load_accounts).pack(side="left", padx=(0, 6))
        
        ctk.CTkButton(btns, text="☑️", font=ctk.CTkFont(size=13), height=40, width=45, fg_color="#555555", hover_color="#666666", command=self._select_all).pack(side="left")
        
        right_frame = ctk.CTkFrame(self, fg_color="transparent", width=400)
        right_frame.pack(side="right", fill="both", padx=(10, 20), pady=20)
        right_frame.pack_propagate(False)
        
        log_hdr = ctk.CTkFrame(right_frame, fg_color="#1a1a1a", corner_radius=8, height=40)
        log_hdr.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(log_hdr, text="📋 Логи", font=ctk.CTkFont(weight="bold", size=13)).pack(side="left", padx=12, pady=10)
        
        ctk.CTkButton(log_hdr, text="🗑️", width=35, height=28, fg_color="#444444", command=self._clear_logs).pack(side="right", padx=8, pady=6)
        
        self.log_text = ctk.CTkTextbox(right_frame, font=ctk.CTkFont(size=10, family="Consolas"), wrap="word")
        self.log_text.pack(fill="both", expand=True)
        
        self._log("🎉 CS2Farmer запущен!")
        self._log("⚡ Мин RAM | BES 25% | Сетка 2x2")
    
    def _auto_import_accounts(self):
        logpass_path = os.path.join(config.BASE_DIR, 'logpass.txt')
        if os.path.exists(logpass_path):
            count = self.am.import_from_logpass(logpass_path)
            self._log(f"✅ Импортировано: {count}" if count > 0 else "ℹ️ Уже в базе")
        else:
            self._log("⚠️ logpass.txt не найден")
    
    def _load_accounts(self):
        for w in self.accounts_frame.winfo_children():
            w.destroy()
        
        accounts = self.am.get_all()
        self.total_lbl.configure(text=f"📊 {len(accounts)}")
        self._update_selected()
        
        if not accounts:
            ctk.CTkLabel(self.accounts_frame, text="📭 Нет аккаунтов", font=ctk.CTkFont(size=12), text_color="#666666").pack(pady=30)
            return
        
        for acc in accounts:
            self._create_row(acc)
    
    def _create_row(self, acc: Account):
        row = ctk.CTkFrame(self.accounts_frame, fg_color="#252525", height=36)
        row.pack(fill="x", padx=5, pady=2)
        
        var = ctk.BooleanVar(value=self.selected_accounts.get(acc.id, False))
        cb = ctk.CTkCheckBox(row, text="", variable=var, width=26, checkbox_width=16, command=lambda: self._toggle(acc.id, var.get()))
        cb.pack(side="left", padx=5)
        
        ctk.CTkLabel(row, text=acc.username, width=150, anchor="w", font=ctk.CTkFont(size=11)).pack(side="left", padx=5)
        
        colors = {AccountStatus.STOPPED: "#888888", AccountStatus.STARTING: "#FF9800", AccountStatus.IN_GAME: "#4CAF50", AccountStatus.ERROR: "#f44336", AccountStatus.BANNED: "#9C27B0"}
        icons = {AccountStatus.STOPPED: "⏸️", AccountStatus.STARTING: "⏳", AccountStatus.IN_GAME: "✅", AccountStatus.ERROR: "❌", AccountStatus.BANNED: "🚫"}
        status_color = colors.get(acc.status, "#888888")
        status_icon = icons.get(acc.status, "⏸️")
        ctk.CTkLabel(row, text=f"{status_icon}", width=90, text_color=status_color, font=ctk.CTkFont(size=13)).pack(side="left", padx=5)
        
        mafile_color = "#4CAF50" if acc.ma_file_path else "#f44336"
        ctk.CTkLabel(row, text="✅" if acc.ma_file_path else "❌", width=50, text_color=mafile_color, font=ctk.CTkFont(size=13)).pack(side="left", padx=5)
        
        pt = acc.play_time_minutes if acc.play_time_minutes else 0
        ctk.CTkLabel(row, text=f"{pt//60}ч {pt%60}м", width=65, font=ctk.CTkFont(size=10)).pack(side="left", padx=5)
    
    def _toggle(self, aid: int, selected: bool):
        self.selected_accounts[aid] = selected
        self._update_selected()
    
    def _update_selected(self):
        cnt = sum(1 for v in self.selected_accounts.values() if v)
        self.selected_lbl.configure(text=f"✓ {cnt}")
    
    def _select_all(self):
        for row in self.accounts_frame.winfo_children():
            for cb in row.winfo_children():
                if isinstance(cb, ctk.CTkCheckBox):
                    cb.set(True)
        for acc in self.am.get_all():
            self.selected_accounts[acc.id] = True
        self._update_selected()
    
    def _start_selected(self):
        selected = [aid for aid, s in self.selected_accounts.items() if s]
        
        if not selected:
            self._log("⚠️ Выберите аккаунты!")
            return
        if self.is_running:
            self._log("⚠️ Уже запущено")
            return
        
        self.is_running = True
        self.start_btn.configure(state="disabled", text="⏳...")
        self.status_text.configure(text="Запуск...", text_color="#FF9800")
        self.status_dot.configure(text_color="#FF9800")
        
        self._log(f"🚀 Запуск {len(selected)} аккаунтов...")
        self._log(f"📐 640×480 | 🔲 2×2 Grid")
        self._log(f"⚡ Мин RAM (2GB heap)")
        self._log(f"🔧 BES: {config.BES_CPU_LIMIT}% CPU")
        self._log(f"🗑️ Авто-закрытие библиотек")
        
        def run():
            self.am.start_accounts_sequential(selected, self._on_progress)
            self.is_running = False
            self.after(0, self._on_complete)
        
        threading.Thread(target=run, daemon=True).start()
    
    def _stop_all(self):
        self._log("⏹️ Остановка...")
        self.am.stop_all()
        self.is_running = False
        self.start_btn.configure(state="normal", text="▶️ Запустить")
        self.status_text.configure(text="Готов", text_color="#4CAF50")
        self.status_dot.configure(text_color="#4CAF50")
        self._load_accounts()
        self._log("✅ Остановлено")
    
    def _on_progress(self, current: int, total: int):
        self._log(f"✅ Аккаунт {current}/{total} запущен")
        self.after(0, self._load_accounts)
    
    def _on_complete(self):
        self.start_btn.configure(state="normal", text="▶️ Запустить")
        self.status_text.configure(text="Готов", text_color="#4CAF50")
        self.status_dot.configure(text_color="#4CAF50")
        self._log("✅ Все запущены!")
        self._load_accounts()
    
    def _clear_logs(self):
        self.log_text.delete("1.0", "end")
        self._log("🗑️ Очищено")
    
    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {msg}\n")
        self.log_text.see("end")
        try:
            with open(config.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {msg}\n")
        except:
            pass
    
    def _on_closing(self):
        self.console_capture.stop()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app._on_closing)
    app.mainloop()