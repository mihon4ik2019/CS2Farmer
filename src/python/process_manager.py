import subprocess
import time
import os
from typing import Optional

class ProcessManager:
    STEAM_LAUNCH_OPTIONS = "-login -nofriendsui -vgui -noreactlogin -noverifyfiles -nobootstrapupdate -skipinitialbootstrap -norepairfiles -overridepackageurl -disable-winh264 -language english"
    CS2_LAUNCH_OPTIONS = (
        "-swapcores -noqueuedload -vrdisable -windowed -nopreload -limitvsconst "
        "-softparticlesdefaultoff -nohltv -noaafonts -nosound -novid "
        "+violence_hblood 0 +sethdmodels 0 +mat_disable_fancy_blending 1 +r_dynamic 0 "
        "+engine_no_focus_sleep 120 -w 640 -h 480"
    )

    @staticmethod
    def find_steam_path() -> Optional[str]:
        steam_path = r"C:\Program Files (x86)\Steam\steam.exe"
        if os.path.exists(steam_path):
            return steam_path
        steam_path = r"C:\Program Files\Steam\steam.exe"
        if os.path.exists(steam_path):
            return steam_path
        return None

    @staticmethod
    def kill_all_steam():
        os.system("taskkill /f /im steam.exe 2>nul")
        time.sleep(2)

    @staticmethod
    def start_cs2() -> bool:
        steam_uri = "steam://rungameid/730//" + ProcessManager.CS2_LAUNCH_OPTIONS.replace(" ", "/")
        try:
            subprocess.Popen(["cmd", "/c", "start", steam_uri], shell=True)
            print(f"[ProcessManager] CS2 запущен с параметрами")
            return True
        except Exception as e:
            print(f"[ProcessManager] Ошибка запуска CS2: {e}")
            return False

    @staticmethod
    def kill_all():
        os.system("taskkill /f /im cs2.exe 2>nul")