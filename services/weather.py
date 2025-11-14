import time
import requests
from config import CACHE_TTL_WEATHER

_cache = {}

def _cache_get(key):
    item = _cache.get(key)
    if not item:
        return None
    exp, val = item
    if exp < time.time():
        _cache.pop(key, None)
        return None
    return val

def _cache_set(key, val, ttl):
    _cache[key] = (time.time() + ttl, val)

def _http_get_with_retry(url, params, timeout=20, retries=2, backoff=0.5):
    last = None
    for i in range(retries + 1):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            return r
        except Exception as e:
            last = e
            if i < retries:
                time.sleep(backoff * (2 ** i))
    raise last

def _get_climatology(lat, lon):
    """Fetch climatology data from Open-Meteo API, with fallback to default values."""
    key = f"climatology:{lat:.4f},{lon:.4f}"
    cached = _cache_get(key)
    if cached:
        return cached
    
    try:
        url = "https://climate-api.open-meteo.com/v1/climate"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": "1991-01-01",
            "end_date": "2020-12-31",
            "models": "EC_Earth3_Veg",
            "daily": "temperature_2m_mean,precipitation_sum",
            "timezone": "auto"
        }
        r = _http_get_with_retry(url, params, timeout=20)
        if r.status_code == 200:
            j = r.json()
            daily = j.get("daily", {})
            temps = daily.get("temperature_2m_mean", [])
            rains = daily.get("precipitation_sum", [])
            dates = daily.get("time", [])
            
            # Group by month and calculate averages
            monthly_data = {}
            for i, date_str in enumerate(dates):
                if i < len(temps) and i < len(rains):
                    try:
                        month = int(date_str.split("-")[1])
                        if month not in monthly_data:
                            monthly_data[month] = {"temps": [], "rains": []}
                        monthly_data[month]["temps"].append(float(temps[i] or 0))
                        monthly_data[month]["rains"].append(float(rains[i] or 0))
                    except (ValueError, IndexError):
                        continue
            
            # Calculate monthly averages
            monthly = []
            for month in range(1, 13):
                if month in monthly_data:
                    avg_temp = sum(monthly_data[month]["temps"]) / len(monthly_data[month]["temps"])
                    avg_rain = sum(monthly_data[month]["rains"]) / len(monthly_data[month]["rains"])
                    monthly.append({"month": month, "temp": round(avg_temp, 1), "rain": round(avg_rain, 1)})
                else:
                    # Fallback for missing months
                    monthly.append({"month": month, "temp": 20, "rain": 50})
            
            if len(monthly) == 12:
                result = {"monthly": monthly}
                _cache_set(key, result, 86400 * 7)  # Cache for 7 days
                return result
    except Exception:
        pass
    
    # Fallback climatology data
    fallback = {
        "monthly": [
            {"month": 1, "temp": 18, "rain": 25},
            {"month": 2, "temp": 20, "rain": 30},
            {"month": 3, "temp": 24, "rain": 35},
            {"month": 4, "temp": 28, "rain": 45},
            {"month": 5, "temp": 32, "rain": 60},
            {"month": 6, "temp": 34, "rain": 80},
            {"month": 7, "temp": 33, "rain": 90},
            {"month": 8, "temp": 32, "rain": 85},
            {"month": 9, "temp": 30, "rain": 70},
            {"month": 10, "temp": 26, "rain": 50},
            {"month": 11, "temp": 22, "rain": 35},
            {"month": 12, "temp": 19, "rain": 28}
        ]
    }
    _cache_set(key, fallback, 86400)  # Cache fallback for 1 day
    return fallback

def geocode_location(query):
    if not query:
        return {"results": []}
    key = f"geo:{query}"
    cached = _cache_get(key)
    if cached:
        return cached
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": query, "count": 5, "language": "en", "format": "json"}
    try:
        r = _http_get_with_retry(url, params, timeout=15)
        if r.status_code != 200:
            raise RuntimeError(f"geocode status {r.status_code}")
        data = r.json().get("results", [])
        res = {"results": [{"name": x.get("name"), "lat": x.get("latitude"), "lon": x.get("longitude")} for x in data]}
    except Exception:
        res = {"results": [{"name": "Sample", "lat": 28.6139, "lon": 77.2090}]}
    _cache_set(key, res, 3600)
    return res

def get_weather(lat, lon):
    key = f"weather:{lat:.4f},{lon:.4f}"
    cached = _cache_get(key)
    if cached:
        return cached
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": "auto",
        "current": "temperature_2m,relative_humidity_2m,rain,wind_speed_10m",
        "daily": "temperature_2m_mean,precipitation_sum"
    }
    try:
        r = _http_get_with_retry(url, params, timeout=20)
        if r.status_code != 200:
            raise RuntimeError(f"forecast status {r.status_code}")
        j = r.json()
        cur = j.get("current", {})
        d = j.get("daily", {})
        temps = d.get("temperature_2m_mean", [])
        rains = d.get("precipitation_sum", [])
        days = []
        for i in range(min(len(temps), len(rains))):
            days.append({"dt": i, "temp": {"day": float(temps[i] or 0)}, "rain": float(rains[i] or 0)})
        data = {
            "lat": lat,
            "lon": lon,
            "current": {
                "temp": float(cur.get("temperature_2m", 0) or 0),
                "humidity": float(cur.get("relative_humidity_2m", 0) or 0),
                "wind_speed": float(cur.get("wind_speed_10m", 0) or 0),
                "rain": {"1h": float(cur.get("rain", 0) or 0)}
            },
            "daily": days
        }
    except Exception:
        data = {
            "lat": lat,
            "lon": lon,
            "current": {"temp": 26, "humidity": 60, "wind_speed": 3.2, "rain": {"1h": 0}},
            "daily": [
                {"dt": 0, "temp": {"day": 26}, "rain": 5},
                {"dt": 1, "temp": {"day": 27}, "rain": 12},
                {"dt": 2, "temp": {"day": 25}, "rain": 8},
                {"dt": 3, "temp": {"day": 24}, "rain": 2},
                {"dt": 4, "temp": {"day": 26}, "rain": 15},
                {"dt": 5, "temp": {"day": 28}, "rain": 0},
                {"dt": 6, "temp": {"day": 27}, "rain": 10}
            ]
        }
    # Try to fetch climatology data
    if "climatology" not in data:
        climatology = _get_climatology(lat, lon)
        data["climatology"] = climatology
    _cache_set(key, data, CACHE_TTL_WEATHER)
    return data
