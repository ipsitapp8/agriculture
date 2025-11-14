def _avg_daily_rain_mm(daily):
    values = []
    for d in daily:
        v = d.get("rain", 0)
        if isinstance(v, dict):
            v = v.get("1h", 0)
        values.append(float(v or 0))
    if not values:
        return 0.0
    return sum(values) / len(values)

def _avg_daily_temp_c(daily):
    values = []
    for d in daily:
        t = d.get("temp", {})
        if isinstance(t, dict):
            values.append(float(t.get("day", t.get("min", 0))))
        else:
            values.append(float(t or 0))
    if not values:
        return 0.0
    return sum(values) / len(values)

def _score_linear(x, min_ideal, max_ideal, min_acc, max_acc, weight):
    if min_ideal <= x <= max_ideal:
        return weight
    if min_acc <= x < min_ideal:
        return weight * (x - min_acc) / (min_ideal - min_acc)
    if max_ideal < x <= max_acc:
        return weight * (max_acc - x) / (max_acc - max_ideal)
    return 0.0

def _texture_score(tex, allowed, weight):
    if tex in allowed:
        return weight
    sim = {
        "loam": {"sandy loam", "silt loam", "clay loam"},
        "sandy loam": {"loam", "sandy"},
        "clay loam": {"loam", "clay"}
    }
    for a in allowed:
        if tex in sim.get(a, set()):
            return weight * 0.5
    return 0.0

