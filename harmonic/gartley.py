import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from harmonic.pivots import PivotPoint
from harmonic.states import PatternType, Direction, PatternState
from harmonic.geometry import GeometryCalculator
from harmonic.prz import PRZCalculator

class GartleyDetector:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        # Frozen tolerances
        self.ab_xa_target = 0.618
        self.ab_xa_tol = 0.080
        self.ad_xa_target = 0.786
        self.ad_xa_tol = 0.080
        self.bc_ab_min = 0.382
        self.bc_ab_max = 0.886
        self.cd_bc_min = 1.130
        self.cd_bc_max = 2.240

    def detect(self, pivots: List[PivotPoint], df: pd.DataFrame, symbol: str, timeframe: str) -> List[Dict[str, Any]]:
        patterns = []
        n_pivots = len(pivots)
        if n_pivots < 4:
            return patterns
            
        pip_size = 0.01 if 'JPY' in symbol else (0.10 if 'XAU' in symbol else 0.0001)
        current_price = float(df['close'].iloc[-1]) if not df.empty else 0.0
        
        # 1. Detect COMPLETED Gartley (requires 5 pivots X, A, B, C, D)
        for i in range(n_pivots - 4):
            pX, pA, pB, pC, pD = pivots[i], pivots[i+1], pivots[i+2], pivots[i+3], pivots[i+4]
            
            # Direction check
            if not pX.is_high and pA.is_high and not pB.is_high and pC.is_high and not pD.is_high:
                direction = Direction.BULLISH
                if not (pA.price > pC.price and pB.price > pX.price and pD.price > pX.price and pD.price < pB.price):
                    continue
            elif pX.is_high and not pA.is_high and pB.is_high and not pC.is_high and pD.is_high:
                direction = Direction.BEARISH
                if not (pA.price < pC.price and pB.price < pX.price and pD.price < pX.price and pD.price > pB.price):
                    continue
            else:
                continue
                
            # Geometry Ratios
            ab_xa = GeometryCalculator.calc_ratio(pA.price, pB.price, pX.price, pA.price)
            bc_ab = GeometryCalculator.calc_ratio(pB.price, pC.price, pA.price, pB.price)
            cd_bc = GeometryCalculator.calc_ratio(pC.price, pD.price, pB.price, pC.price)
            ad_xa = GeometryCalculator.calc_ratio(pA.price, pD.price, pX.price, pA.price)
            
            # Validation against frozen tolerances
            is_valid = (
                (abs(ab_xa - self.ab_xa_target) <= self.ab_xa_tol) and
                (abs(ad_xa - self.ad_xa_target) <= self.ad_xa_tol) and
                (self.bc_ab_min - 0.05 <= bc_ab <= self.bc_ab_max + 0.05) and
                (self.cd_bc_min - 0.05 <= cd_bc <= self.cd_bc_max + 0.05)
            )
            
            prz = PRZCalculator.calculate_gartley_prz(pX.price, pA.price, pB.price, pC.price, direction.value)
            prz_width_pips = abs(prz['prz_high'] - prz['prz_low']) / pip_size
            
            time_xa = abs(pA.bar_index - pX.bar_index)
            time_ad = abs(pD.bar_index - pA.bar_index)
            sym_ratio = (time_ad / (time_xa * 1.618)) if time_xa > 0 else 1.0
            
            ratios_dict = {'AB_XA': ab_xa, 'BC_AB': bc_ab, 'CD_BC': cd_bc, 'AD_XA': ad_xa}
            quality = GeometryCalculator.compute_quality_score(PatternType.GARTLEY, ratios_dict, prz_width_pips, sym_ratio)
            
            pat_id = f"{symbol}_{timeframe}_GARTLEY_{direction.value}_{pX.occurrence_time.strftime('%Y%m%d%H%M')}_{pD.occurrence_time.strftime('%Y%m%d%H%M')}"
            
            # Research Trade Levels
            ad_dist = abs(pD.price - pA.price)
            sl_price = pX.price - (10.0 * pip_size) if direction == Direction.BULLISH else pX.price + (10.0 * pip_size)
            tp1_price = pD.price + (0.382 * ad_dist) if direction == Direction.BULLISH else pD.price - (0.382 * ad_dist)
            tp2_price = pD.price + (0.618 * ad_dist) if direction == Direction.BULLISH else pD.price - (0.618 * ad_dist)
            
            state = PatternState.COMPLETED if is_valid else PatternState.INVALIDATED
            
            patterns.append({
                'pattern_id': pat_id,
                'symbol': symbol,
                'timeframe': timeframe,
                'pattern_type': PatternType.GARTLEY.value,
                'direction': direction.value,
                'state': state.value,
                'quality_score': quality,
                'is_accepted': is_valid,
                'X_time': pX.occurrence_time,
                'X_price': pX.price,
                'A_time': pA.occurrence_time,
                'A_price': pA.price,
                'B_time': pB.occurrence_time,
                'B_price': pB.price,
                'C_time': pC.occurrence_time,
                'C_price': pC.price,
                'D_time': pD.occurrence_time,
                'D_confirmation_time': pD.confirmation_time,
                'D_price': pD.price,
                'signal_available_time': pD.confirmation_time,
                'current_price': current_price,
                'prz_low': prz['prz_low'],
                'prz_high': prz['prz_high'],
                'prz_mid': prz['prz_mid'],
                'prz_width_pips': prz_width_pips,
                'ratios': ratios_dict,
                'entry_zone': (prz['prz_low'], prz['prz_high']),
                'structural_stop': sl_price,
                'target_1': tp1_price,
                'target_2': tp2_price
            })
            
        # 2. Detect FORMING & POTENTIAL_D Gartley (from last 4 pivots X, A, B, C)
        if n_pivots >= 4:
            pX, pA, pB, pC = pivots[-4], pivots[-3], pivots[-2], pivots[-1]
            if not pX.is_high and pA.is_high and not pB.is_high and pC.is_high:
                direction = Direction.BULLISH
                is_struct = (pA.price > pC.price and pB.price > pX.price)
            elif pX.is_high and not pA.is_high and pB.is_high and not pC.is_high:
                direction = Direction.BEARISH
                is_struct = (pA.price < pC.price and pB.price < pX.price)
            else:
                is_struct = False
                
            if is_struct:
                ab_xa = GeometryCalculator.calc_ratio(pA.price, pB.price, pX.price, pA.price)
                if abs(ab_xa - self.ab_xa_target) <= self.ab_xa_tol + 0.02:
                    prz = PRZCalculator.calculate_gartley_prz(pX.price, pA.price, pB.price, pC.price, direction.value)
                    prz_width_pips = abs(prz['prz_high'] - prz['prz_low']) / pip_size
                    
                    dist_to_prz = min(abs(current_price - prz['prz_low']), abs(current_price - prz['prz_high'])) / pip_size
                    state = PatternState.POTENTIAL_D if dist_to_prz <= 35.0 else PatternState.FORMING
                    
                    pat_id = f"{symbol}_{timeframe}_GARTLEY_{direction.value}_FORMING_{pX.occurrence_time.strftime('%Y%m%d%H%M')}_{pC.occurrence_time.strftime('%Y%m%d%H%M')}"
                    
                    proj_d = prz['prz_mid']
                    ad_dist = abs(proj_d - pA.price)
                    sl_price = pX.price - (10.0 * pip_size) if direction == Direction.BULLISH else pX.price + (10.0 * pip_size)
                    tp1_price = proj_d + (0.382 * ad_dist) if direction == Direction.BULLISH else proj_d - (0.382 * ad_dist)
                    tp2_price = proj_d + (0.618 * ad_dist) if direction == Direction.BULLISH else proj_d - (0.618 * ad_dist)
                    
                    patterns.append({
                        'pattern_id': pat_id,
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'pattern_type': PatternType.GARTLEY.value,
                        'direction': direction.value,
                        'state': state.value,
                        'quality_score': 80 if state == PatternState.POTENTIAL_D else 70,
                        'is_accepted': False,
                        'X_time': pX.occurrence_time,
                        'X_price': pX.price,
                        'A_time': pA.occurrence_time,
                        'A_price': pA.price,
                        'B_time': pB.occurrence_time,
                        'B_price': pB.price,
                        'C_time': pC.occurrence_time,
                        'C_price': pC.price,
                        'D_time': None,
                        'D_confirmation_time': None,
                        'D_price': proj_d,
                        'signal_available_time': None,
                        'current_price': current_price,
                        'prz_low': prz['prz_low'],
                        'prz_high': prz['prz_high'],
                        'prz_mid': prz['prz_mid'],
                        'prz_width_pips': prz_width_pips,
                        'ratios': {'AB_XA': ab_xa, 'AD_XA_proj': 0.786},
                        'entry_zone': (prz['prz_low'], prz['prz_high']),
                        'structural_stop': sl_price,
                        'target_1': tp1_price,
                        'target_2': tp2_price
                    })
                    
        return patterns
