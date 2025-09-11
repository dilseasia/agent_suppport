import random
from app.models.model import WeatherData

# def get_weather(city: str) -> WeatherData:
#     """
#     Mock weather retrieval for a given city
#     """
#     weather_conditions = [
#         "sunny", "cloudy", "rainy"
#     ]
#     city = [
#         "newyork", "delhi", "chandigarh"
#     ]
#     # return WeatherData(
#     #     temperature=f"{random.randint(20, 35)}°C", 
#     #     city=random.choice(city),
#     #     conditions=random.choice(weather_conditions)
#     # )
#     return {
#         "temperature":f"{random.randint(20, 35)}°C", 
#         "city":random.choice(city),
#         "conditions":random.choice(weather_conditions)
#     }


import random
from datetime import datetime

def get_weather(city: str):
    """
    Mock weather retrieval for a given city with date included.
    """
    weather_conditions = ["sunny", "cloudy", "rainy"]

    # Example cities
    cities = ["newyork", "delhi", "chandigarh"]

    return {
        "temperature": f"{random.randint(20, 35)}°C",
        "city": random.choice(cities),
        "conditions": random.choice(weather_conditions),
        "date": datetime.now().strftime("%Y-%m-%d")  # e.g., '2025-08-25'
    }
