from flask import Blueprint, request, jsonify, Response
import csv
import io
from services.weather import get_weather
from services.soil import get_soil
from services.recommender import recommend_for_location, CROPS

bp = Blueprint("recommend", __name__)

@bp.post("/api/recommend")
def recommend():
    try:
        body = request.get_json(silent=True) or {}
        lat = body.get("lat")
        lon = body.get("lon")
        if lat is None or lon is None:
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
        res = recommend_for_location(weather, soil)
        return jsonify(res)
    except Exception as e:
        return jsonify({"error": "Internal server error", "message": str(e)}), 500

@bp.get("/api/crops")
def crops():
    return jsonify({"crops": [{"name": c["name"], "metadata": c.get("metadata", {})} for c in CROPS]})

@bp.post("/api/export/csv")
def export_csv():
    try:
        body = request.get_json(silent=True) or {}
        recs = body.get("recs", [])
        fields = body.get("fields", [])
        if not isinstance(recs, list) or not isinstance(fields, list) or not recs or not fields:
            return jsonify({"error": "recs and fields required"}), 400
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(fields)
        for r in recs:
            row = [r.get(f, "") for f in fields]
            writer.writerow(row)
        buffer.seek(0)
        return Response(buffer.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=crop_recommendations.csv"})
    except Exception as e:
        return jsonify({"error": "Export failed", "message": str(e)}), 500
