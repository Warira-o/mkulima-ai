# Updated services/carbon.py

def calculate_baseline_carbon(farm_size_acres: float, practice: str, 
                             soil_type: str = "loam", crops: list = None) -> dict:
    """
    Enhanced carbon sequestration baseline calculation.
    
    Args:
        farm_size_acres: Farm size in acres
        practice: Farming practice type
        soil_type: Type of soil (clay, loam, sandy)
        crops: List of crops grown (optional)
    
    Returns:
        Dictionary with enhanced audit results
    """
    
    # Base sequestration rates (tCO2e per acre per year)
    sequestration_multipliers = {
        "Conventional": 0.2,
        "No-Till": 0.6,
        "Cover Cropping": 0.8,
        "Agroforestry": 1.5,
        "Regenerative": 1.2
    }
    
    # Soil type modifiers
    soil_modifiers = {
        "Clay": 1.2,           # Holds more carbon
        "Loam": 1.0,           # Baseline
        "Sandy": 0.7           # Lower carbon retention
    }
    
    # Get base rate
    base_rate = sequestration_multipliers.get(practice, 0.2)
    
    # Apply soil modifier
    soil_modifier = soil_modifiers.get(soil_type, 1.0)
    adjusted_rate = base_rate * soil_modifier
    
    # Calculate sequestration
    est_sequestration = farm_size_acres * adjusted_rate
    
    return {
        "farm_size": farm_size_acres,
        "practice": practice,
        "soil_type": soil_type,
        "base_rate": base_rate,
        "soil_modifier": soil_modifier,
        "adjusted_rate": round(adjusted_rate, 3),
        "estimated_tCO2e": round(est_sequestration, 2),
        "crops": crops or [],
        "soil_health_note": get_soil_health_note(soil_type, practice)
    }

def get_soil_health_note(soil_type: str, practice: str) -> str:
    """
    Provide soil health interpretation.
    """
    
    notes = {
        ("Clay", "Conventional"): "⚠️ Clay soil can compact with conventional farming. Consider cover crops to maintain structure.",
        ("Clay", "No-Till"): "✅ No-till is excellent for clay—protects structure and builds carbon.",
        ("Clay", "Regenerative"): "✅ Perfect combination! Clay + regenerative practices maximize carbon storage.",
        ("Loam", "Conventional"): "Good baseline. Loam balances well with any practice.",
        ("Loam", "Regenerative"): "✅ Ideal! Loam + regenerative = excellent carbon sequestration.",
        ("Sandy", "Conventional"): "⚠️ Sandy soil loses carbon quickly. Regenerative practices essential for improvement.",
        ("Sandy", "Regenerative"): "✅ Regenerative practices can significantly improve sandy soil carbon retention.",
        ("Sandy", "Agroforestry"): "✅ Trees help sandy soil retain moisture and carbon—great choice!"
    }
    
    return notes.get((soil_type, practice), "Standard soil health baseline.")