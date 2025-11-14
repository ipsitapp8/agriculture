import time
import requests
from config import CACHE_TTL_SOIL

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

def _classify_texture(sand, silt, clay):
    if sand >= 70 and clay <= 20:
        return "sandy"
    if sand >= 50 and clay <= 25:
        return "sandy loam"
    if 20 <= clay <= 35 and 30 <= silt <= 50:
        return "clay loam"
    if 20 <= clay <= 30 and 30 <= sand <= 50:
        return "loam"
    return "loam"

def _fallback(lat, lon):
    sand = 45
    silt = 30
    clay = 25
    ph = 6.4
    soc = 1.2
    return {
        "lat": lat,
        "lon": lon,
        "ph": ph,
        "soc_pct": soc,
        "sand_pct": sand,
        "silt_pct": silt,
        "clay_pct": clay,
        "texture": _classify_texture(sand, silt, clay)
    }

def get_soil(lat, lon):
    key = f"soil:{lat:.4f},{lon:.4f}"
    cached = _cache_get(key)
    if cached:
        return cached
    try:
        url = "https://rest.isric.org/soilgrids/v2.1/properties/query"
        params = {
            "lat": lat,
            "lon": lon,
            "property": ["phh2o", "soc", "sand", "silt", "clay"],
            "depth": "0-5cm",
            "value": "mean"
        }
        r = _http_get_with_retry(url, params, timeout=20)
        j = r.json()
        props = {p["name"]: p["mean"] for p in j.get("properties", [])}
        ph = float(props.get("phh2o", 6.5))
        soc = float(props.get("soc", 1.0))
        sand = float(props.get("sand", 40))
        silt = float(props.get("silt", 30))
        clay = float(props.get("clay", 30))
        data = {
            "lat": lat,
            "lon": lon,
            "ph": ph,
            "soc_pct": soc,
            "sand_pct": sand,
            "silt_pct": silt,
            "clay_pct": clay,
            "texture": _classify_texture(sand, silt, clay)
        }
        _cache_set(key, data, CACHE_TTL_SOIL)
        return data
    except Exception:
        data = _fallback(lat, lon)
        _cache_set(key, data, CACHE_TTL_SOIL)
        return data
