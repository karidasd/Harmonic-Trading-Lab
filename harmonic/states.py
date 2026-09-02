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
    INVALIDATED = "INVALIDATED"
