import numpy as np
from typing import Dict, Any, Tuple
from harmonic.states import PatternType, Direction, PatternState

class GeometryCalculator:
    """
    Calculates harmonic Fibonacci ratios and objective 0-100 GEOMETRY QUALITY score.
    """
    @staticmethod
    def calc_ratio(leg1_p1: float, leg1_p2: float, leg2_p1: float, leg2_p2: float) -> float:
        d1 = abs(leg1_p2 - leg1_p1)
        d2 = abs(leg2_p2 - leg2_p1)
        if d2 <= 1e-8:
            return np.nan
        return d1 / d2

    @staticmethod
    def compute_quality_score(
        pattern_type: PatternType,
        ratios: Dict[str, float],
        prz_width_pips: float,
        time_symmetry_ratio: float = 1.0
    ) -> int:
        """
        Deterministic 0-100 GEOMETRY QUALITY score based exclusively on Fibonacci closeness,
        PRZ tight clustering, and leg bar-time symmetry.
        """
        score = 100.0
        
        if pattern_type == PatternType.ABCD:
            # Target CD/AB = 1.0
            cd_ab = ratios.get('CD_AB', 1.0)
            err_cd_ab = abs(cd_ab - 1.0) / 0.15 # 0 to 1
            
            # BC/AB target range 0.382 to 0.886
            bc_ab = ratios.get('BC_AB', 0.618)
            err_bc = 0.0
            if bc_ab < 0.382:
                err_bc = (0.382 - bc_ab) / 0.382
            elif bc_ab > 0.886:
                err_bc = (bc_ab - 0.886) / 0.886
                
            ratio_penalty = (0.7 * err_cd_ab + 0.3 * err_bc) * 40.0
            score -= min(40.0, ratio_penalty)
            
        elif pattern_type == PatternType.GARTLEY:
            # Target AB/XA = 0.618
            ab_xa = ratios.get('AB_XA', 0.618)
            err_b = abs(ab_xa - 0.618) / 0.08
            
            # Target AD/XA = 0.786
            ad_xa = ratios.get('AD_XA', 0.786)
            err_d = abs(ad_xa - 0.786) / 0.08
            
            ratio_penalty = (0.5 * err_b + 0.5 * err_d) * 40.0
            score -= min(40.0, ratio_penalty)
            
        # PRZ tightness penalty (tighter PRZ = higher quality score)
        prz_penalty = min(30.0, (prz_width_pips / 35.0) * 30.0)
        score -= prz_penalty
        
        # Time symmetry penalty (CD time vs AB time)
        sym_err = abs(time_symmetry_ratio - 1.0)
        sym_penalty = min(30.0, sym_err * 20.0)
        score -= sym_penalty
        
        return max(0, min(100, int(round(score))))
