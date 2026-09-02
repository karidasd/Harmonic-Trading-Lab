import json
import os
from typing import Dict, Any

class ResearchDataLoader:
    @staticmethod
    def load_frozen_results(path: str = "LIVE_HARMONIC_SCANNER/research/frozen_results.json") -> Dict[str, Any]:
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
