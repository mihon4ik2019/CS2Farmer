import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from src.python.models import MatchScoreMode

class MasterPasswordDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.password = None
        self.title("🔐 Мастер-пароль")
        self.geometry("400x250")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        ctk.CTkLabel(self, text="Введите мастер-пароль для доступа к данным:",
                     font=("Segoe UI", 12)).pack(pady=20)
        self.entry = ctk.CTkEntry(self, show="*", width=250, font=("Segoe UI", 12))
        self.entry.pack(pady=10)
        self.entry.focus()

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="OK", command=self.ok, width=100).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Отмена", command=self.cancel, width=100).pack(side="left", padx=10)

        self.protocol("WM_DELETE_WINDOW", self.cancel)

    def ok(self):
        self.password = self.entry.get()
        if self.password:
            self.destroy()
        else:
            CTkMessagebox(title="Ошибка", message="Пароль не может быть пустым", icon="warning")

    def cancel(self):
        self.password = None
        self.destroy()

class ChangePasswordDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.new_password = None
        self.title("🔐 Смена мастер-пароля")
        self.geometry("400x250")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        ctk.CTkLabel(self, text="Введите новый мастер-пароль:", font=("Segoe UI", 12)).pack(pady=20)
        self.entry = ctk.CTkEntry(self, show="*", width=250, font=("Segoe UI", 12))
        self.entry.pack(pady=10)
        self.entry.focus()

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="OK", command=self.ok, width=100).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Отмена", command=self.cancel, width=100).pack(side="left", padx=10)

    def ok(self):
        self.new_password = self.entry.get()
        if self.new_password:
            self.destroy()
        else:
            CTkMessagebox(title="Ошибка", message="Пароль не может быть пустым", icon="warning")

    def cancel(self):
        self.new_password = None
        self.destroy()

class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("⚙ Настройки")
        self.geometry("450x350")
        self.transient(parent)
        self.grab_set()

        ctk.CTkLabel(self, text="Steam API Key:", font=("Segoe UI", 12)).pack(pady=5)
        self.api_key_entry = ctk.CTkEntry(self, width=350, font=("Segoe UI", 12))
        self.api_key_entry.insert(0, parent.app.db.get_setting('steam_api_key') or '')
        self.api_key_entry.pack(pady=5)

        ctk.CTkLabel(self, text="Путь к Steam:", font=("Segoe UI", 12)).pack(pady=5)
        self.steam_path_entry = ctk.CTkEntry(self, width=350, font=("Segoe UI", 12))
        default_path = r"C:\Program Files (x86)\Steam\steam.exe"
        self.steam_path_entry.insert(0, parent.app.db.get_setting('steam_path') or default_path)
        self.steam_path_entry.pack(pady=5)

        ctk.CTkLabel(self, text="Интервал Anti-AFK (сек):", font=("Segoe UI", 12)).pack(pady=5)
        self.afk_interval = ctk.CTkEntry(self, width=350, font=("Segoe UI", 12))
        self.afk_interval.insert(0, parent.app.db.get_setting('afk_interval') or '60')
        self.afk_interval.pack(pady=5)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="Сохранить", command=self.save, width=120).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Отмена", command=self.destroy, width=120).pack(side="left", padx=10)

    def save(self):
        self.parent.app.db.set_setting('steam_api_key', self.api_key_entry.get())
        self.parent.app.db.set_setting('steam_path', self.steam_path_entry.get())
        self.parent.app.db.set_setting('afk_interval', self.afk_interval.get())
        self.parent.log("⚙ Настройки сохранены")
        self.destroy()

class AccountSettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, account):
        super().__init__(parent)
        self.parent = parent
        self.account = account
        self.title(f"⚙ Настройки аккаунта {account.username}")
        self.geometry("400x300")
        self.transient(parent)
        self.grab_set()

        ctk.CTkLabel(self, text="Anti-AFK:", font=("Segoe UI", 12)).pack(pady=5)
        self.anti_afk_var = ctk.BooleanVar(value=account.anti_afk_enabled)
        ctk.CTkCheckBox(self, text="Включить Anti-AFK", variable=self.anti_afk_var,
                        font=("Segoe UI", 12)).pack(pady=5)

        ctk.CTkLabel(self, text="Режим счёта:", font=("Segoe UI", 12)).pack(pady=5)
        self.mode_var = ctk.StringVar(value=account.match_score_mode.value)
        modes = [m.value for m in MatchScoreMode]
        ctk.CTkComboBox(self, values=modes, variable=self.mode_var,
                        font=("Segoe UI", 12), width=200).pack(pady=5)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="Сохранить", command=self.save, width=120).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Отмена", command=self.destroy, width=120).pack(side="left", padx=10)

    def save(self):
        self.account.anti_afk_enabled = self.anti_afk_var.get()
        self.account.match_score_mode = MatchScoreMode(self.mode_var.get())
        self.parent.account_manager.db.update_account(self.account)
        self.parent.log(f"⚙ Настройки аккаунта {self.account.username} сохранены")
        self.destroy()