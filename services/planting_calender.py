"""
services/planting_calendar.py
Generates a personalised planting and harvesting calendar based on
the farmer's GPS location (Kenya agro-ecological zone) and crops selected.
"""

from datetime import datetime

# Kenya has two main rainy seasons:
# Long Rains (LR): March – May
# Short Rains (SR): October – December
# Some regions (e.g. western Kenya) have a third season.

# Agro-ecological zones based on rough latitude bands within Kenya
def get_zone(lat: float, lon: float) -> str:
    """
    Classifies GPS coordinates into a Kenya farming zone.
    Returns one of: 'highland', 'western', 'coastal', 'arid', 'central'
    """
    if lat < -2.5:  # South Kenya / coastal
        if lon > 39.0:
            return "coastal"
        return "southern"
    elif lat < -1.0:  # Central highlands
        if lon > 36.5 and lon < 38.5:
            return "highland"
        return "central"
    elif lat < 0.5:  # Nairobi / Rift Valley
        if lon < 36.0:
            return "rift_valley"
        return "central"
    elif lat < 1.5:  # Western Kenya
        return "western"
    else:  # Northern / arid
        return "arid"


# Zone-specific season definitions
ZONE_SEASONS = {
    "highland": [
        {"name": "Long Rains", "start_month": 3, "end_month": 5, "plant_start": "March", "harvest_end": "July"},
        {"name": "Short Rains", "start_month": 10, "end_month": 12, "plant_start": "October", "harvest_end": "January"},
    ],
    "central": [
        {"name": "Long Rains", "start_month": 3, "end_month": 5, "plant_start": "March", "harvest_end": "July"},
        {"name": "Short Rains", "start_month": 10, "end_month": 12, "plant_start": "October", "harvest_end": "January"},
    ],
    "western": [
        {"name": "Long Rains", "start_month": 3, "end_month": 8, "plant_start": "February", "harvest_end": "August"},
        {"name": "Short Rains", "start_month": 9, "end_month": 11, "plant_start": "September", "harvest_end": "December"},
    ],
    "coastal": [
        {"name": "Long Rains (Masika)", "start_month": 4, "end_month": 6, "plant_start": "April", "harvest_end": "July"},
        {"name": "Short Rains (Vuli)", "start_month": 10, "end_month": 12, "plant_start": "October", "harvest_end": "January"},
    ],
    "rift_valley": [
        {"name": "Long Rains", "start_month": 3, "end_month": 5, "plant_start": "March", "harvest_end": "July"},
        {"name": "Short Rains", "start_month": 10, "end_month": 11, "plant_start": "October", "harvest_end": "December"},
    ],
    "southern": [
        {"name": "Long Rains", "start_month": 3, "end_month": 5, "plant_start": "March", "harvest_end": "June"},
        {"name": "Short Rains", "start_month": 10, "end_month": 12, "plant_start": "October", "harvest_end": "January"},
    ],
    "arid": [
        {"name": "Short Rains Only", "start_month": 10, "end_month": 12, "plant_start": "October", "harvest_end": "January"},
    ],
}

