from flask import Blueprint, request, jsonify
from services.weather import get_weather
from services.soil import get_soil
from services.recommender import month_statuses

bp = Blueprint("calendar", __name__)

@bp.get("/api/calendar")
def calendar():
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
        weather = get_weather(latf, lonf)
        soil = get_soil(latf, lonf)
        res = month_statuses(weather, soil)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
