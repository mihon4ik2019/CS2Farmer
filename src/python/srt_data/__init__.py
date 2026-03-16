"""SRT Data Package"""
import os

SRT_DATA_DIR = os.path.dirname(os.path.abspath(__file__))
SERVERS_FILE = os.path.join(SRT_DATA_DIR, 'servers.json')
REGIONS_FILE = os.path.join(SRT_DATA_DIR, 'regions.json')
CONFIG_FILE = os.path.join(SRT_DATA_DIR, 'srt_config.json')