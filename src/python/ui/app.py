import customtkinter as ctk
from .main_window import MainWindow
from .dialogs import MasterPasswordDialog
from src.python.database import Database
from src.python.process_manager import ProcessManager
from src.python.account_manager import AccountManager
from src.python.ban_checker import BanChecker
from src.python.drop_collector import DropCollector
from src.python.logger import SecureLogger
from src.python import config

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CS2 Farmer Panel")
        self.geometry("1500x850")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.font_large = ctk.CTkFont(family="Segoe UI", size=18, weight="bold")
        self.font_normal = ctk.CTkFont(family="Segoe UI", size=14)
        self.font_small = ctk.CTkFont(family="Segoe UI", size=12)

        dlg = MasterPasswordDialog(self)
        self.wait_window(dlg)
        if not dlg.password:
            self.destroy()
            return
        self.master_password = dlg.password

        try:
            self.db = Database(config.DB_PATH, self.master_password)
        except ValueError as e:
            from CTkMessagebox import CTkMessagebox
            CTkMessagebox(title="Ошибка", message=str(e), icon="cancel")
            self.destroy()
            return

        self.pm = ProcessManager()
        self.ban_checker = BanChecker(self.db.get_setting('steam_api_key') or '')
        self.account_manager = AccountManager(self.db, self.pm, self.ban_checker)
        self.drop_collector = DropCollector(self.db)
        self.logger = SecureLogger(config.LOG_FILE, self.master_password)

        self.logger.log('INFO', 'Приложение запущено')

        self.main_window = MainWindow(self)
        self.main_window.pack(fill="both", expand=True)

        settings_frame = ctk.CTkFrame(self)
        settings_frame.place(relx=0.98, rely=0.02, anchor="ne")

        self.appearance_menu = ctk.CTkOptionMenu(settings_frame, values=["dark", "light"],
                                                 command=self.change_appearance)
        self.appearance_menu.set("dark")
        self.appearance_menu.pack(side="left", padx=5)
        from CTkToolTip import CTkToolTip
        CTkToolTip(self.appearance_menu, message="Переключить тему оформления")

        self.scale_var = ctk.DoubleVar(value=1.0)
        self.scale_slider = ctk.CTkSlider(settings_frame, from_=0.8, to=1.5,
                                          variable=self.scale_var, command=self.change_scale)
        self.scale_slider.pack(side="left", padx=5)
        CTkToolTip(self.scale_slider, message="Масштаб интерфейса")

        self.scale_label = ctk.CTkLabel(settings_frame, text="100%", font=self.font_small)
        self.scale_label.pack(side="left", padx=5)

    def change_appearance(self, mode):
        ctk.set_appearance_mode(mode)
        self.logger.log('INFO', f'Тема изменена на {mode}')

    def change_scale(self, value):
        self.scale_label.configure(text=f"{int(value*100)}%")