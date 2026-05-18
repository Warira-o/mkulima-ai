# services/veterinary.py
import math
import pandas as pd
from typing import List, Dict

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two GPS coordinates (in km).
    """
    R = 6371  # Earth's radius in kilometers
    
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    
    a = (math.sin(dLat / 2) * math.sin(dLat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dLon / 2) * math.sin(dLon / 2))
    
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def get_nearby_veterinarians(latitude: float, longitude: float, 
                            radius_km: float = 15, 
                            animal_type: str = None) -> List[Dict]:
    """
    Find veterinary services near farmer's location.
    
    Args:
        latitude: Farmer's GPS latitude
        longitude: Farmer's GPS longitude
        radius_km: Search radius (default 15 km)
        animal_type: Filter by livestock type (cattle, poultry, sheep, etc.)
    
    Returns:
        List of veterinary clinics sorted by distance
    """
    
    # MVP: Hardcoded vet database for Kenya
    # In production, integrate with Google Places API or veterinary association database
    VETERINARY_DATABASE = [
        {
            "id": "vet_001",
            "name": "Nairobi Central Veterinary Clinic",
            "phone": "+254 702 000 001",
            "whatsapp": "+254702000001",
            "location": (-1.2921, 36.8219),  # Central Nairobi
            "services": ["cattle", "sheep", "goats", "poultry"],
            "hours": "8:00 AM - 6:00 PM",
            "emergency_hours": "24/7 Emergency Line",
            "address": "Nairobi Central, Nairobi",
            "rating": 4.8,
            "specialties": ["vaccination", "surgery", "diagnostics"]
        },
        {
            "id": "vet_002",
            "name": "Karen Animal Hospital",
            "phone": "+254 722 000 002",
            "whatsapp": "+254722000002",
            "location": (-1.3521, 36.6869),  # Karen, Nairobi
            "services": ["cattle", "sheep", "goats", "poultry", "pigs"],
            "hours": "9:00 AM - 5:30 PM",
            "emergency_hours": "Call emergency line",
            "address": "Karen, Nairobi",
            "rating": 4.6,
            "specialties": ["livestock farming", "emergency care"]
        },
        {
            "id": "vet_003",
            "name": "Njoro Veterinary Services",
            "phone": "+254 718 000 003",
            "whatsapp": "+254718000003",
            "location": (-0.3667, 35.5833),  # Njoro, Nakuru County
            "services": ["cattle", "sheep", "goats", "poultry"],
            "hours": "7:00 AM - 5:00 PM",
            "emergency_hours": "Available",
            "address": "Njoro, Nakuru County",
            "rating": 4.7,
            "specialties": ["dairy cattle", "reproductive health"]
        },
        {
            "id": "vet_004",
            "name": "Kisii County Veterinary Centre",
            "phone": "+254 735 000 004",
            "whatsapp": "+254735000004",
            "location": (-0.6823, 34.7742),  # Kisii
            "services": ["cattle", "sheep", "goats", "poultry"],
            "hours": "8:00 AM - 5:00 PM",
            "emergency_hours": "24/7 by appointment",
            "address": "Kisii Town, Kisii County",
            "rating": 4.5,
            "specialties": ["general practice", "foot-and-mouth disease management"]
        },
        {
            "id": "vet_005",
            "name": "Thika Road Veterinary Clinic",
            "phone": "+254 722 000 005",
            "whatsapp": "+254722000005",
            "location": (-1.3333, 36.9667),  # Thika
            "services": ["cattle", "poultry", "sheep"],
            "hours": "8:30 AM - 6:00 PM",
            "emergency_hours": "Emergency calls accepted",
            "address": "Thika, Kiambu County",
            "rating": 4.4,
            "specialties": ["dairy farming support", "vaccination programs"]
        },
    ]
    
    # Calculate distance to each vet
    nearby_vets = []
    for vet in VETERINARY_DATABASE:
        distance = haversine_distance(
            latitude, longitude,
            vet["location"][0], vet["location"][1]
        )
        
        # Only include vets within radius
        if distance <= radius_km:
            vet_copy = vet.copy()
            vet_copy["distance_km"] = round(distance, 1)
            
            # Filter by animal type if specified
            if animal_type is None or animal_type in vet_copy["services"]:
                nearby_vets.append(vet_copy)
    
    # Sort by distance
    nearby_vets.sort(key=lambda x: x["distance_km"])
    
    return nearby_vets

def format_vet_for_display(vet: Dict) -> Dict:
    """
    Format vet data for streamlit display.
    """
    return {
        "name": vet["name"],
        "distance": f"{vet['distance_km']} km",
        "phone": vet["phone"],
        "whatsapp": vet["whatsapp"],
        "hours": vet["hours"],
        "emergency": vet.get("emergency_hours", "N/A"),
        "animals": ", ".join(vet["services"]),
        "specialties": ", ".join(vet["specialties"]),
        "address": vet["address"],
        "rating": f"⭐ {vet['rating']}"
    }

def get_emergency_hotline():
    """
    Return emergency veterinary hotline numbers.
    """
    return {
        "kenya_vet_association": {
            "name": "Kenya Veterinary Association Emergency",
            "phone": "+254 722 222 222",  # Placeholder
            "description": "After-hours emergency support"
        },
        "nairobi_emergency": {
            "name": "Nairobi Emergency Animal Services",
            "phone": "+254 700 000 000",  # Placeholder
            "description": "24/7 emergency vet line"
        }
    }

def get_emergency_care_tips(animal_type: str = "cattle") -> Dict:
    """
    Return basic emergency care guidance while waiting for veterinarian.
    """
    EMERGENCY_TIPS = {
        "cattle": {
            "signs": [
                "Won't eat or drink",
                "Lying down, won't get up",
                "Bleeding from mouth/nose",
                "Difficulty breathing",
                "Swollen joints",
                "Unusual discharge"
            ],
            "immediate_actions": [
                "Move animal to quiet, clean space",
                "Provide clean water if possible",
                "Note exact symptoms for vet",
                "Check temperature if possible",
                "Keep animal calm and stress-free"
            ],
            "avoid": [
                "Don't move animal unless necessary",
                "Don't force-feed or force-drink",
                "Don't use unknown medications",
                "Don't delay calling vet"
            ]
        },
        "poultry": {
            "signs": [
                "Not eating/drinking",
                "Ruffled feathers",
                "Discharge from eyes/nose",
                "Twisted neck/wobbling",
                "Lameness or dragging wing",
                "Watery/bloody droppings"
            ],
            "immediate_actions": [
                "Isolate sick bird from flock",
                "Provide clean water",
                "Keep warm and dry",
                "Monitor for spread to other birds",
                "Note onset of symptoms"
            ],
            "avoid": [
                "Don't share equipment with healthy birds",
                "Don't use human medicines",
                "Don't delay treatment"
            ]
        },
        "sheep_goats": {
            "signs": [
                "Limping or lameness",
                "Stiff joints",
                "Won't stand",
                "Coughing",
                "Diarrhea",
                "Excessive drooling"
            ],
            "immediate_actions": [
                "Isolate from flock",
                "Provide hay and water",
                "Keep in dry shelter",
                "Monitor closely",
                "Document symptoms"
            ],
            "avoid": [
                "Don't force movement",
                "Don't use old vaccines",
                "Don't delay professional help"
            ]
        }
    }
    
    return EMERGENCY_TIPS.get(animal_type, EMERGENCY_TIPS["cattle"])