CROPS = [
    {
        "name": "Rice",
        "rain": (150, 400, 100, 500),
        "temp": (20, 30, 15, 34),
        "ph": (5.0, 6.5, 4.5, 7.5),
        "soc": (1.0, 2.5, 0.6, 2.5),
        "textures": {"clay", "silty clay", "clay loam"},
        "metadata": {"growth_cycle_days": 120, "water_mm": 900, "category": "cereal", "family": "Poaceae", "planting_months": [3,4,5,6,7]}
    },
    {
        "name": "Wheat",
        "rain": (50, 120, 30, 150),
        "temp": (10, 25, 5, 30),
        "ph": (6.0, 7.5, 5.5, 8.0),
        "soc": (0.6, 2.0, 0.4, 2.0),
        "textures": {"loam", "sandy loam"},
        "metadata": {"growth_cycle_days": 140, "water_mm": 450, "category": "cereal", "family": "Poaceae", "planting_months": [10,11,12]}
    },
    {
        "name": "Maize",
        "rain": (80, 150, 50, 200),
        "temp": (18, 30, 12, 34),
        "ph": (5.5, 7.5, 5.0, 8.0),
        "soc": (0.8, 2.0, 0.5, 2.0),
        "textures": {"loam", "silt loam"},
        "metadata": {"growth_cycle_days": 110, "water_mm": 550, "category": "cereal", "family": "Poaceae", "planting_months": [3,4,5,6]}
    },
    {
        "name": "Soybean",
        "rain": (60, 120, 40, 160),
        "temp": (20, 30, 15, 33),
        "ph": (6.0, 7.0, 5.5, 7.5),
        "soc": (1.0, 2.5, 0.6, 2.5),
        "textures": {"loam", "sandy loam"},
        "metadata": {"growth_cycle_days": 100, "water_mm": 400, "category": "legume", "family": "Fabaceae", "planting_months": [4,5,6,7]}
    },
    {
        "name": "Potato",
        "rain": (40, 100, 30, 150),
        "temp": (15, 20, 8, 22),
        "ph": (5.5, 6.5, 5.0, 7.0),
        "soc": (1.0, 3.0, 0.7, 3.0),
        "textures": {"sandy loam", "silt loam"},
        "metadata": {"growth_cycle_days": 90, "water_mm": 500, "category": "tuber", "family": "Solanaceae", "planting_months": [1,2,3,9,10,11]}
    },
    {
        "name": "Cotton",
        "rain": (50, 150, 30, 200),
        "temp": (20, 35, 16, 38),
        "ph": (5.8, 8.0, 5.5, 8.5),
        "soc": (0.6, 2.0, 0.3, 2.0),
        "textures": {"sandy loam", "loam"},
        "metadata": {"growth_cycle_days": 180, "water_mm": 700, "category": "fiber", "family": "Malvaceae", "planting_months": [4,5]}
    },
    {
        "name": "Tomato",
        "rain": (40, 80, 30, 120),
        "temp": (18, 28, 12, 32),
        "ph": (5.5, 6.8, 5.0, 7.5),
        "soc": (0.8, 2.5, 0.5, 2.5),
        "textures": {"loam"},
        "metadata": {"growth_cycle_days": 75, "water_mm": 400, "category": "vegetable", "family": "Solanaceae", "planting_months": [1,2,3,7,8,9,10,11,12]}
    },
    {
        "name": "Carrot",
        "rain": (30, 70, 20, 100),
        "temp": (12, 24, 8, 28),
        "ph": (6.0, 7.0, 5.5, 7.5),
        "soc": (0.6, 2.5, 0.4, 2.5),
        "textures": {"sandy loam", "loam"},
        "metadata": {"growth_cycle_days": 80, "water_mm": 300, "category": "root", "family": "Apiaceae", "planting_months": [2,3,8,9,10]}
    },
    {
        "name": "Onion",
        "rain": (30, 70, 20, 120),
        "temp": (12, 24, 8, 28),
        "ph": (6.0, 7.0, 5.5, 7.5),
        "soc": (0.6, 2.5, 0.3, 2.5),
        "textures": {"sandy loam"},
        "metadata": {"growth_cycle_days": 120, "water_mm": 350, "category": "bulb", "family": "Amaryllidaceae", "planting_months": [1,2,3,9,10,11]}
    },
    {
        "name": "Cabbage",
        "rain": (40, 90, 30, 130),
        "temp": (10, 22, 6, 26),
        "ph": (6.0, 7.5, 5.5, 8.0),
        "soc": (0.8, 2.5, 0.5, 2.5),
        "textures": {"loam", "sandy loam"},
        "metadata": {"growth_cycle_days": 90, "water_mm": 400, "category": "leafy", "family": "Brassicaceae", "planting_months": [2,3,8,9]}
    },
    {
        "name": "Lettuce",
        "rain": (30, 60, 20, 90),
        "temp": (10, 20, 6, 24),
        "ph": (6.0, 7.0, 5.5, 7.5),
        "soc": (0.6, 2.5, 0.4, 2.5),
        "textures": {"loam", "sandy loam"},
        "metadata": {"growth_cycle_days": 45, "water_mm": 250, "category": "leafy", "family": "Asteraceae", "planting_months": [2,3,4,8,9,10,11]}
    },
    {
        "name": "Spinach",
        "rain": (30, 60, 20, 90),
        "temp": (8, 18, 4, 22),
        "ph": (6.0, 7.0, 5.5, 7.5),
        "soc": (0.6, 2.5, 0.4, 2.5),
        "textures": {"loam", "sandy loam"},
        "metadata": {"growth_cycle_days": 40, "water_mm": 200, "category": "leafy", "family": "Amaranthaceae", "planting_months": [2,3,8,9,10,11]}
    },
    {
        "name": "Chickpea",
        "rain": (20, 60, 10, 90),
        "temp": (12, 28, 6, 32),
        "ph": (6.0, 8.0, 5.5, 8.5),
        "soc": (0.4, 2.0, 0.2, 2.0),
        "textures": {"loam", "sandy loam"},
        "metadata": {"growth_cycle_days": 100, "water_mm": 300, "category": "legume", "family": "Fabaceae", "planting_months": [10,11,12,1,2]}
    },
    {
        "name": "Lentil",
        "rain": (20, 50, 10, 80),
        "temp": (8, 24, 4, 28),
        "ph": (6.0, 7.5, 5.5, 8.0),
        "soc": (0.3, 2.0, 0.2, 2.0),
        "textures": {"loam"},
        "metadata": {"growth_cycle_days": 90, "water_mm": 250, "category": "legume", "family": "Fabaceae", "planting_months": [10,11,12,1,2]}
    },
    {
        "name": "Sunflower",
        "rain": (40, 90, 30, 140),
        "temp": (20, 30, 15, 35),
        "ph": (6.0, 7.5, 5.5, 8.0),
        "soc": (0.6, 2.0, 0.3, 2.0),
        "textures": {"loam", "sandy loam"},
        "metadata": {"growth_cycle_days": 100, "water_mm": 400, "category": "oilseed", "family": "Asteraceae", "planting_months": [4,5,6,7]}
    },
    {
        "name": "Groundnut",
        "rain": (50, 120, 30, 160),
        "temp": (20, 32, 16, 35),
        "ph": (5.5, 6.5, 5.0, 7.0),
        "soc": (0.8, 2.5, 0.5, 2.5),
        "textures": {"sandy", "sandy loam"},
        "metadata": {"growth_cycle_days": 120, "water_mm": 500, "category": "legume", "family": "Fabaceae", "planting_months": [4,5,6]}
    },
    {
        "name": "Mustard",
        "rain": (30, 70, 20, 110),
        "temp": (12, 25, 8, 28),
        "ph": (6.0, 7.8, 5.5, 8.5),
        "soc": (0.4, 2.0, 0.2, 2.0),
        "textures": {"loam", "sandy loam"},
        "metadata": {"growth_cycle_days": 90, "water_mm": 300, "category": "oilseed", "family": "Brassicaceae", "planting_months": [10,11,12,1]}
    },
    {
        "name": "Rapeseed",
        "rain": (40, 90, 30, 130),
        "temp": (10, 22, 6, 26),
        "ph": (6.0, 7.5, 5.5, 8.0),
        "soc": (0.6, 2.0, 0.3, 2.0),
        "textures": {"loam"},
        "metadata": {"growth_cycle_days": 120, "water_mm": 350, "category": "oilseed", "family": "Brassicaceae", "planting_months": [10,11,12,1]}
    },
    {
        "name": "Sugarcane",
        "rain": (100, 300, 80, 400),
        "temp": (22, 34, 18, 36),
        "ph": (5.5, 7.5, 5.0, 8.0),
        "soc": (1.2, 3.0, 0.8, 3.0),
        "textures": {"clay loam", "silt loam"},
        "metadata": {"growth_cycle_days": 300, "water_mm": 1500, "category": "cash", "family": "Poaceae", "planting_months": [2,3,4]}
    },
    {
        "name": "Sorghum",
        "rain": (40, 100, 20, 150),
        "temp": (20, 35, 15, 38),
        "ph": (5.5, 7.5, 5.0, 8.0),
        "soc": (0.5, 2.0, 0.3, 2.0),
        "textures": {"sandy loam", "loam"},
        "metadata": {"growth_cycle_days": 110, "water_mm": 400, "category": "cereal", "family": "Poaceae", "planting_months": [6,7,8]}
    },
    {
        "name": "Pearl Millet",
        "rain": (20, 80, 10, 120),
        "temp": (25, 38, 18, 40),
        "ph": (5.5, 7.8, 5.0, 8.5),
        "soc": (0.4, 2.0, 0.2, 2.0),
        "textures": {"sandy", "sandy loam"},
        "metadata": {"growth_cycle_days": 80, "water_mm": 250, "category": "cereal", "family": "Poaceae", "planting_months": [6,7,8]}
    },
    {
        "name": "Barley",
        "rain": (40, 90, 20, 120),
        "temp": (8, 24, 4, 28),
        "ph": (6.0, 7.5, 5.5, 8.0),
        "soc": (0.5, 2.0, 0.3, 2.0),
        "textures": {"loam", "sandy loam"},
        "metadata": {"growth_cycle_days": 120, "water_mm": 400, "category": "cereal", "family": "Poaceae", "planting_months": [10,11,12,1]}
    },
    {
        "name": "Oats",
        "rain": (60, 120, 40, 160),
        "temp": (10, 22, 6, 26),
        "ph": (6.0, 7.0, 5.5, 7.5),
        "soc": (0.8, 2.0, 0.5, 2.0),
        "textures": {"loam"},
        "metadata": {"growth_cycle_days": 110, "water_mm": 450, "category": "cereal", "family": "Poaceae", "planting_months": [2,3,9,10]}
    },
    {
        "name": "Tea",
        "rain": (150, 400, 120, 500),
        "temp": (15, 25, 10, 28),
        "ph": (4.5, 5.5, 4.0, 6.0),
        "soc": (1.5, 3.5, 1.0, 3.5),
        "textures": {"silty", "clay loam"},
        "metadata": {"growth_cycle_days": 365, "water_mm": 1200, "category": "cash", "family": "Theaceae", "planting_months": [6,7,8]}
    }
]

