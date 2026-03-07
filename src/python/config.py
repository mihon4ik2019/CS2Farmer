"""
CS2Farmer Configuration - 30С ПОСЛЕ ПРОЦЕССА
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MAFILES_DIR = os.path.join(BASE_DIR, 'mafiles')
DB_PATH = os.path.join(DATA_DIR, 'cs2farmer.db')
LOG_FILE = os.path.join(DATA_DIR, 'secure.log')

# === STEAM ПАРАМЕТРЫ ===
STEAM_LAUNCH_OPTIONS = [
    "-nofriendsui", "-vgui", "-noreactlogin",
    "-noverifyfiles", "-nobootstrapupdate",
    "-skipinitialbootstrap", "-language", "english",
    "-tcp", "-no-cef-sandbox",
    "-no-browser", "-nomusic", "-nocontroller",
    "-nocloudsync", "-nobroadcasting",
    "-disable-winh264", "-no-shader-cache",
    "-disablehtmlaudio", "-silent",
]
DISABLE_STEAM_OVERLAY = True

# === CS2 ПАРАМЕТРЫ ===
CS2_LAUNCH_OPTIONS = [
    "-windowed", "-w", "640", "-h", "480",
    "-low", "-nostartupmenu", "-nojoy",
    "-novid", "-nosound", "-noaafonts",
    "-nohltv", "-nopreload", "-noqueuedload",
    "-heapsize", "4194304",
    "-mem_mb", "4096",
    "-mem_max_mb", "4096",
    "-swapcores", "-vrdisable",
    "-limitvsconst", "-softparticlesdefaultoff",
    "-mat_disable_fancy_blending", "1",
    "+mat_fullscreen", "0",
    "+window_mode", "1",
    "+mat_config_current", "0",
    "+mat_queue_mode", "2",
    "+mat_antialias", "0",
    "+mat_aaquality", "0",
    "+mat_forceaniso", "0",
    "+mat_vsync", "0",
    "+mat_triplebuffered", "0",
    "+mat_grain_scale_override", "0",
    "+gpu_level", "0",
    "+mat_disable_bloom", "1",
    "+mat_disable_dof", "1",
    "+mat_disable_tonemapping", "1",
    "+mat_motion_blur_enabled", "0",
    "+mat_dynamic_tonemapping", "0",
    "+mat_powersavingsmode", "1",
    "+violence_hblood", "0",
    "+sethdmodels", "0",
    "+r_dynamic", "0",
    "+fps_max", "30",
    "+engine_no_focus_sleep", "120",
    "+cl_disablefreezecam", "1",
    "+cl_showhelp", "0",
    "+host_thread_mode", "2",
    "+snd_mixahead", "0.05",
    "+r_waterforceexpensive", "0",
    "+r_waterforcereflectentities", "0",
    "+r_drawtracers_firstperson", "0",
    "+cl_showloadout", "0",
    "+cl_autohelp", "0",
    "+cl_teammate_colors_show", "0",
]

CS_RESOLUTION = "640x480"
CS_WIDTH = 640
CS_HEIGHT = 480

# === ЗАДЕРЖКИ ===
ACCOUNTS_LAUNCH_DELAY = 90
MIN_STEAM_WAIT_TIME = 15
DELAY_AFTER_LOGIN = 10
DELAY_BEFORE_CS2 = 5
DELAY_AFTER_2FA = 40
CS2_LOAD_WAIT = 30  # ✅ 30 СЕКУНД ПОСЛЕ НАХОЖДЕНИЯ ПРОЦЕССА

# === ОКНА (2x2 СЕТКА) ===
WINDOW_OFFSET_X = 640
WINDOW_OFFSET_Y = 480

# === BES ===
BES_CPU_LIMIT = 25
BES_AUTO_APPLY = True
BES_PATH = r"C:\Users\mihon\Desktop\CS2Farmer\BES\BES.exe"

# === AVAST SANDBOX ===
AVAST_EXCLUSIONS = [
    r"C:\Program Files (x86)\Steam",
    r"C:\Program Files\Steam",
    r"C:\avast! sandbox",
    BASE_DIR,
]

# === БЕЗОПАСНОСТЬ ===
CHECK_BANS_BEFORE_START = False
RATE_LIMIT_DELAY_MINUTES = 5

# === ТАЙМАУТЫ ===
TIMEOUT_STEAM_WINDOW = 60
TIMEOUT_CS2_PROCESS = 180
TIMEOUT_LIBRARY_WINDOW = 90

# === БЫСТРЫЙ ПОИСК ===
SEARCH_INTERVAL_FAST = 0.05
SEARCH_INTERVAL_NORMAL = 0.1

# === ГАРАНТИИ ===
FORCE_CLOSE_LIBRARY = True
WAIT_CS2_LOAD = True
CS2_LOAD_SECONDS = 30  # ✅ 30 СЕКУНД
MAX_LIBRARY_CLOSE_ATTEMPTS = 10

# === ОПТИМИЗАЦИИ ===
HIGH_PRIORITY = True
CLEAR_STEAM_CACHE = True
PREWARM_NETWORK = True
DISABLE_WINDOWS_DEFENDER = True
PROCESS_AFFINITY = True
PRELOAD_DLLS = True
KEEP_STEAM_RUNNING = True

# === ЛОГИРОВАНИЕ ===
ENABLE_DETAILED_LOGS = True
LOG_TO_FILE = True
LOG_TO_UI = True

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MAFILES_DIR, exist_ok=True)