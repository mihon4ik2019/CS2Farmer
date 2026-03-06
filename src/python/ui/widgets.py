import customtkinter as ctk
import threading
from CTkToolTip import CTkToolTip
from src.python.models import AccountStatus

class AccountCard(ctk.CTkFrame):
    def __init__(self, master, account, main_window, selected=False):
        super().__init__(master, corner_radius=10, border_width=2)
        self.account = account
        self.main_window = main_window
        self.app = main_window.app
        self.account_manager = main_window.account_manager
        self.selected = selected
        self.animation_running = False
        self.after_id = None

        self.status_colors = {
            AccountStatus.STOPPED: ("#808080", "#A9A9A9"),
            AccountStatus.STARTING: ("#FFA500", "#FFD700"),
            AccountStatus.IN_GAME: ("#008000", "#90EE90"),
            AccountStatus.ERROR: ("#FF0000", "#FFB6C1"),
            AccountStatus.BANNED: ("#8B0000", "#CD5C5C"),
            AccountStatus.MATCH_FOUND: ("#800080", "#DDA0DD"),
        }
        color_pair = self.status_colors.get(account.status, ("#FFFFFF", "#000000"))
        fg_color = color_pair[0] if self.app._get_appearance_mode() == "dark" else color_pair[1]
        
        if selected:
            self.configure(border_color="#2196F3", border_width=3)
        else:
            self.configure(border_color=fg_color, border_width=2)

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)

        self.checkbox = ctk.CTkCheckBox(self, text="", width=20, command=self.toggle_selection)
        self.checkbox.select() if selected else self.checkbox.deselect()
        self.checkbox.grid(row=0, column=0, padx=5, pady=5)

        self.login_label = ctk.CTkLabel(self, text=account.username, font=("Segoe UI", 14, "bold"))
        self.login_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        self.status_label = ctk.CTkLabel(self, text=account.status.value, font=("Segoe UI", 12), text_color=fg_color)
        self.status_label.grid(row=0, column=2, padx=5, pady=5, sticky="e")

        if account.steam_id:
            steam_label = ctk.CTkLabel(self, text=f"SteamID: {account.steam_id}", font=("Segoe UI", 10))
            steam_label.grid(row=1, column=1, columnspan=2, padx=5, sticky="w")

        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_columnconfigure(1, weight=1)

        self.time_label = ctk.CTkLabel(info_frame, text=f"⏱️ {account.play_time_minutes} мин", font=("Segoe UI", 10))
        self.time_label.grid(row=0, column=0, sticky="w")

        self.drop_label = ctk.CTkLabel(info_frame, text=f"📦 {account.drop_total} всего", font=("Segoe UI", 10))
        self.drop_label.grid(row=0, column=1, sticky="e")

        # Индикатор запуска CS2
        self.cs2_indicator = ctk.CTkLabel(self, text="⚫ CS2 ожидает", font=("Segoe UI", 9), text_color="gray")
        self.cs2_indicator.grid(row=3, column=1, columnspan=2, padx=5, pady=(0,2), sticky="w")

        actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        actions_frame.grid(row=4, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        actions_frame.grid_columnconfigure(0, weight=1)
        actions_frame.grid_columnconfigure(1, weight=1)
        actions_frame.grid_columnconfigure(2, weight=1)

        start_btn = ctk.CTkButton(actions_frame, text="▶", width=30, command=self.start_account)
        start_btn.grid(row=0, column=0, padx=2)
        CTkToolTip(start_btn, message="Запустить аккаунт")

        stop_btn = ctk.CTkButton(actions_frame, text="⏹", width=30, command=self.stop_account)
        stop_btn.grid(row=0, column=1, padx=2)
        CTkToolTip(stop_btn, message="Остановить аккаунт")

        settings_btn = ctk.CTkButton(actions_frame, text="⚙", width=30, command=self.open_settings)
        settings_btn.grid(row=0, column=2, padx=2)
        CTkToolTip(settings_btn, message="Настройки аккаунта")

        if account.status == AccountStatus.STARTING:
            self.start_animation()

    def toggle_selection(self):
        self.selected = self.checkbox.get() == 1
        self.main_window.toggle_selection(self.account.id)

    def start_animation(self):
        if self.animation_running:
            return
        self.animation_running = True
        colors = ["#FFA500", "#FFD700", "#FFA500"]
        self.animation_index = 0
        def animate():
            if not self.animation_running or self.account.status != AccountStatus.STARTING:
                self.animation_running = False
                return
            try:
                color = colors[self.animation_index % len(colors)]
                self.configure(border_color=color)
                self.status_label.configure(text_color=color)
                self.animation_index += 1
                self.after_id = self.after(500, animate)
            except:
                self.animation_running = False
        animate()

    def stop_animation(self):
        self.animation_running = False
        if self.after_id:
            self.after_cancel(self.after_id)
        color_pair = self.status_colors.get(self.account.status, ("#FFFFFF", "#000000"))
        fg_color = color_pair[0] if self.app._get_appearance_mode() == "dark" else color_pair[1]
        self.configure(border_color=fg_color)
        self.status_label.configure(text_color=fg_color)

    def start_account(self):
        threading.Thread(target=self.account_manager.start_account, args=(self.account.id,), daemon=True).start()
        self.main_window.log(f"🚀 Запуск аккаунта {self.account.username}")

    def stop_account(self):
        self.account_manager.stop_account(self.account.id)
        self.main_window.log(f"⏹ Остановка аккаунта {self.account.username}")

    def open_settings(self):
        from .dialogs import AccountSettingsDialog
        AccountSettingsDialog(self.main_window, self.account)

    def destroy(self):
        self.stop_animation()
        super().destroy()