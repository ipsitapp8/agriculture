from flask import Blueprint, request, jsonify
from services.soil import get_soil

bp = Blueprint("soil", __name__)

@bp.get("/api/soil")
def soil():
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
        data = get_soil(latf, lonf)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500
