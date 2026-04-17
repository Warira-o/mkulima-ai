def calculate_baseline_carbon(farm_size_acres: float, practice: str) -> dict:
    """
    Calculates estimated carbon sequestration baseline based on farm size and practices.
    Returns a dictionary with the audit results.
    """
    # Industry standard estimates (tCO2e sequestered per acre per year)
    sequestration_multipliers = {
        "Conventional": 0.2,
        "No-Till": 0.6,
        "Cover Cropping": 0.8,
        "Agroforestry": 1.5,
        "Regenerative": 1.2
    }
    
    rate = sequestration_multipliers.get(practice, 0.2)
    est_sequestration = farm_size_acres * rate
    
    return {
        "farm_size": farm_size_acres,
        "practice": practice,
        "rate": rate,
        "estimated_tCO2e": round(est_sequestration, 2)
    }