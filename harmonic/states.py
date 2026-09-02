from enum import Enum

class PatternType(str, Enum):
    ABCD = "ABCD"
    GARTLEY = "GARTLEY"

class Direction(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"

class PatternState(str, Enum):
    FORMING = "FORMING"
    POTENTIAL_D = "POTENTIAL_D"
    COMPLETED = "COMPLETED"
    ACTIVE = "ACTIVE"
    TP1_HIT = "TP1_HIT"
    TP2_HIT = "TP2_HIT"
    SL_HIT = "SL_HIT"
    EXPIRED = "EXPIRED"
    INVALIDATED = "INVALIDATED"
