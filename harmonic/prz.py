from typing import Dict, Any, List
import numpy as np

class PRZCalculator:
    """
    Constructs Potential Reversal Zones (PRZ) from Fibonacci extensions & projections.
    """
    @staticmethod
    def calculate_abcd_prz(A: float, B: float, C: float, direction: str) -> Dict[str, float]:
        ab_dist = abs(B - A)
        bc_dist = abs(C - B)
        
        if direction == "BULLISH":
            # CD = AB projection from C
            proj_100 = C - (1.0 * ab_dist)
            proj_127 = C - (1.272 * bc_dist)
            proj_161 = C - (1.618 * bc_dist)
            
            projs = [proj_100, proj_127, proj_161]
            prz_low = min(projs)
            prz_high = max(projs)
            prz_mid = (prz_low + prz_high) / 2.0
        else: # BEARISH
            proj_100 = C + (1.0 * ab_dist)
            proj_127 = C + (1.272 * bc_dist)
            proj_161 = C + (1.618 * bc_dist)
            
            projs = [proj_100, proj_127, proj_161]
            prz_low = min(projs)
            prz_high = max(projs)
            prz_mid = (prz_low + prz_high) / 2.0
            
        return {
            'prz_low': prz_low,
            'prz_high': prz_high,
            'prz_mid': prz_mid,
            'projections': projs
        }

    @staticmethod
    def calculate_gartley_prz(X: float, A: float, B: float, C: float, direction: str) -> Dict[str, float]:
        xa_dist = abs(A - X)
        ab_dist = abs(B - A)
        bc_dist = abs(C - B)
        
        if direction == "BULLISH":
            d_xa_786 = X + (0.214 * xa_dist) # A - 0.786*XA (since X is low, A is high)
            d_abcd = C - (1.0 * ab_dist)
            d_bc_1618 = C - (1.618 * bc_dist)
            
            projs = [d_xa_786, d_abcd, d_bc_1618]
            prz_low = min(projs)
            prz_high = max(projs)
            prz_mid = (prz_low + prz_high) / 2.0
        else:
            d_xa_786 = X - (0.214 * xa_dist) # A + 0.786*XA (since X is high, A is low)
            d_abcd = C + (1.0 * ab_dist)
            d_bc_1618 = C + (1.618 * bc_dist)
            
            projs = [d_xa_786, d_abcd, d_bc_1618]
            prz_low = min(projs)
            prz_high = max(projs)
            prz_mid = (prz_low + prz_high) / 2.0
            
        return {
            'prz_low': prz_low,
            'prz_high': prz_high,
            'prz_mid': prz_mid,
            'projections': projs
        }
