from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class StandardHandTest:
    hand_id: str
    date: str
    table: str
    size_table: int
    game_type: str
    hero: str
    hero_position: str
    hero_cards: List[str]
    stacks: Dict[str, float]
    actions: Dict[str, List[str]]
    board: List[str]
    winner: Optional[str]
    win_amount: float      # En BB
    sb: float              # En euros
    bb: float              # En euros
    rake: float            # En BB
    raw_text: str = field(repr=False)