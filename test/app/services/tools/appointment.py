import random
import uuid
from typing import List
from app.models.model import (
    AppointmentSlot, 
    AppointmentConfirmation, 
    AppointmentRequest
)

def check_appointment_availability(
    dealership_id: str, 
    date: str
) -> List[AppointmentSlot]:
    """
    Mock appointment availability check
    """
    time_slots = [
        "09:00", "10:00", "11:00", 
        "13:00", "14:00", "15:00", 
        "16:00", "17:00"
    ]
    # return [
    #     AppointmentSlot(time=slot, available=random.choice([True, False]))
    #     for slot in time_slots
    # ]
    return time_slots


# def schedule_appointment(
#     request: AppointmentRequest
# ) -> AppointmentConfirmation:
#     """
#     Mock appointment scheduling
#     """
#     return AppointmentConfirmation(
#         confirmation_id=str(uuid.uuid4()),
#         status="Confirmed",
#         details={
#             "dealership_id": request.dealership_id,
#             "date": request.date,
#             "time": request.time,
#             "car_model": request.car_model
#         }
#     )


def schedule_appointment(
        car_model: str, 
        date:str, 
        dealership_id:str, 
        time:str, 
        user_id: str):
    
    return {
        "confirmation_id": str(uuid.uuid4()),
        "status": "Confirmed",
        "details": {
            "dealership_id": "asdfg",
            "date": "12.12.202",
            "time": "12:25",
            "car_model": "car model"
        }
    }
