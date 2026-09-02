import unittest
from harmonic.states import PatternType
from harmonic.geometry import GeometryCalculator

class TestGeometry(unittest.TestCase):
    def test_quality_scoring(self):
        ratios_perfect = {'BC_AB': 0.618, 'CD_AB': 1.000}
        q_perf = GeometryCalculator.compute_quality_score(PatternType.ABCD, ratios_perfect, prz_width_pips=5.0, time_symmetry_ratio=1.0)
        self.assertGreaterEqual(q_perf, 90)

        ratios_distorted = {'BC_AB': 0.300, 'CD_AB': 1.250}
        q_dist = GeometryCalculator.compute_quality_score(PatternType.ABCD, ratios_distorted, prz_width_pips=40.0, time_symmetry_ratio=2.5)
        self.assertLess(q_dist, 60)

if __name__ == '__main__':
    unittest.main()
