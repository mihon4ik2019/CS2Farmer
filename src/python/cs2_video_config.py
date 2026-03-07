"""
CS2 Video Config - ТОЧНЫЙ ФОРМАТ ИЗ cs2_video.txt FSM Panel
"""
import os
from typing import Dict

from . import config
from .logger import SecureLogger

logger = SecureLogger()


class CS2VideoConfig:
    """ПРИМЕНЕНИЕ ВИДЕО НАСТРОЕК CS2 (ТОЧНЫЙ ФОРМАТ cs2_video.txt)"""
    
    def __init__(self):
        # ✅ ТОЧНЫЕ НАСТРОЙКИ ИЗ cs2_video.txt FSM Panel
        self.video_settings = {
            "Version": "16",
            "VendorID": "4318",
            "DeviceID": "7171",
            "setting.cpu_level": "0",
            "setting.gpu_mem_level": "0",
            "setting.gpu_level": "0",
            "setting.knowndevice": "1",
            "setting.defaultres": "360",
            "setting.defaultresheight": "270",
            "setting.refreshrate_numerator": "0",
            "setting.refreshrate_denominator": "0",
            "setting.fullscreen": "0",
            "setting.coop_fullscreen": "0",
            "setting.nowindowborder": "1",
            "setting.mat_vsync": "0",
            "setting.fullscreen_min_on_focus_loss": "1",
            "setting.high_dpi": "0",
            "Autoconfig": "2",
            "setting.shaderquality": "0",
            "setting.r_texturefilteringquality": "0",
            "setting.msaa_samples": "0",
            "setting.r_csgo_cmaa_enable": "0",
            "setting.r_low_latency": "0",
            "setting.aspectratiomode": "0",
            "setting.videocfg_texture_detail": "0",
            "setting.videocfg_shadow_quality": "0",
            "setting.videocfg_ao_detail": "0",
            "setting.videocfg_particle_detail": "0",
            "setting.videocfg_fsr_detail": "4",
            "setting.videocfg_hdr_detail": "3",
        }
    
    def get_launch_commands(self) -> list:
        """Получить команды для запуска"""
        commands = []
        
        for key, value in self.video_settings.items():
            if key not in ["Version", "Autoconfig", "VendorID", "DeviceID"]:
                commands.extend([f"+{key}", value])
        
        return commands
    
    def apply_to_account(self, username: str) -> bool:
        """
        Применить настройки видео для аккаунта
        Создаёт video.cfg в ТОЧНОМ формате как в FSM Panel
        """
        try:
            steam_data_path = os.path.join(
                config.STEAM_DATA_DIR,
                f"steam_{username}",
                "userdata",
                "0",
                "730",
                "local",
                "cfg"
            )
            
            os.makedirs(steam_data_path, exist_ok=True)
            
            video_cfg_path = os.path.join(steam_data_path, "video.cfg")
            
            # ✅ ТОЧНЫЙ ФОРМАТ КАК В cs2_video.txt FSM Panel
            cfg_content = '"video.cfg"\n{\n'
            
            # Сначала Version, VendorID, DeviceID, Autoconfig
            cfg_content += f'\t"Version"\t\t"{self.video_settings["Version"]}"\n'
            cfg_content += f'\t"VendorID"\t\t"{self.video_settings["VendorID"]}"\n'
            cfg_content += f'\t"DeviceID"\t\t"{self.video_settings["DeviceID"]}"\n'
            cfg_content += f'\t"Autoconfig"\t\t"{self.video_settings["Autoconfig"]}"\n'
            
            # Остальные настройки
            for key, value in self.video_settings.items():
                if key not in ["Version", "Autoconfig", "VendorID", "DeviceID"]:
                    cfg_content += f'\t"{key}"\t\t"{value}"\n'
            
            cfg_content += '}\n'
            
            with open(video_cfg_path, 'w', encoding='utf-8') as f:
                f.write(cfg_content)
            
            logger.debug(f"[CS2VideoConfig] Применено для {username}: {video_cfg_path}")
            return True
            
        except Exception as e:
            logger.error(f"[CS2VideoConfig] Ошибка: {e}")
            return False
    
    def get_all_settings(self) -> Dict[str, str]:
        """Получить все настройки"""
        return self.video_settings.copy()


video_config = CS2VideoConfig()