WEIGHTS = {"rain": 35, "temp": 25, "ph": 15, "soc": 15, "texture": 10}

def _status(score):
    if score >= 75:
        return "green"
    if score >= 50:
        return "yellow"
    return "red"

def _rationale(x, ideal, acc, name):
    mi, ma = ideal
    mai, maa = acc
    return {
        "name": name,
        "value": x,
        "ideal": [mi, ma],
        "acceptable": [mai, maa]
    }

def recommend_for_location(weather, soil):
    daily = weather.get("daily", [])
    rain = _avg_daily_rain_mm(daily)
    temp = _avg_daily_temp_c(daily)
    ph = float(soil.get("ph", 6.5))
    soc = float(soil.get("soc_pct", 1.0))
    tex = soil.get("texture", "loam")
    items = []
    for c in CROPS:
        r = _score_linear(rain, *c["rain"], WEIGHTS["rain"])
        t = _score_linear(temp, *c["temp"], WEIGHTS["temp"])
        p = _score_linear(ph, *c["ph"], WEIGHTS["ph"])
        s = _score_linear(soc, *c["soc"], WEIGHTS["soc"])
        x = _texture_score(tex, c["textures"], WEIGHTS["texture"])
        score = r + t + p + s + x
        items.append({
            "crop": c["name"],
            "score": round(score, 1),
            "status": _status(score),
            "metadata": c.get("metadata", {}),
            "factors": {
                "rain": _rationale(rain, (c["rain"][0], c["rain"][1]), (c["rain"][2], c["rain"][3]), "rain"),
                "temp": _rationale(temp, (c["temp"][0], c["temp"][1]), (c["temp"][2], c["temp"][3]), "temp"),
                "ph": _rationale(ph, (c["ph"][0], c["ph"][1]), (c["ph"][2], c["ph"][3]), "ph"),
                "soc": _rationale(soc, (c["soc"][0], c["soc"][1]), (c["soc"][2], c["soc"][3]), "soc"),
                "texture": {"name": "texture", "value": tex, "allowed": list(c["textures"]) }
            }
        })
    items.sort(key=lambda x: x["score"], reverse=True)
    return {"rainfall_mm": rain, "temp_c": temp, "soil": soil, "recommendations": items}

