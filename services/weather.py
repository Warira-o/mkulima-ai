import os
import requests

def get_weather_by_coords(lat: float, lon: float) -> str:
    """Fetches real-time weather using exact GPS coordinates."""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            temp = data['main']['temp']
            desc = data['weather'][0]['description']
            location_name = data['name']
            return f"{temp}°C with {desc} in {location_name}"
        else:
            return "Unable to fetch weather for these coordinates."
    except Exception as e:
        return f"Weather service error: {str(e)}"