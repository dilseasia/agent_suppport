import random
from app.models.model import WeatherData

def get_weather(city: str) -> WeatherData:
    """
    Mock weather retrieval for a given city
    """
    weather_conditions = [
        "sunny", "cloudy", "rainy"
    ]
    city = [
        "newyork", "delhi", "chandigarh"
    ]
    # return WeatherData(
    #     temperature=f"{random.randint(20, 35)}°C", 
    #     city=random.choice(city),
    #     conditions=random.choice(weather_conditions)
    # )
    return {
        "temperature":f"{random.randint(20, 35)}°C", 
        "city":random.choice(city),
        "conditions":random.choice(weather_conditions)
    }