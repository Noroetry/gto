from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class StandardHand:
    hand_id: str
    room_name: str
    game_type: str
    sb: float = 0.0          # En euros
    bb: float = 0.0          # En euros
    date_played: str = ""
    table_name: str = ""
    table_size: int = 0
    players: List[Dict[str, Any]] = field(default_factory=list)
    actions: Dict[str, List[str]] = field(default_factory=dict)
    board: List[str] = field(default_factory=list)
    winner: Optional[str] = None
    win_amount: float = 0.0  # En BB
    rake: float = 0.0        # En BB
    raw_text: str = field(default="", repr=False)