import customtkinter as ctk
from tkinter import filedialog
import threading
import keyboard
from CTkToolTip import CTkToolTip
from CTkMessagebox import CTkMessagebox
from .dialogs import ChangePasswordDialog, SettingsDialog, AccountSettingsDialog
from .stats_window import StatsWindow
from .widgets import AccountCard
from src.python.models import AccountStatus

class MainWindow(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.app = parent
        self.account_manager = parent.account_manager
        self.pm = parent.pm
        self.drop_collector = parent.drop_collector
        self.selected_accounts = set()

        self.status_colors = {
            AccountStatus.STOPPED: ("#808080", "#A9A9A9"),
            AccountStatus.STARTING: ("#FFA500", "#FFD700"),
            AccountStatus.IN_GAME: ("#008000", "#90EE90"),
            AccountStatus.ERROR: ("#FF0000", "#FFB6C1"),
            AccountStatus.BANNED: ("#8B0000", "#CD5C5C"),
            AccountStatus.MATCH_FOUND: ("#800080", "#DDA0DD"),
        }

        self.create_widgets()
        self.refresh_accounts()
        self.after(5000, self.auto_refresh)

    def create_widgets(self):
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(pady=10, fill="x")
        title = ctk.CTkLabel(title_frame, text="CS2 Farmer Panel",
                             font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"))
        title.pack()

        toolbar1 = ctk.CTkFrame(self)
        toolbar1.pack(fill="x", padx=20, pady=5)

        toolbar2 = ctk.CTkFrame(self)
        toolbar2.pack(fill="x", padx=20, pady=5)

        def create_button(parent, text, command, fg_color=None, tooltip=""):
            btn = ctk.CTkButton(parent, text=text, command=command,
                                font=self.app.font_normal,
                                fg_color=fg_color,
                                width=140, height=40,
                                corner_radius=8)
            btn.pack(side="left", padx=4)
            if tooltip:
                CTkToolTip(btn, message=tooltip, delay=0.5)
            return btn

        create_button(toolbar1, "📂 Импорт", self.import_accounts, tooltip="Импортировать аккаунты из .txt")
        create_button(toolbar1, "▶ Последовательно", self.start_selected_sequential, fg_color="#FF9800",
                     tooltip="Запустить выбранные аккаунты один за другим")
        create_button(toolbar1, "⏹ Остановить все", self.stop_all, tooltip="Остановить все аккаунты")
        create_button(toolbar1, "💀 Завершить всё", self.kill_all, tooltip="Принудительно завершить все процессы")
        create_button(toolbar1, "📦 Собрать дроп", self.collect_drop, fg_color="#4CAF50", tooltip="Собрать дроп")
        create_button(toolbar1, "📊 Статистика", self.show_stats, fg_color="#FF9800", tooltip="Показать статистику")

        create_button(toolbar2, "✅ Выбрать все", self.select_all, fg_color="#2196F3", tooltip="Выбрать все аккаунты")
        create_button(toolbar2, "❌ Снять все", self.deselect_all, fg_color="#9E9E9E", tooltip="Снять выбор со всех")
        create_button(toolbar2, "▶ Запустить выбранные", self.start_selected, fg_color="#4CAF50",
                     tooltip="Запустить отмеченные аккаунты")
        create_button(toolbar2, "⏹ Остановить выбранные", self.stop_selected, fg_color="#F44336",
                     tooltip="Остановить отмеченные аккаунты")
        create_button(toolbar2, "🔐 Сменить пароль", self.change_password, tooltip="Сменить мастер-пароль")

        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(filter_frame, text="Фильтр статуса:", font=self.app.font_normal).pack(side="left", padx=5)
        self.status_filter = ctk.CTkComboBox(filter_frame, values=["Все"] + [s.value for s in AccountStatus],
                                             width=200, font=self.app.font_normal)
        self.status_filter.set("Все")
        self.status_filter.pack(side="left", padx=5)
        ctk.CTkButton(filter_frame, text="Применить", command=self.refresh_accounts,
                      font=self.app.font_normal, width=100).pack(side="left", padx=5)

        self.cards_frame = ctk.CTkScrollableFrame(self, label_text="Аккаунты")
        self.cards_frame.pack(fill="both", expand=True, padx=20, pady=10)

        stats_frame = ctk.CTkFrame(self)
        stats_frame.pack(fill="x", padx=20, pady=5)
        self.stats_label = ctk.CTkLabel(stats_frame, text="Farmed this week: 0 | Drop received: 0 | CS2 запуск: OK",
                                        font=self.app.font_normal)
        self.stats_label.pack(side="left", padx=10)

        log_frame = ctk.CTkFrame(self)
        log_frame.pack(fill="x", padx=20, pady=10)
        log_header = ctk.CTkFrame(log_frame)
        log_header.pack(fill="x")
        ctk.CTkLabel(log_header, text="Лог событий:", font=self.app.font_large).pack(side="left")
        ctk.CTkButton(log_header, text="Очистить", command=self.clear_log,
                     font=self.app.font_normal, width=80).pack(side="right")
        self.log_text = ctk.CTkTextbox(log_frame, height=150, font=("Consolas", 11))
        self.log_text.pack(fill="both", expand=True, pady=5)

    def log(self, msg, level="INFO"):
        self.log_text.insert("end", f"{msg}\n")
        self.log_text.see("end")
        self.app.logger.log(level, msg)

    def clear_log(self):
        self.log_text.delete("0.0", "end")
        self.app.logger.log('INFO', 'Лог очищен')

    def select_all(self):
        accounts = self.account_manager.get_all()
        self.selected_accounts = {acc.id for acc in accounts}
        self.refresh_accounts()
        self.log(f"✅ Выбрано {len(self.selected_accounts)} аккаунтов")

    def deselect_all(self):
        self.selected_accounts.clear()
        self.refresh_accounts()
        self.log("❌ Выбор снят со всех аккаунтов")

    def start_selected(self):
        if not self.selected_accounts:
            CTkMessagebox(title="Предупреждение", message="Нет выбранных аккаунтов", icon="warning")
            return
        for acc_id in self.selected_accounts:
            threading.Thread(target=self.account_manager.start_account, args=(acc_id,), daemon=True).start()
        self.log(f"🚀 Запуск {len(self.selected_accounts)} выбранных аккаунтов...")

    def stop_selected(self):
        if not self.selected_accounts:
            CTkMessagebox(title="Предупреждение", message="Нет выбранных аккаунтов", icon="warning")
            return
        for acc_id in self.selected_accounts:
            self.account_manager.stop_account(acc_id)
        self.log(f"⏹ Остановка {len(self.selected_accounts)} выбранных аккаунтов")
        self.refresh_accounts()

    def toggle_selection(self, account_id: int):
        if account_id in self.selected_accounts:
            self.selected_accounts.remove(account_id)
        else:
            self.selected_accounts.add(account_id)

    def import_accounts(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        if not file_path:
            return
        try:
            count = self.account_manager.import_from_file(file_path)
            self.log(f"✅ Импортировано {count} аккаунтов", "INFO")
            self.refresh_accounts()
        except Exception as e:
            CTkMessagebox(title="Ошибка", message=str(e), icon="cancel")

    def refresh_accounts(self):
        for widget in self.cards_frame.winfo_children():
            widget.destroy()
        accounts = self.account_manager.get_all()
        filter_status = self.status_filter.get()
        if filter_status != "Все":
            accounts = [a for a in accounts if a.status.value == filter_status]
        row, col = 0, 0
        max_cols = 3
        for acc in accounts:
            card = AccountCard(self.cards_frame, acc, self,
                              selected=(acc.id in self.selected_accounts))
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        for i in range(max_cols):
            self.cards_frame.grid_columnconfigure(i, weight=1)
        self._update_stats()

    def _update_stats(self):
        accounts = self.account_manager.get_all()
        total_drop = sum(a.drop_total for a in accounts)
        total_time = sum(a.play_time_minutes for a in accounts)
        self.stats_label.configure(text=f"Farmed this week: {total_time//60}h {total_time%60}m | Drop received: {total_drop}")

    def auto_refresh(self):
        self.refresh_accounts()
        self.after(5000, self.auto_refresh)

    def start_selected_sequential(self):
        accounts = self.account_manager.get_all()
        if not accounts:
            CTkMessagebox(title="Предупреждение", message="Нет аккаунтов для запуска", icon="warning")
            return
        acc_ids = [acc.id for acc in accounts]
        self.log(f"🚀 Последовательный запуск {len(acc_ids)} аккаунтов...")
        self.account_manager.start_accounts_sequential(acc_ids)

    def stop_all(self):
        self.account_manager.stop_all()
        self.log("⏹ Все аккаунты остановлены")
        self.refresh_accounts()

    def kill_all(self):
        self.pm.kill_all()
        self.log("💀 Все процессы завершены")

    def collect_drop(self):
        accounts = self.account_manager.get_all()
        self.log("📦 Сбор дропа...")
        threading.Thread(target=self._collect, args=(accounts,), daemon=True).start()

    def _collect(self, accounts):
        total = self.drop_collector.collect_all(accounts)
        self.after(0, lambda: self.log(f"📦 Собрано {total} предметов", "INFO"))
        self.after(0, self.refresh_accounts)

    def show_stats(self):
        StatsWindow(self, self.drop_collector)

    def change_password(self):
        dlg = ChangePasswordDialog(self)
        self.wait_window(dlg)
        if dlg.new_password:
            try:
                self.app.db.change_master_password(dlg.new_password)
                self.log("🔐 Мастер-пароль успешно изменён")
            except Exception as e:
                CTkMessagebox(title="Ошибка", message=str(e), icon="cancel")