import os
import requests

def get_weather(location: str) -> str:
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location},KE&appid={api_key}&units=metric"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            temp = data['main']['temp']
            desc = data['weather'][0]['description']
            return f"{temp}°C with {desc}"
        elif response.status_code == 404:
            return "Location not found. Please try a major nearby town."
        else:
            return "Unable to fetch weather at the moment."
    except Exception as e:
        return f"Weather service error: {str(e)}"