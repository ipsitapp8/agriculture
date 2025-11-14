import unittest
from app import create_app

class TestRoutes(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_weather_route(self):
        r = self.client.get('/api/weather?lat=28.6139&lon=77.2090')
        self.assertEqual(r.status_code, 200)
        j = r.get_json()
        self.assertIn('current', j)

    def test_soil_route(self):
        r = self.client.get('/api/soil?lat=28.6139&lon=77.2090')
        self.assertEqual(r.status_code, 200)
        j = r.get_json()
        self.assertIn('ph', j)

    def test_recommend_route(self):
        r = self.client.post('/api/recommend', json={'lat':28.6139,'lon':77.2090})
        self.assertEqual(r.status_code, 200)
        j = r.get_json()
        self.assertIn('recommendations', j)

    def test_calendar_route(self):
        r = self.client.get('/api/calendar?lat=28.6139&lon=77.2090')
        self.assertEqual(r.status_code, 200)
        j = r.get_json()
        self.assertIn('months', j)
        self.assertIn('climatology_months', j)

if __name__ == '__main__':
    unittest.main()