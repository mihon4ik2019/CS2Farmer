from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Optional

class AccountStatus(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    IN_GAME = "in_game"
    ERROR = "error"
    BANNED = "banned"
    CREATING_LOBBY = "creating_lobby"
    WAITING_IN_LOBBY = "waiting_in_lobby"
    SEARCHING_MATCH = "searching_match"
    MATCH_FOUND = "match_found"

class LobbyRole(Enum):
    NONE = "none"
    HOST = "host"
    MEMBER = "member"

class MatchScoreMode(Enum):
    TIE_8_8 = "8:8"
    RANDOM = "random"
    SIMULATION = "simulation"

@dataclass
class Account:
    id: int
    username: str
    password: str
    ma_file_path: Optional[str] = None
    steam_id: Optional[str] = None
    status: AccountStatus = AccountStatus.STOPPED
    status_message: Optional[str] = None
    last_login: Optional[datetime] = None
    play_time_minutes: int = 0
    drop_today: int = 0
    drop_week: int = 0
    drop_month: int = 0
    drop_total: int = 0
    lobby_role: LobbyRole = LobbyRole.NONE
    lobby_code: Optional[str] = None
    team_index: int = -1
    anti_afk_enabled: bool = True
    match_score_mode: MatchScoreMode = MatchScoreMode.TIE_8_8