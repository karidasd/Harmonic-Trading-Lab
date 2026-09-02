import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from harmonic.pivots import PivotPoint
from harmonic.states import PatternType, Direction, PatternState
from harmonic.geometry import GeometryCalculator
from harmonic.prz import PRZCalculator

class ABCDDetector:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        # Frozen tolerances
        self.bc_ab_min = 0.382
        self.bc_ab_max = 0.886
        self.cd_bc_min = 1.130
        self.cd_bc_max = 2.618
        self.cd_ab_target = 1.000
        self.cd_ab_tol = 0.150

    def detect(self, pivots: List[PivotPoint], df: pd.DataFrame, symbol: str, timeframe: str) -> List[Dict[str, Any]]:
        patterns = []
        n_pivots = len(pivots)
        if n_pivots < 3:
            return patterns
            
        pip_size = 0.01 if 'JPY' in symbol else (0.10 if 'XAU' in symbol else 0.0001)
        current_price = float(df['close'].iloc[-1]) if not df.empty else 0.0
        
        # 1. Detect COMPLETED AB=CD (requires 4 pivots A, B, C, D)
        for i in range(n_pivots - 3):
            pA, pB, pC, pD = pivots[i], pivots[i+1], pivots[i+2], pivots[i+3]
            
            # Direction check
            if pA.is_high and not pB.is_high and pC.is_high and not pD.is_high:
                direction = Direction.BULLISH
                if not (pA.price > pC.price and pD.price < pB.price):
                    continue
            elif not pA.is_high and pB.is_high and not pC.is_high and pD.is_high:
                direction = Direction.BEARISH
                if not (pA.price < pC.price and pD.price > pB.price):
                    continue
            else:
                continue
                
            # Geometry Ratios
            bc_ab = GeometryCalculator.calc_ratio(pB.price, pC.price, pA.price, pB.price)
            cd_bc = GeometryCalculator.calc_ratio(pC.price, pD.price, pB.price, pC.price)
            cd_ab = GeometryCalculator.calc_ratio(pC.price, pD.price, pA.price, pB.price)
            
            # Validation against frozen tolerances
            is_valid = (
                (self.bc_ab_min - 0.05 <= bc_ab <= self.bc_ab_max + 0.05) and
                (self.cd_bc_min - 0.05 <= cd_bc <= self.cd_bc_max + 0.05) and
                (abs(cd_ab - self.cd_ab_target) <= self.cd_ab_tol)
            )
            
            prz = PRZCalculator.calculate_abcd_prz(pA.price, pB.price, pC.price, direction.value)
            prz_width_pips = abs(prz['prz_high'] - prz['prz_low']) / pip_size
            
            time_ab = abs(pB.bar_index - pA.bar_index)
            time_cd = abs(pD.bar_index - pC.bar_index)
            sym_ratio = (time_cd / time_ab) if time_ab > 0 else 1.0
            
            ratios_dict = {'BC_AB': bc_ab, 'CD_BC': cd_bc, 'CD_AB': cd_ab}
            quality = GeometryCalculator.compute_quality_score(PatternType.ABCD, ratios_dict, prz_width_pips, sym_ratio)
            
            pat_id = f"{symbol}_{timeframe}_ABCD_{direction.value}_{pA.occurrence_time.strftime('%Y%m%d%H%M')}_{pD.occurrence_time.strftime('%Y%m%d%H%M')}"
            
            # Research Trade Levels
            ad_dist = abs(pD.price - pA.price)
            sl_price = pD.price - (15.0 * pip_size) if direction == Direction.BULLISH else pD.price + (15.0 * pip_size)
            tp1_price = pD.price + (0.382 * ad_dist) if direction == Direction.BULLISH else pD.price - (0.382 * ad_dist)
            tp2_price = pD.price + (0.618 * ad_dist) if direction == Direction.BULLISH else pD.price - (0.618 * ad_dist)
            
            state = PatternState.COMPLETED if is_valid else PatternState.INVALIDATED
            
            patterns.append({
                'pattern_id': pat_id,
                'symbol': symbol,
                'timeframe': timeframe,
                'pattern_type': PatternType.ABCD.value,
                'direction': direction.value,
                'state': state.value,
                'quality_score': quality,
                'is_accepted': is_valid,
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
            
        # 2. Detect FORMING & POTENTIAL_D AB=CD (from last 3 pivots A, B, C)
        if n_pivots >= 3:
            pA, pB, pC = pivots[-3], pivots[-2], pivots[-1]
            if pA.is_high and not pB.is_high and pC.is_high:
                direction = Direction.BULLISH
                is_struct = (pA.price > pC.price)
            elif not pA.is_high and pB.is_high and not pC.is_high:
                direction = Direction.BEARISH
                is_struct = (pA.price < pC.price)
            else:
                is_struct = False
                
            if is_struct:
                bc_ab = GeometryCalculator.calc_ratio(pB.price, pC.price, pA.price, pB.price)
                if self.bc_ab_min - 0.05 <= bc_ab <= self.bc_ab_max + 0.05:
                    prz = PRZCalculator.calculate_abcd_prz(pA.price, pB.price, pC.price, direction.value)
                    prz_width_pips = abs(prz['prz_high'] - prz['prz_low']) / pip_size
                    
                    # Check if price is approaching or inside PRZ (POTENTIAL_D vs FORMING)
                    dist_to_prz = min(abs(current_price - prz['prz_low']), abs(current_price - prz['prz_high'])) / pip_size
                    state = PatternState.POTENTIAL_D if dist_to_prz <= 30.0 else PatternState.FORMING
                    
                    pat_id = f"{symbol}_{timeframe}_ABCD_{direction.value}_FORMING_{pA.occurrence_time.strftime('%Y%m%d%H%M')}_{pC.occurrence_time.strftime('%Y%m%d%H%M')}"
                    
                    proj_d = prz['prz_mid']
                    ad_dist = abs(proj_d - pA.price)
                    sl_price = proj_d - (15.0 * pip_size) if direction == Direction.BULLISH else proj_d + (15.0 * pip_size)
                    tp1_price = proj_d + (0.382 * ad_dist) if direction == Direction.BULLISH else proj_d - (0.382 * ad_dist)
                    tp2_price = proj_d + (0.618 * ad_dist) if direction == Direction.BULLISH else proj_d - (0.618 * ad_dist)
                    
                    patterns.append({
                        'pattern_id': pat_id,
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'pattern_type': PatternType.ABCD.value,
                        'direction': direction.value,
                        'state': state.value,
                        'quality_score': 75 if state == PatternState.POTENTIAL_D else 65,
                        'is_accepted': False,
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
                        'ratios': {'BC_AB': bc_ab, 'CD_AB_proj': 1.0},
                        'entry_zone': (prz['prz_low'], prz['prz_high']),
                        'structural_stop': sl_price,
                        'target_1': tp1_price,
                        'target_2': tp2_price
                    })
                    
        return patterns
