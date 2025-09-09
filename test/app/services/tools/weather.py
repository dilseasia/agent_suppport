# import random
# from app.models.model import WeatherData

# # def get_weather(city: str) -> WeatherData:
# #     """
# #     Mock weather retrieval for a given city
# #     """
# #     weather_conditions = [
# #         "sunny", "cloudy", "rainy"
# #     ]
# #     city = [
# #         "newyork", "delhi", "chandigarh"
# #     ]
# #     # return WeatherData(
# #     #     temperature=f"{random.randint(20, 35)}°C", 
# #     #     city=random.choice(city),
# #     #     conditions=random.choice(weather_conditions)
# #     # )
# #     return {
# #         "temperature":f"{random.randint(20, 35)}°C", 
# #         "city":random.choice(city),
# #         "conditions":random.choice(weather_conditions)
# #     }


# import random
# from datetime import datetime

# def get_weather(city: str):
#     """
#     Mock weather retrieval for a given city with date included.
#     """
#     weather_conditions = ["sunny", "cloudy", "rainy"]

#     # Example cities
#     cities = ["newyork", "delhi", "chandigarh"]

#     return {
#         "temperature": f"{random.randint(20, 35)}°C",
#         "city": random.choice(cities),
#         "conditions": random.choice(weather_conditions),
#         "date": datetime.now().strftime("%Y-%m-%d")  # e.g., '2025-08-25'
#     }

# def handle(query: str) -> str:
#     # Dummy implementation
#     return "The weather today is sunny with a high of 28°C."
import random
from datetime import datetime

# Example cities and weather conditions
cities = ["newyork", "delhi", "chandigarh"]
weather_conditions = ["sunny", "cloudy", "rainy", "stormy", "foggy", "windy"]


def get_weather(city: str = None) -> dict:
    """
    Mock weather retrieval for a given city.
    If no city is provided, a random one is chosen.
    """
    city = city.lower() if city else random.choice(cities)
    return {
        "city": city.title(),
        "temperature": f"{random.randint(20, 35)}°C",
        "conditions": random.choice(weather_conditions),
        "date": datetime.now().strftime("%Y-%m-%d")
    }


def handle(query: str) -> str:
    """
    Handle weather-related queries.
    Supports:
    - current weather
    - temperature
    - rain/sunny/cloudy conditions
    - forecasts for New York, Delhi, and Chandigarh
    """
    query_lower = query.lower()

    # --- Determine the city ---
    selected_city = None
    for c in cities:
        if c in query_lower:
            selected_city = c
            break

    weather = get_weather(selected_city)

    # --- Queries about today's weather ---
    if any(kw in query_lower for kw in ["today", "current", "weather", "temperature", "rain", "forecast"]):
        return f"🌦️ Weather update for {weather['city']} on {weather['date']}: {weather['conditions']} with a temperature of {weather['temperature']}."

    # --- Queries about specific info (temperature, conditions) ---
    elif any(kw in query_lower for kw in ["temperature", "hot", "cold"]):
        return f"🌡️ The temperature in {weather['city']} is {weather['temperature']} today."

    elif any(kw in query_lower for kw in ["condition", "rain", "sunny", "cloudy", "storm"]):
        return f"☁️ The weather in {weather['city']} today is {weather['conditions']}."

    # --- Default fallback ---
    return "I can provide current weather updates and forecasts for New York, Delhi, and Chandigarh."