# Per-crop calendar data
# days_to_harvest measured from planting
CROP_DATA = {
    "Maize": {
        "days_to_harvest": 120,
        "seasons": ["Long Rains", "Short Rains"],
        "soil_pref": ["Loam", "Clay"],
        "climate_tip": "Maize needs 500–800mm of rain. Plant within 2 weeks of first rains for best yield.",
        "climate_risk": "Drought stress during tasseling (day 60–80) causes major yield loss.",
        "carbon_benefit": "Maize residue left in soil adds organic matter — don't burn it.",
    },
    "Beans": {
        "days_to_harvest": 75,
        "seasons": ["Long Rains", "Short Rains"],
        "soil_pref": ["Loam", "Sandy"],
        "climate_tip": "Beans fix nitrogen in soil — great companion crop for maize.",
        "climate_risk": "Waterlogging causes root rot. Avoid low-lying areas.",
        "carbon_benefit": "Legumes improve soil health and reduce need for synthetic fertiliser.",
    },
    "Coffee": {
        "days_to_harvest": 270,
        "seasons": ["Long Rains"],
        "soil_pref": ["Loam", "Clay"],
        "climate_tip": "Coffee thrives at 1200–1800m altitude with 1200–2000mm rainfall.",
        "climate_risk": "Rising temperatures are pushing coffee belts to higher altitudes.",
        "carbon_benefit": "Coffee grown with shade trees sequesters significantly more carbon.",
    },
    "Tea": {
        "days_to_harvest": 365,
        "seasons": ["Long Rains", "Short Rains"],
        "soil_pref": ["Clay", "Loam"],
        "climate_tip": "Tea is a perennial — it doesn't follow planting seasons but needs consistent rain.",
        "climate_risk": "Dry spells reduce quality and quantity of green leaf.",
        "carbon_benefit": "Tea bushes are long-lived carbon stores — avoid uprooting mature plants.",
    },
    "Avocado": {
        "days_to_harvest": 548,
        "seasons": ["Long Rains"],
        "soil_pref": ["Loam"],
        "climate_tip": "Plant during long rains. Avocado trees take 18 months to first harvest.",
        "climate_risk": "Young trees are sensitive to frost — avoid planting above 2100m.",
        "carbon_benefit": "Avocado trees are excellent long-term carbon sinks.",
    },
    "Banana": {
        "days_to_harvest": 300,
        "seasons": ["Long Rains", "Short Rains"],
        "soil_pref": ["Loam", "Clay"],
        "climate_tip": "Bananas need year-round moisture — supplement with irrigation in dry months.",
        "climate_risk": "Strong winds during long rains can topple banana plants.",
        "carbon_benefit": "Banana plant biomass contributes to surface organic matter.",
    },
    "Vegetables": {
        "days_to_harvest": 60,
        "seasons": ["Long Rains", "Short Rains"],
        "soil_pref": ["Loam", "Sandy"],
        "climate_tip": "Most vegetables can be grown in both seasons with irrigation.",
        "climate_risk": "Heavy rains promote fungal disease — space plants well for airflow.",
        "carbon_benefit": "Intensive vegetable growing with mulch and compost builds soil organic matter.",
    },
}

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


def generate_planting_calendar(lat: float, lon: float, crops: list) -> dict:
    """
    Generates a personalised planting calendar.

    Args:
        lat: Latitude of farm.
        lon: Longitude of farm.
        crops: List of crop names selected by the farmer.

    Returns:
        dict with zone, seasons, and per-crop schedule.
    """
    zone = get_zone(lat, lon)
    seasons = ZONE_SEASONS.get(zone, ZONE_SEASONS["central"])
    current_month = datetime.now().month

    schedule = []

    for crop in crops:
        crop_info = CROP_DATA.get(crop)
        if not crop_info:
            continue

        crop_seasons = []
        for season in seasons:
            if any(s in season["name"] for s in crop_info["seasons"]):
                plant_month = season["start_month"]
                harvest_month = (plant_month + (crop_info["days_to_harvest"] // 30)) % 12 or 12
                harvest_month_name = MONTH_NAMES[harvest_month]

                # Determine if this season is upcoming, current, or past
                if plant_month == current_month:
                    timing = "🟢 Plant NOW"
                elif plant_month > current_month:
                    months_away = plant_month - current_month
                    timing = f"⏳ In {months_away} month{'s' if months_away > 1 else ''}"
                else:
                    months_ago = current_month - plant_month
                    timing = f"⚠️ {months_ago} month{'s' if months_ago > 1 else ''} ago — wait for next season"

                crop_seasons.append({
                    "season": season["name"],
                    "plant_month": season["plant_start"],
                    "harvest_month": harvest_month_name,
                    "timing": timing,
                })

        schedule.append({
            "crop": crop,
            "seasons": crop_seasons,
            "days_to_harvest": crop_info["days_to_harvest"],
            "soil_pref": crop_info["soil_pref"],
            "climate_tip": crop_info["climate_tip"],
            "climate_risk": crop_info["climate_risk"],
            "carbon_benefit": crop_info["carbon_benefit"],
        })

    return {
        "zone": zone.replace("_", " ").title(),
        "lat": round(lat, 4),
        "lon": round(lon, 4),
        "current_month": MONTH_NAMES[current_month],
        "seasons": seasons,
        "schedule": schedule,
    }


def get_zone_description(zone: str) -> str:
    descriptions = {
        "highland": "Highland zone (above 1500m) — cool temps, reliable long and short rains.",
        "central": "Central Kenya — two seasons, moderate rainfall, good for mixed farming.",
        "western": "Western Kenya — extended wet season, high rainfall, good for maize and tea.",
        "coastal": "Coastal zone — hot and humid, Masika and Vuli rain seasons.",
        "rift_valley": "Rift Valley — two seasons, variable rainfall, good for wheat, maize, and horticulture.",
        "southern": "Southern zone — two seasons, suitable for beans, maize, and livestock.",
        "arid": "Arid/semi-arid zone — one short rainy season; focus on drought-tolerant crops.",
    }
    return descriptions.get(zone, "Kenya farming zone.")