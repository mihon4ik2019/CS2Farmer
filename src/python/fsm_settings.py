"""
FSM Settings - ТОЧНЫЙ ПАРСИНГ settings.json FSM PANEL
Учитывает пробелы в ключах JSON (как в FSM Panel)
"""
import os
import json
from typing import Dict, Any, Optional, List

from . import config
from .logger import SecureLogger

logger = SecureLogger()


class FSMSettings:
    """ЗАГРУЗКА НАСТРОЕК ИЗ FSM PANEL settings.json"""
    
    def __init__(self):
        self.settings_file = config.SETTINGS_FILE
        self.fsm_cfg_file = config.FSM_CFG_FILE
        self.machine_convar_file = config.MACHINE_CONVAR_FILE
        self.settings = self._load_settings()
        self.convars = self._load_convars()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Загрузка settings.json с учётом пробелов в ключах"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    raw_settings = json.load(f)
                    
                    # ✅ ОЧИСТКА КЛЮЧЕЙ ОТ ПРОБЕЛОВ (как в FSM Panel)
                    settings = {}
                    for key, value in raw_settings.items():
                        clean_key = key.strip()
                        settings[clean_key] = value
                    
                    logger.info(f"[FSMSettings] Загружено: {self.settings_file}")
                    logger.debug(f"[FSMSettings] Ключей: {len(settings)}")
                    return settings
        except Exception as e:
            logger.debug(f"[FSMSettings] Ошибка загрузки settings.json: {e}")
        
        return {}
    
    def _load_convars(self) -> Dict[str, str]:
        """Загрузка cs2_machine_convars.vcfg"""
        convars = {}
        
        try:
            if os.path.exists(self.machine_convar_file):
                with open(self.machine_convar_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('//') and '"' in line:
                            parts = line.split('"')
                            if len(parts) >= 4:
                                key = parts[1].strip()
                                value = parts[3].strip()
                                convars[key] = value
                
                logger.info(f"[FSMSettings] Загружено конваров: {len(convars)}")
        except Exception as e:
            logger.debug(f"[FSMSettings] Ошибка загрузки convars: {e}")
        
        return convars
    
    def get(self, key: str, default: Any = None) -> Any:
        """Получение настройки"""
        clean_key = key.strip()
        return self.settings.get(clean_key, default)
    
    def get_convar(self, key: str, default: str = None) -> str:
        """Получение конвара"""
        return self.convars.get(key, default)
    
    def get_launch_options(self) -> List[str]:
        """Получение launch options из FSM settings (ADDITIONAL_LAUNCH_OPTIONS)"""
        options = self.get('ADDITIONAL_LAUNCH_OPTIONS', '')
        if options:
            return options.strip().split()
        return []
    
    def get_steam_launch_options(self) -> List[str]:
        """Получение Steam launch options"""
        options = self.get('STEAM_LAUNCH_OPTIONS', '')
        if options:
            return options.strip().split()
        return []
    
    def get_cs_resolution(self) -> tuple:
        """Получение разрешения CS2"""
        res = self.get('CS_RESOLUTION', '360x270')
        try:
            w, h = res.strip().split('x')
            return (int(w), int(h))
        except:
            return (360, 270)
    
    def get_bes_percent(self) -> int:
        """Получение BES процента (BES_REDUCTION_PERCENT)"""
        return self.get('BES_REDUCTION_PERCENT', 25)
    
    def get_accounts_delay(self) -> int:
        """Получение задержки между аккаунтами"""
        return self.get('ACCOUNTS_LAUNCH_DELAY', 0)
    
    def get_panel_position(self) -> tuple:
        """Получение позиции панели"""
        pos = self.get('PANEL_POSITION', '1150x665+208+208')
        try:
            parts = pos.strip().replace('x', '+').split('+')
            return (int(parts[2]), int(parts[3]))
        except:
            return (208, 208)
    
    def get_avast_sandbox_folder(self) -> str:
        """Получение папки Avast Sandbox"""
        return self.get('AVASTSANDBOX_FOLDER', r"C:\avast! sandbox")
    
    def get_map_load_delay(self) -> int:
        """Получение задержки загрузки карты"""
        return self.get('MAP_LOAD_DELAY', 65)
    
    def get_game_search_timeout(self) -> int:
        """Получение таймаута поиска игры"""
        return self.get('GAME_SEARCH_TIMEOUT', 90)
    
    def get_round_target(self) -> int:
        """Получение целевого количества раундов"""
        return self.get('ROUND_TARGET', 22)
    
    def is_running_2v2(self) -> bool:
        """Проверка режима 2v2"""
        return self.get('RUNNING2VS2', True)
    
    def is_auto_loot_enabled(self) -> bool:
        """Проверка авто-лута"""
        return self.get('AUTO_LOOT', True)
    
    def is_auto_accept_enabled(self) -> bool:
        """Проверка авто-принятия"""
        return self.get('ENABLE_AUTOACCEPT', True)


fsm_settings = FSMSettings()