def month_statuses(weather, soil):
    rec = recommend_for_location(weather, soil)["recommendations"]
    best = rec[0] if rec else None
    months = []
    names = [
        "Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"
    ]
    # Current conditions view
    for i, m in enumerate(names, start=1):
        status = best["status"] if best else "yellow"
        note = best["crop"] if best else ""
        planting_ok = False
        if best and i in best.get("metadata", {}).get("planting_months", []):
            planting_ok = True
            note = f"{note} (planting window)"
        months.append({"month": m, "status": status, "note": note, "planting_ok": planting_ok})
    
    # Climatology view
    climatology_months = []
    climatology = weather.get("climatology", {}).get("monthly", [])
    ph = float(soil.get("ph", 6.5))
    soc = float(soil.get("soc_pct", 1.0))
    tex = soil.get("texture", "loam")
    for i, m in enumerate(names, start=1):
        month_data = next((item for item in climatology if item.get("month") == i), None)
        if month_data:
            tval = float(month_data.get("temp", 0) or 0)
            rval = float(month_data.get("rain", 0) or 0)
            scored = []
            for c in CROPS:
                r = _score_linear(rval, *c["rain"], WEIGHTS["rain"])
                t = _score_linear(tval, *c["temp"], WEIGHTS["temp"])
                p = _score_linear(ph, *c["ph"], WEIGHTS["ph"])
                s = _score_linear(soc, *c["soc"], WEIGHTS["soc"])
                x = _texture_score(tex, c["textures"], WEIGHTS["texture"])
                score = r + t + p + s + x
                scored.append((score, c))
            scored.sort(key=lambda y: y[0], reverse=True)
            top_score, top_crop = scored[0]
            clim_status = _status(top_score)
            clim_note = f"{top_crop['name']} (climate avg)"
            clim_planting_ok = i in top_crop.get("metadata", {}).get("planting_months", [])
        else:
            clim_status = "yellow"
            clim_note = "No climate data"
            clim_planting_ok = False
        climatology_months.append({
            "month": m,
            "status": clim_status,
            "note": clim_note,
            "planting_ok": clim_planting_ok,
            "temp": month_data.get("temp", "N/A") if month_data else "N/A",
            "rain": month_data.get("rain", "N/A") if month_data else "N/A"
        })
    
    return {"months": months, "climatology_months": climatology_months}
