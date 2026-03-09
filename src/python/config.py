"""
CS2Farmer Configuration - ТОЧНЫЕ НАСТРОЙКИ ИЗ FSM PANEL v.2.8.5
Из settings.json + cs2_video.txt
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MAFILES_DIR = os.path.join(BASE_DIR, 'mafiles')
SESSIONS_DIR = os.path.join(BASE_DIR, 'sessions')
SETTINGS_DIR = os.path.join(BASE_DIR, 'settings')
STEAM_DATA_DIR = os.path.join(BASE_DIR, 'steam_data')
DB_PATH = os.path.join(DATA_DIR, 'cs2farmer.db')
LOG_FILE = os.path.join(DATA_DIR, 'secure.log')

# === STEAM ПАРАМЕТРЫ (ИЗ FSM PANEL settings.json) ===
STEAM_LAUNCH_OPTIONS = [
    "-nofriendsui",
    "-vgui",
    "-noreactlogin",
    "-noverifyfiles",
    "-nobootstrapupdate",
    "-skipinitialbootstrap",
    "-norepairfiles",
    "-overridepackageurl",
    "-disable-winh264",
    "-language", "english",
    "-no-cef-sandbox",
    "-tcp",
    "-silent",
]
DISABLE_STEAM_OVERLAY = True

# === CS2 ПАРАМЕТРЫ (ИЗ FSM PANEL ADDITIONAL_LAUNCH_OPTIONS) ===
CS2_LAUNCH_OPTIONS = [
    # Разрешение (из FSM Panel - 360x270)
    "-windowed", "-w", "360", "-h", "270",
    
    # Из FSM Panel ADDITIONAL_LAUNCH_OPTIONS
    "-swapcores",
    "-noqueuedload",
    "-vrdisable",
    "-nopreload",
    "-limitvsconst",
    "-softparticlesdefaultoff",
    "-nohltv",
    "-noaafonts",
    "-nosound",
    "-novid",
    
    # Минимальная графика
    "-low",
    "-nostartupmenu",
    "-nojoy",
    "-heapsize", "2097152",
    "-mem_mb", "2048",
    "-mem_max_mb", "2048",
    
    # Из FSM Panel
    "+violence_hblood", "0",
    "+sethdmodels", "0",
    "+mat_disable_fancy_blending", "1",
    "+r_dynamic", "0",
    "+engine_no_focus_sleep", "120",
    
    # Из cs2_video.txt
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
    
    # Из cs2_video.txt (setting.*)
    "+setting.gpu_level", "0",
    "+setting.gpu_mem_level", "0",
    "+setting.cpu_level", "0",
    "+setting.shaderquality", "0",
    "+setting.r_texturefilteringquality", "0",
    "+setting.msaa_samples", "0",
    "+setting.r_csgo_cmaa_enable", "0",
    "+setting.videocfg_texture_detail", "0",
    "+setting.videocfg_shadow_quality", "0",
    "+setting.videocfg_ao_detail", "0",
    "+setting.videocfg_particle_detail", "0",
    "+setting.videocfg_fsr_detail", "4",
    "+setting.videocfg_hdr_detail", "3",
    "+setting.nowindowborder", "1",
    "+setting.defaultres", "360",
    "+setting.defaultresheight", "270",
    "+setting.fullscreen", "0",
    "+setting.coop_fullscreen", "0",
    "+setting.refreshrate_numerator", "0",
    "+setting.refreshrate_denominator", "0",
    "+setting.high_dpi", "0",
    "+setting.fullscreen_min_on_focus_loss", "1",
    "+setting.r_low_latency", "0",
    "+setting.aspectratiomode", "0",
    "+setting.knowndevice", "1",
    
    # Отключение popup
    "+cl_popupwindows", "0",
    "+cl_showloadout", "0",
    "+cl_autohelp", "0",
    "+cl_teammate_colors_show", "0",
    "+cl_disablefreezecam", "1",
    "+cl_showhelp", "0",
    
    # Дополнительно
    "+host_thread_mode", "2",
    "+snd_mixahead", "0.05",
    "+r_waterforceexpensive", "0",
    "+r_waterforcereflectentities", "0",
    "+r_drawtracers_firstperson", "0",
    "+fps_max", "30",
]

# === РАЗРЕШЕНИЕ (ИЗ FSM PANEL) ===
CS_RESOLUTION = "360x270"
CS_WIDTH = 360
CS_HEIGHT = 270

# === ЗАДЕРЖКИ (ИЗ FSM PANEL settings.json) ===
ACCOUNTS_LAUNCH_DELAY = 0  # ✅ Из FSM Panel
MIN_STEAM_WAIT_TIME = 8
DELAY_AFTER_LOGIN = 6
DELAY_BEFORE_CS2 = 2
DELAY_AFTER_2FA = 20
CS2_LOAD_SECONDS = 25
MAP_LOAD_DELAY = 65  # ✅ Из FSM Panel
GAME_SEARCH_TIMEOUT = 90  # ✅ Из FSM Panel
ROUND_TARGET = 22  # ✅ Из FSM Panel
AUTODISCONNECTS_DELAY = 11  # ✅ Из FSM Panel

# === ОКНА (2x2 СЕТКА) ===
WINDOW_OFFSET_X = 360
WINDOW_OFFSET_Y = 270
VERIFY_WINDOW_POSITION = True
WINDOW_POSITION_RETRIES = 5
WINDOW_POSITION_TOLERANCE = 10
RESET_WINDOW_POSITION_ON_START = True
KEEP_WINDOW_POSITION = True

# === POPUP (ОТКЛЮЧЕНО - ТОЛЬКО ПАРАМЕТРЫ) ===
AUTO_CLOSE_POPUPS = False
POPUP_CHECK_INTERVAL = 0

# === BES (ИЗ FSM PANEL) ===
BES_CPU_LIMIT = 25  # ✅ Из FSM Panel (BES_REDUCTION_PERCENT)
BES_AUTO_APPLY = True
BES_PATH = r"C:\Users\mihon\Desktop\CS2Farmer\BES\BES.exe"
VERIFY_BES_APPLICATION = True
BES_RETRIES = 3
BES_CHECK_INTERVAL = 1.0

# === AVAST SANDBOX (ИЗ FSM PANEL) ===
AVASTSANDBOX_FOLDER = r"C:\avast! sandbox"  # ✅ Из FSM Panel
AVAST_EXCLUSIONS = [
    r"C:\Program Files (x86)\Steam",
    r"C:\Program Files\Steam",
    AVASTSANDBOX_FOLDER,
    BASE_DIR,
    SESSIONS_DIR,
    SETTINGS_DIR,
    STEAM_DATA_DIR,
]

# === STEAM GUARD ===
STEAM_GUARD_REQUIRED = True
SKIP_2FA = False
ACCOUNT_LOGIN_ATTEMPTS = 2  # ✅ Из FSM Panel

# === БЕЗОПАСНОСТЬ ===
CHECK_BANS_BEFORE_START = False
RATE_LIMIT_DELAY_MINUTES = 5
MAX_ACCOUNT_RETRIES = 2

# === ТАЙМАУТЫ ===
TIMEOUT_STEAM_WINDOW = 45
TIMEOUT_CS2_PROCESS = 180
TIMEOUT_LIBRARY_WINDOW = 60
TIMEOUT_WINDOW_POSITION = 30
TIMEOUT_BES_APPLICATION = 10

# === БЫСТРЫЙ ПОИСК ===
SEARCH_INTERVAL_FAST = 0.03
SEARCH_INTERVAL_NORMAL = 0.05

# === ЛОГИРОВАНИЕ ===
ENABLE_DETAILED_LOGS = True
LOG_TO_FILE = True
LOG_TO_UI = True
LOG_BES_APPLICATION = True
LOG_WINDOW_POSITION = True
LOG_PROCESS_INFO = True
LOG_CS2_WAIT_STATUS = False
CS2_WAIT_LOG_INTERVAL = 10
MAX_LOG_SIZE_MB = 10
LOG_ROTATION = True

# === ГАРАНТИИ ===
FORCE_CLOSE_LIBRARY = True
WAIT_CS2_LOAD = True
MAX_LIBRARY_CLOSE_ATTEMPTS = 10

# === SESSION FILES ===
SAVE_SESSIONS = True
LOAD_SESSIONS = True
SESSION_TIMEOUT_HOURS = 168

# === SETTINGS ===
AUTO_CREATE_SETTINGS = True
SETTINGS_FILE = os.path.join(SETTINGS_DIR, 'settings.json')
FSM_CFG_FILE = os.path.join(SETTINGS_DIR, 'fsm.cfg')
MACHINE_CONVAR_FILE = os.path.join(SETTINGS_DIR, 'cs2_machine_convars.vcfg')

# === ОПТИМИЗАЦИИ ===
HIGH_PRIORITY = True
CLEAR_STEAM_CACHE = False
PREWARM_NETWORK = True
DISABLE_WINDOWS_DEFENDER = True
PROCESS_AFFINITY = True
PRELOAD_DLLS = True
KEEP_STEAM_RUNNING = True
PARALLEL_CS2_WAIT = False
USE_SEPARATE_STEAM_DATA = True

# === FSM PANEL СОВМЕСТИМОСТЬ ===
RUNNING2VS2 = True  # ✅ Из FSM Panel
DISABLE_CS2_BACKGROUND = True  # ✅ Из FSM Panel
DROP_HISTORY_CACHE = True  # ✅ Из FSM Panel
AUTO_LOOT = True  # ✅ Из FSM Panel
DELAY_BETWEEN_TRADES = 40  # ✅ Из FSM Panel
ENABLE_AUTOACCEPT = True  # ✅ Из FSM Panel
AUTOACCEPT_READ_TIME = 300  # ✅ Из FSM Panel
CS2_AUTOUPDATER_ENABLED = True  # ✅ Из FSM Panel
ANCIENT_MAP_PRELOAD = True  # ✅ Из FSM Panel

# === STEAM SERVICE FIX ===
FIX_STEAM_SERVICE = True  # ✅ Авто-исправление Steam Service
STEAM_SERVICE_PATH = r"C:\Program Files (x86)\Steam\bin\SteamService.exe"

# === ВОССТАНОВЛЕНИЕ ===
AUTO_RECOVER_ON_ERROR = True
CLEANUP_ON_EXIT = True
AUTO_RESTART_ON_CRASH = True
MAX_RESTART_ATTEMPTS = 3

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MAFILES_DIR, exist_ok=True)
os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(SETTINGS_DIR, exist_ok=True)
os.makedirs(STEAM_DATA_DIR, exist_ok=True)