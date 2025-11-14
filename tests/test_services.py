import unittest
from services.weather import get_weather
from services.soil import get_soil

class TestServices(unittest.TestCase):
    def test_weather_fallback(self):
        w = get_weather(28.6139, 77.2090)
        self.assertIn("current", w)
        self.assertIn("daily", w)
        self.assertIn("climatology", w)

    def test_soil_fallback(self):
        s = get_soil(28.6139, 77.2090)
        self.assertIn("ph", s)
        self.assertIn("soc_pct", s)
        self.assertIn("texture", s)

if __name__ == '__main__':
    unittest.main()