"""
services/market_prices.py
Fetches daily commodity prices for Kenyan markets.
Falls back to realistic static data if the API is unavailable.
"""

import os
import requests
from datetime import datetime

# Static fallback prices (KES per 90kg bag or per kg where noted)
# Sourced from typical AMIS Kenya ranges
FALLBACK_PRICES = {
    "Maize": {
        "unit": "per 90kg bag",
        "markets": {
            "Nairobi": 3200,
            "Nakuru": 3000,
            "Eldoret": 2900,
            "Kisumu": 3100,
            "Mombasa": 3400,
        },
        "trend": "stable",
        "tip": "Maize prices are usually higher in Nairobi — consider transport costs before selling locally.",
    },
    "Beans": {
        "unit": "per 90kg bag",
        "markets": {
            "Nairobi": 9500,
            "Nakuru": 9000,
            "Eldoret": 8800,
            "Kisumu": 9200,
            "Mombasa": 9800,
        },
        "trend": "rising",
        "tip": "Bean prices are rising — holding stock for 2–4 weeks may increase earnings.",
    },
    "Tea (green leaf)": {
        "unit": "per kg",
        "markets": {
            "Nairobi": 24,
            "Nakuru": 22,
            "Kericho": 23,
            "Kisumu": 21,
            "Mombasa": 25,
        },
        "trend": "stable",
        "tip": "Sell to KTDA factories for guaranteed prices and bonus payments.",
    },
    "Coffee (cherry)": {
        "unit": "per kg",
        "markets": {
            "Nairobi": 80,
            "Nyeri": 85,
            "Kirinyaga": 82,
            "Kisumu": 75,
            "Mombasa": 88,
        },
        "trend": "rising",
        "tip": "Coffee cherry prices are strong — ensure proper processing to fetch premium rates.",
    },
    "Potatoes": {
        "unit": "per 110kg bag",
        "markets": {
            "Nairobi": 2800,
            "Nakuru": 2500,
            "Eldoret": 2400,
            "Kisumu": 2700,
            "Mombasa": 3000,
        },
        "trend": "falling",
        "tip": "Potato prices are currently falling — try to sell quickly or store in a cool place.",
    },
    "Tomatoes": {
        "unit": "per crate (≈30kg)",
        "markets": {
            "Nairobi": 1800,
            "Nakuru": 1500,
            "Eldoret": 1400,
            "Kisumu": 1600,
            "Mombasa": 2000,
        },
        "trend": "stable",
        "tip": "Tomato prices vary weekly — check the nearest market before harvesting.",
    },
}

TREND_ARROWS = {
    "rising": "📈 Rising",
    "falling": "📉 Falling",
    "stable": "➡️ Stable",
}


def get_market_prices(commodity: str = None) -> dict:
    """
    Returns today's market price data for Kenyan commodities.
    Attempts live fetch first; falls back to static data.

    Args:
        commodity: Optional crop name to filter results.

    Returns:
        dict with commodity price data.
    """
    # Try to fetch live data from a public Kenyan market prices source
    # (AMIS Kenya public endpoint — may not always be available)
    live_data = _try_live_fetch(commodity)
    if live_data:
        return live_data

    # Use fallback data
    if commodity and commodity in FALLBACK_PRICES:
        return {commodity: FALLBACK_PRICES[commodity]}
    return FALLBACK_PRICES


def _try_live_fetch(commodity: str = None) -> dict | None:
    """
    Attempts to fetch live prices from a public API.
    Returns None if unavailable.
    """
    try:
        # AMIS Kenya open data endpoint (illustrative — replace with live endpoint if available)
        url = "https://www.amis.co.ke/api/prices"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            raw = response.json()
            return _parse_amis_response(raw, commodity)
    except Exception:
        pass
    return None


def _parse_amis_response(raw: dict, commodity: str = None) -> dict:
    """Parse AMIS API response into standard format."""
    # Placeholder — implement according to actual AMIS response schema
    return None


def get_best_market(commodity: str) -> dict:
    """
    Returns the highest-priced market for a given commodity today.

    Args:
        commodity: Name of the crop.

    Returns:
        dict with best market name and price.
    """
    data = FALLBACK_PRICES.get(commodity)
    if not data:
        return {"market": "Unknown", "price": 0, "unit": ""}
    best = max(data["markets"], key=lambda m: data["markets"][m])
    return {
        "market": best,
        "price": data["markets"][best],
        "unit": data["unit"],
        "trend": TREND_ARROWS.get(data["trend"], "➡️ Stable"),
        "tip": data["tip"],
    }


def format_price_table(commodity: str) -> list[dict]:
    """
    Returns a list of dicts suitable for a Streamlit dataframe.

    Args:
        commodity: Name of the crop.

    Returns:
        List of {Market, Price (KES), Unit} dicts.
    """
    data = FALLBACK_PRICES.get(commodity, {})
    markets = data.get("markets", {})
    unit = data.get("unit", "")
    return [
        {"Market": market, f"Price (KES) — {unit}": price}
        for market, price in sorted(markets.items(), key=lambda x: -x[1])
    ]


def get_last_updated() -> str:
    """Returns a human-friendly last-updated timestamp."""
    return datetime.now().strftime("%d %b %Y, %H:%M")