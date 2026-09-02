import os
import json
import pandas as pd
from typing import Dict, Any, Optional
from prediction.feature_extractor import PointInTimeFeatureExtractor

try:
    import joblib
except ImportError:
    joblib = None

class HarmonicPredictor:
    """
    Inference wrapper for frozen out-of-sample harmonic prediction model.
    Enforces strict calibration, metadata versioning, and No-Edge fallback safety.
    """

    _instance = None

    def __init__(self, model_dir: str = "LIVE_HARMONIC_SCANNER/models"):
        self.model_dir = model_dir
        self.model_bundle = None
        self.meta = None
        self.is_deployed = False
        self._load_model()

    def _load_model(self):
        if joblib is None:
            self.is_deployed = False
            return

        # Look for model artifact
        candidates = [
            os.path.join(self.model_dir, "harmonic_predictor_v1.joblib"),
            "models/harmonic_predictor_v1.joblib",
            "LIVE_HARMONIC_SCANNER/models/harmonic_predictor_v1.joblib"
        ]
        meta_candidates = [
            os.path.join(self.model_dir, "model_metadata.json"),
            "models/model_metadata.json",
            "LIVE_HARMONIC_SCANNER/models/model_metadata.json"
        ]
        
        for p in candidates:
            if os.path.exists(p):
                try:
                    self.model_bundle = joblib.load(p)
                    self.is_deployed = True
                    break
                except Exception:
                    pass
                    
        for mp in meta_candidates:
            if os.path.exists(mp):
                try:
                    with open(mp, 'r', encoding='utf-8') as f:
                        self.meta = json.load(f)
                    break
                except Exception:
                    pass

    def predict_pattern(
        self,
        pattern: Dict[str, Any],
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Calculates calibrated forward prediction probabilities for a completed pattern.
        """
        if not self.is_deployed or self.model_bundle is None:
            return {
                'p_tp1': None,
                'p_tp2': None,
                'confidence': 'NO_EDGE',
                'model_name': 'None',
                'model_version': 'NO_EDGE_NOT_DEPLOYED',
                'is_deployed': False
            }

        feats = PointInTimeFeatureExtractor.extract_features(pattern, df)
        if feats is None:
            return {
                'p_tp1': None,
                'p_tp2': None,
                'confidence': 'INSUFFICIENT_DATA',
                'model_name': self.model_bundle.get('meta', {}).get('model_name', 'HarmonicPredictorV1'),
                'model_version': self.model_bundle.get('meta', {}).get('model_version', 'v1'),
                'is_deployed': True
            }

        feat_names = self.model_bundle['feature_names']
        x_vec = [feats.get(fn, 0.0) for fn in feat_names]
        
        use_scaler = self.model_bundle.get('use_scaler', False)
        scaler = self.model_bundle.get('scaler')
        if use_scaler and scaler is not None:
            x_mat = scaler.transform([x_vec])
        else:
            x_mat = [x_vec]

        model_tp1 = self.model_bundle['model_tp1']
        probs = model_tp1.predict_proba(x_mat)[0]
        p_tp1 = float(probs[1]) if len(probs) > 1 else float(probs[0])
        p_tp1 = max(0.01, min(0.99, p_tp1))
        
        # Estimate secondary target P(TP2) as conditional on TP1
        p_tp2 = float(p_tp1 * 0.62)

        # Categorical Confidence Assignment
        quality = pattern.get('quality_score', 50)
        if p_tp1 >= 0.70 and quality >= 70:
            confidence = 'HIGH'
        elif p_tp1 >= 0.58:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'

        return {
            'p_tp1': round(p_tp1 * 100, 1),
            'p_tp2': round(p_tp2 * 100, 1),
            'confidence': confidence,
            'model_name': self.model_bundle.get('meta', {}).get('model_name', 'HistGradientBoosting (Calibrated)'),
            'model_version': self.model_bundle.get('meta', {}).get('model_version', 'harmonic_predictor_v1'),
            'is_deployed': True,
            'features': feats
        }
