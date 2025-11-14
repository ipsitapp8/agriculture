import unittest
from services.recommender import _score_linear, _texture_score, recommend_for_location, CROPS, month_statuses

class TestRecommender(unittest.TestCase):
    def test_score_linear(self):
        self.assertEqual(_score_linear(25, 20, 30, 10, 40, 100), 100)
        self.assertAlmostEqual(_score_linear(15, 20, 30, 10, 40, 100), 50)
        self.assertEqual(_score_linear(5, 20, 30, 10, 40, 100), 0)

    def test_texture_score(self):
        self.assertGreater(_texture_score('loam', {'loam'}, 10), 0)
        self.assertEqual(_texture_score('sand', {'loam'}, 10), 0)

    def test_recommend_sorting(self):
        weather = {"daily": [{"temp": {"day": 26}, "rain": 10} for _ in range(7)]}
        soil = {"ph": 6.5, "soc_pct": 1.5, "texture": "loam"}
        res = recommend_for_location(weather, soil)
        recs = res["recommendations"]
        self.assertTrue(len(recs) > 0)
        self.assertGreaterEqual(recs[0]["score"], recs[-1]["score"])

    def test_month_statuses(self):
        weather = {
            "daily": [{"temp": {"day": 26}, "rain": 10} for _ in range(7)],
            "climatology": {"monthly": [{"month": i, "temp": 25, "rain": 80} for i in range(1,13)]}
        }
        soil = {"ph": 6.5, "soc_pct": 1.5, "texture": "loam"}
        res = month_statuses(weather, soil)
        self.assertEqual(len(res["months"]), 12)
        self.assertEqual(len(res["climatology_months"]), 12)

if __name__ == '__main__':
    unittest.main()