

import requests
from datetime import datetime
from typing import Dict

def get_current_carbon_prices() -> Dict:
    """
    Fetch current carbon credit market prices.
    For MVP, returns hardcoded values.
    In production, integrate with real market APIs:
    - Carbon Desk API
    - Verra Registry
    - Gold Standard pricing
    """
    
    # Real-world 2024 prices (approximate)
    CARBON_PRICES = {
        "vcs_verified_carbon_unit": {
            "name": "Verra VCS (Verified Carbon Unit)",
            "price_usd": 12.50,
            "price_kes": 1625,  # Approximate KES conversion
            "standard": "International standard",
            "description": "Most widely traded carbon credits"
        },
        "gold_standard": {
            "name": "Gold Standard Credits",
            "price_usd": 14.00,
            "price_kes": 1820,
            "standard": "Premium quality",
            "description": "Includes SDG benefits"
        },
        "kenya_national": {
            "name": "Kenya National Carbon Market",
            "price_usd": 10.00,
            "price_kes": 1300,
            "standard": "Emerging market",
            "description": "Kenya-specific credits"
        }
    }
    
    return CARBON_PRICES

def calculate_potential_earnings(
    tco2e_sequestered: float,
    carbon_standard: str = "vcs_verified_carbon_unit",
    years: int = 1
) -> Dict:
    """
    Calculate potential farmer earnings from carbon credits.
    
    Args:
        tco2e_sequestered: Tons of CO2 equivalent sequestered
        carbon_standard: Type of carbon credit standard
        years: Number of years for aggregated earnings
    
    Returns:
        Dictionary with earnings breakdown
    """
    
    prices = get_current_carbon_prices()
    standard_data = prices.get(carbon_standard, prices["vcs_verified_carbon_unit"])
    
    annual_earnings_usd = tco2e_sequestered * standard_data["price_usd"]
    annual_earnings_kes = tco2e_sequestered * standard_data["price_kes"]
    
    total_earnings_usd = annual_earnings_usd * years
    total_earnings_kes = annual_earnings_kes * years
    
    return {
        "carbon_credits": tco2e_sequestered,
        "standard": standard_data["name"],
        "annual_earnings_usd": round(annual_earnings_usd, 2),
        "annual_earnings_kes": round(annual_earnings_kes, 2),
        "total_earnings_usd": round(total_earnings_usd, 2),
        "total_earnings_kes": round(total_earnings_kes, 2),
        "price_per_tco2e_usd": standard_data["price_usd"],
        "price_per_tco2e_kes": standard_data["price_kes"],
        "years": years,
        "description": standard_data["description"]
    }

def get_carbon_certification_requirements() -> Dict:
    """
    Return requirements for different carbon credit certifications.
    """
    
    return {
        "vcs_verra": {
            "standard": "Verified Carbon Standard (Verra)",
            "cost_estimate_usd": 500,
            "timeline_months": 3,
            "requirements": [
                "Baseline carbon assessment",
                "Land use documentation",
                "Annual monitoring reports",
                "Third-party verification",
                "Soil carbon testing"
            ],
            "requirements_detail": [
                "• Submit baseline carbon audit",
                "• Provide farm location (GPS verified)",
                "• Document current farming practices",
                "• Annual soil sampling & analysis",
                "• Third-party verification visit",
                "• Continued monitoring for 5-10 years"
            ],
            "pros": [
                "Most recognized globally",
                "Best market liquidity",
                "Highest prices typically"
            ],
            "cons": [
                "More rigorous requirements",
                "Higher certification costs",
                "Longer certification period"
            ]
        },
        "gold_standard": {
            "standard": "Gold Standard for Global Goals",
            "cost_estimate_usd": 750,
            "timeline_months": 4,
            "requirements": [
                "Baseline assessment",
                "SDG impact plan",
                "Community engagement",
                "Annual verification",
                "Impact monitoring"
            ],
            "requirements_detail": [
                "• Complete sustainability impact assessment",
                "• Engage local community in planning",
                "• Document health, education, poverty benefits",
                "• Annual third-party audits",
                "• Demonstrate dual benefits (climate + SDG)"
            ],
            "pros": [
                "Premium prices",
                "SDG co-benefits",
                "Community development focus"
            ],
            "cons": [
                "Very rigorous process",
                "Higher costs",
                "Requires community participation"
            ]
        },
        "kenya_national": {
            "standard": "Kenya National Carbon Market",
            "cost_estimate_usd": 200,
            "timeline_months": 1,
            "requirements": [
                "Farm registration",
                "Basic carbon assessment",
                "Annual reporting",
                "Local verification"
            ],
            "requirements_detail": [
                "• Register farm with Kenya Forest Service",
                "• Basic soil carbon measurement",
                "• Annual farm inspection",
                "• Simple reporting template"
            ],
            "pros": [
                "Lower costs",
                "Faster certification",
                "Government backed",
                "Easier process"
            ],
            "cons": [
                "Lower prices",
                "Emerging/untested market",
                "Less global liquidity"
            ]
        }
    }

def get_certification_checklist(standard: str) -> list:
    """
    Return step-by-step checklist for carbon credit certification.
    """
    
    CHECKLISTS = {
        "vcs_verra": [
            "Step 1: Hire a qualified carbon consultant",
            "Step 2: Conduct baseline carbon audit (3 weeks)",
            "Step 3: Document current practices with photos",
            "Step 4: Collect soil samples for carbon testing",
            "Step 5: Submit Project Design Document (PDD)",
            "Step 6: Verra reviews and approves PDD",
            "Step 7: Third-party auditor visits farm (1 day)",
            "Step 8: Receive verification and registration",
            "Step 9: Start selling verified carbon credits",
            "Step 10: Annual monitoring and reporting"
        ],
        "gold_standard": [
            "Step 1: Assess SDG benefits from your farm improvements",
            "Step 2: Conduct baseline carbon audit",
            "Step 3: Engage community stakeholders in planning",
            "Step 4: Submit Gold Standard project design",
            "Step 5: Gold Standard board review (6-8 weeks)",
            "Step 6: Third-party auditor verification",
            "Step 7: Get impact monitoring plan approved",
            "Step 8: Registration and verification",
            "Step 9: Start selling Gold Standard credits",
            "Step 10: Annual impact & carbon monitoring"
        ],
        "kenya_national": [
            "Step 1: Register farm with Kenya Forest Service",
            "Step 2: Simple carbon assessment form",
            "Step 3: Take soil samples (DIY or local assistance)",
            "Step 4: Submit basic documentation",
            "Step 5: Local government verification visit",
            "Step 6: Receive farm carbon certificate",
            "Step 7: Start selling Kenya carbon credits",
            "Step 8: Annual simple reporting"
        ]
    }
    
    return CHECKLISTS.get(standard, CHECKLISTS["vcs_verra"])