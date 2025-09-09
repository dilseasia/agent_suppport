# import random
# import uuid
# from typing import List
# from app.models.model import (
#     AppointmentSlot, 
#     AppointmentConfirmation, 
#     AppointmentRequest
# )

# def check_appointment_availability(
#     dealership_id: str, 
#     date: str
# ) -> List[AppointmentSlot]:
#     """
#     Mock appointment availability check
#     """
#     time_slots = [
#         "09:00", "10:00", "11:00", 
#         "13:00", "14:00", "15:00", 
#         "16:00", "17:00"
#     ]
#     # return [
#     #     AppointmentSlot(time=slot, available=random.choice([True, False]))
#     #     for slot in time_slots
#     # ]
#     return time_slots


# # def schedule_appointment(
# #     request: AppointmentRequest
# # ) -> AppointmentConfirmation:
# #     """
# #     Mock appointment scheduling
# #     """
# #     return AppointmentConfirmation(
# #         confirmation_id=str(uuid.uuid4()),
# #         status="Confirmed",
# #         details={
# #             "dealership_id": request.dealership_id,
# #             "date": request.date,
# #             "time": request.time,
# #             "car_model": request.car_model
# #         }
# #     )


# def schedule_appointment(
#         car_model: str, 
#         date:str, 
#         dealership_id:str, 
#         time:str, 
#         user_id: str):
    
#     return {
#         "confirmation_id": str(uuid.uuid4()),
#         "status": "Confirmed",
#         "details": {
#             "dealership_id": "asdfg",
#             "date": "12.12.202",
#             "time": "12:25",
#             "car_model": "car model"
#         }
#     }

# # example: app/services/tools/appointment.py

# def handle(query: str) -> str:
#     # This is a dummy implementation. Replace with real logic.
#     if "book" in query.lower():
#         return "Your appointment has been booked successfully! ✅"
#     elif "cancel" in query.lower():
#         return "Your appointment has been canceled. ✅"
#     else:
#         return "Your appointment is confirmed for tomorrow at 10 AM."


import uuid
import json
from datetime import datetime, timedelta

# In-memory storage
appointments = {}        # Confirmed appointments: {user_id: details}
pending_actions = {}     # Pending confirmations: {user_id: {"action": "book/cancel", "details": {...}}}
available_cars = ["Honda Civic", "Toyota Corolla", "Ford Mustang"]


def schedule_appointment(car_model: str, date: str, dealership_id: str, time: str, user_id: str) -> dict:
    """
    Schedule an appointment and save it in memory.
    """
    confirmation = {
        "confirmation_id": str(uuid.uuid4()),
        "status": "Confirmed",
        "details": {
            "dealership_id": dealership_id,
            "date": date,
            "time": time,
            "car_model": car_model
        }
    }
    appointments[user_id] = confirmation
    return confirmation


def handle(query: str) -> str:
    """
    Handle appointment-related queries.
    Supports:
    - booking appointments
    - checking status
    - cancelling existing bookings
    - confirming or rejecting pending actions
    """
    user_id = "user"  # Replace with real session/user id
    query_lower = query.lower()
    has_appointment = user_id in appointments

    # --- Pending Confirmation ---
    if user_id in pending_actions:
        return json.dumps({"action": "pending", "details": pending_actions[user_id]})

    # --- Booking Intent ---
    if any(kw in query_lower for kw in ["book", "schedule", "make an appointment"]):
        if has_appointment:
            return json.dumps({"action": "already_booked", "details": appointments[user_id]})
        return json.dumps({"action": "choose_car", "cars": available_cars})

    # --- Car Selection (user selects a car) ---
    for car in available_cars:
        if car.lower() in query_lower:
            date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            time = "10:00"
            dealership_id = "NYC01"
            pending_actions[user_id] = {
                "action": "book",
                "details": {
                    "car_model": car,
                    "date": date,
                    "time": time,
                    "dealership_id": dealership_id
                }
            }
            return json.dumps({"action": "confirm_booking", "details": pending_actions[user_id]})

    # --- Cancellation Intent ---
    if "cancel" in query_lower:
        if has_appointment:
            pending_actions[user_id] = {"action": "cancel", "details": appointments[user_id]}
            return json.dumps({"action": "confirm_cancel", "details": appointments[user_id]})
        return json.dumps({"action": "no_appointment"})

    # --- Status Check ---
    if any(kw in query_lower for kw in ["is", "do i have", "status", "my appointment", "booked"]):
        if has_appointment:
            return json.dumps({"action": "status", "details": appointments[user_id]})
        return json.dumps({"action": "no_appointment"})

    # --- Default Fallback ---
    return json.dumps({"action": "fallback"})
