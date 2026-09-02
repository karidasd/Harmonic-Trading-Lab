import time
import uuid
import pandas as pd
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from harmonic.detector import HarmonicDetector
from harmonic.states import PatternState
from prediction.predictor import HarmonicPredictor
from prediction.outcome_tracker import OutcomeTracker

class PatternEvent:
    def __init__(
        self,
        event_id: str,
        pattern_id: str,
        symbol: str,
        timeframe: str,
        pattern_type: str,
        direction: str,
        state: str,
        geometry_quality: int,
        prz_low: float,
        prz_high: float,
        d_price: float,
        d_confirmation_time: Optional[pd.Timestamp],
        signal_available_time: Optional[pd.Timestamp],
        detected_at: datetime
    ):
        self.event_id = event_id
        self.pattern_id = pattern_id
        self.symbol = symbol
        self.timeframe = timeframe
        self.pattern_type = pattern_type
        self.direction = direction
        self.state = state
        self.geometry_quality = geometry_quality
        self.prz_low = prz_low
        self.prz_high = prz_high
        self.d_price = d_price
        self.d_confirmation_time = d_confirmation_time
        self.signal_available_time = signal_available_time
        self.detected_at = detected_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'pattern_id': self.pattern_id,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'pattern_type': self.pattern_type,
            'direction': self.direction,
            'state': self.state,
            'geometry_quality': self.geometry_quality,
            'prz_low': self.prz_low,
            'prz_high': self.prz_high,
            'd_price': self.d_price,
            'd_confirmation_time': str(self.d_confirmation_time) if self.d_confirmation_time else None,
            'signal_available_time': str(self.signal_available_time) if self.signal_available_time else None,
            'detected_at': self.detected_at.isoformat()
        }

class LiveHarmonicScanner:
    def __init__(self, data_provider):
        self.data_provider = data_provider
        self.detector = HarmonicDetector(left_bars=5, right_bars=5, min_leg_bars=3)
        self.predictor = HarmonicPredictor()
        self.seen_pattern_ids = set() # Session pattern tracking
        self.seen_event_keys = set() # (pattern_id, state)

    def scan_market(
        self,
        symbols: List[str],
        timeframes: List[str]
    ) -> Dict[str, Any]:
        t0_total = time.time()
        fetch_time = 0.0
        detect_time = 0.0
        
        all_patterns = []
        new_events = []
        new_patterns_count = 0
        markets_scanned = 0
        now_utc = datetime.now(timezone.utc)
        
        for sym in symbols:
            for tf in timeframes:
                try:
                    # 1. Measure Data Fetch Latency
                    t0_f = time.time()
                    df = self.data_provider.get_ohlcv(sym, tf, bars=300)
                    fetch_time += (time.time() - t0_f)
                    
                    if df is None or df.empty or len(df) < 30:
                        continue
                    markets_scanned += 1
                    
                    # 2. Measure Pure Detection Latency
                    t0_d = time.time()
                    pats = self.detector.scan_dataframe(df, sym, tf)
                    detect_time += (time.time() - t0_d)
                    
                    for p in pats:
                        pid = p['pattern_id']
                        is_new = pid not in self.seen_pattern_ids
                        if is_new:
                            self.seen_pattern_ids.add(pid)
                            new_patterns_count += 1
                        p['is_new_in_session'] = is_new
                        
                        # 3. Apply Prediction & Outcome Layer for Completed Patterns
                        if p.get('state') == 'COMPLETED':
                            pred_res = self.predictor.predict_pattern(p, df)
                            p['p_tp1'] = pred_res.get('p_tp1')
                            p['p_tp2'] = pred_res.get('p_tp2')
                            p['confidence'] = pred_res.get('confidence', 'NO_EDGE')
                            p['model_name'] = pred_res.get('model_name', 'None')
                            p['model_version'] = pred_res.get('model_version', 'NO_EDGE_NOT_DEPLOYED')
                            
                            # Outcome tracking on forward bars
                            outcome = OutcomeTracker.evaluate_outcome(p, df)
                            p['forward_status'] = outcome.get('status', 'ACTIVE')
                            p['outcome_eval'] = outcome
                        else:
                            p['p_tp1'] = None
                            p['p_tp2'] = None
                            p['confidence'] = 'N/A'
                            p['model_name'] = 'None'
                            p['model_version'] = 'None'
                            p['forward_status'] = p.get('state')
                            
                        all_patterns.append(p)
                        
                        # Deduplicated Event Generation
                        event_key = (p['pattern_id'], p['state'])
                        if event_key not in self.seen_event_keys:
                            self.seen_event_keys.add(event_key)
                            ev = PatternEvent(
                                event_id=str(uuid.uuid4()),
                                pattern_id=p['pattern_id'],
                                symbol=p['symbol'],
                                timeframe=p['timeframe'],
                                pattern_type=p['pattern_type'],
                                direction=p['direction'],
                                state=p['state'],
                                geometry_quality=p['quality_score'],
                                prz_low=p['prz_low'],
                                prz_high=p['prz_high'],
                                d_price=p['D_price'],
                                d_confirmation_time=p['D_confirmation_time'],
                                signal_available_time=p['signal_available_time'],
                                detected_at=now_utc
                            )
                            new_events.append(ev)
                except Exception:
                    pass
                    
        total_time = time.time() - t0_total
        
        # Sort patterns: COMPLETED first, then POTENTIAL_D, then FORMING; within group by quality desc
        state_order = {PatternState.COMPLETED.value: 0, PatternState.POTENTIAL_D.value: 1, PatternState.FORMING.value: 2, PatternState.INVALIDATED.value: 3}
        all_patterns.sort(key=lambda x: (state_order.get(x['state'], 99), -x['quality_score']))
        
        return {
            'patterns': all_patterns,
            'events': new_events,
            'new_patterns_count': new_patterns_count,
            'markets_scanned': markets_scanned,
            'data_fetch_latency_sec': round(fetch_time, 3),
            'detection_latency_sec': round(detect_time, 3),
            'scan_duration_sec': round(total_time, 3),
            'timestamp': now_utc
        }
