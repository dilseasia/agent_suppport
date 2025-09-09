# from app.models.model import DealershipAddress

# def get_dealership_address(dealership_id: str) -> DealershipAddress:
#     """
#     Mock dealership address retrieval
#     """
#     # dealerships = {
#     #     "NYC01": DealershipAddress(
#     #         dealership_id="NYC01", 
#     #         name="SuperCar Manhattan", 
#     #         address="123 Broadway, New York, NY 10001",
#     #         phone="(212) 555-1234"
#     #     ),
#     #     "LA01": DealershipAddress(
#     #         dealership_id="LA01", 
#     #         name="SuperCar Los Angeles", 
#     #         address="456 Sunset Blvd, Los Angeles, CA 90028",
#     #         phone="(323) 555-5678"
#     #     )
#     # }
#     # return dealerships.get(dealership_id, 
#     #     DealershipAddress(
#     #         dealership_id=dealership_id, 
#     #         name="Unknown Dealership", 
#     #         address="Address Not Found"
#     #     )
#     # )

#     dealerships = {
#         "NYC01": {
#             "dealership_id": "NYC01", 
#             "name": "SuperCar Manhattan", 
#             "address": "123 Broadway, New York, NY 10001",
#             "phone" : "(212) 555-1234",
#             "hours":"24 hours"
#         },
#         "LA01":{
#             "dealership_id": "LA01", 
#             "name": "SuperCar Los Angeles", 
#             "address": "456 Sunset Blvd, Los Angeles, CA 90028",
#             "phone": "(323) 555-5678",
#             "hours":"24 hours"
#         }
#         }
#     return dealerships.get(dealership_id)

# def handle(query: str) -> str:
#     # Dummy implementation
#     return "Currently available cars: Honda Civic, Toyota Corolla."


# In-memory dealerships data
dealerships = {
    "NYC01": {
        "dealership_id": "NYC01",
        "name": "SuperCar Manhattan",
        "address": "123 Broadway, New York, NY 10001",
        "phone": "(212) 555-1234",
        "hours": "24 hours"
    },
    "LA01": {
        "dealership_id": "LA01",
        "name": "SuperCar Los Angeles",
        "address": "456 Sunset Blvd, Los Angeles, CA 90028",
        "phone": "(323) 555-5678",
        "hours": "24 hours"
    }
}

# List of cars in each dealership
cars_in_dealership = {
    "NYC01": ["Honda Civic", "Toyota Corolla", "Ford Mustang", "Tesla Model 3"],
    "LA01": ["Honda Accord", "Chevrolet Camaro", "Ford Mustang", "Tesla Model 3"]
}


def get_dealership(dealership_id: str) -> dict:
    """
    Return dealership details by ID.
    """
    return dealerships.get(dealership_id, None)


def list_cars(dealership_id: str = None, brand_filter: str = None) -> list:
    """
    Return list of cars. Can filter by dealership and/or brand keyword.
    """
    all_cars = []

    if dealership_id:
        all_cars = cars_in_dealership.get(dealership_id, [])
    else:
        # Aggregate all cars if no dealership specified
        for cars in cars_in_dealership.values():
            all_cars.extend(cars)
        all_cars = list(set(all_cars))  # Remove duplicates

    # Filter by brand/model keyword if provided
    if brand_filter:
        brand_filter_lower = brand_filter.lower()
        all_cars = [car for car in all_cars if brand_filter_lower in car.lower()]

    return all_cars


def handle(query: str) -> dict:
    """
    Handle dealership-related queries such as:
    - fetching dealership info
    - listing available cars
    - filtering cars by brand or location
    """
    query_lower = query.lower()

    # --- Dealership info ---
    if any(kw in query_lower for kw in ["dealership info", "dealership details", "where is"]):
        dealership_id = "NYC01" if "nyc" in query_lower else "LA01" if "la" in query_lower else "NYC01"
        info = get_dealership(dealership_id)
        if info:
            return {"action": "dealership_info", "details": info}
        return {"action": "no_dealership_found"}

    # --- List cars ---
    if any(kw in query_lower for kw in ["cars", "available cars", "show me"]):
        brand_keywords = ["honda", "toyota", "ford", "tesla", "chevrolet"]
        brand_filter = next((kw for kw in brand_keywords if kw in query_lower), None)

        dealership_id = "NYC01" if "nyc" in query_lower else "LA01" if "la" in query_lower else None
        car_list = list_cars(dealership_id=dealership_id, brand_filter=brand_filter)

        return {"action": "list_cars", "cars": car_list}

    # --- Default fallback ---
    return {"action": "fallback"}
