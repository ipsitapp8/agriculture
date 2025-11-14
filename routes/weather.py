from flask import Blueprint, request, jsonify
from services.weather import geocode_location, get_weather

bp = Blueprint("weather", __name__)

@bp.get("/api/geocode")
def geocode():
    try:
        q = request.args.get("query", "").strip()
        if not q:
            return jsonify({"results": []})
        res = geocode_location(q)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": "Geocoding failed", "message": str(e), "results": []}), 500

@bp.get("/api/weather")
def weather():
    try:
        lat = request.args.get("lat")
        lon = request.args.get("lon")
        if not lat or not lon:
            return jsonify({"error": "lat and lon required"}), 400
        try:
            latf = float(lat)
            lonf = float(lon)
        except (ValueError, TypeError):
            return jsonify({"error": "invalid coordinates"}), 400
        if not (-90 <= latf <= 90 and -180 <= lonf <= 180):
            return jsonify({"error": "out of range coordinates"}), 400
        data = get_weather(latf, lonf)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500

@bp.get("/api/debug/openweather")
def debug_openweather():
    try:
        from config import OPENWEATHER_API_KEY
        present = bool(OPENWEATHER_API_KEY)
    except Exception:
        present = False
    return jsonify({"key_present": present})
