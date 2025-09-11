# app/Agent/appointment/tool.py

import random
from datetime import datetime, timedelta

# In-memory "database" of appointments
appointments = {}

def book_appointment(vehicle: str, date: str = None, time: str = None) -> dict:
    """
    Book a new appointment. If no date/time provided, pick earliest slot.
    """
    if not date or not time:
        # Default earliest slot: tomorrow at 10 AM
        tomorrow = datetime.now() + timedelta(days=1)
        date = tomorrow.strftime("%Y-%m-%d")
        time = "10:00 AM"

    appointment_id = f"A{random.randint(100,999)}"
    appointments[appointment_id] = {"vehicle": vehicle, "date": date, "time": time}

    return {
        "action": "book_appointment",
        "appointment_id": appointment_id,
        "vehicle": vehicle,
        "date": date,
        "time": time,
        "status": "booked"
    }


def cancel_appointment(appointment_id: str) -> dict:
    """
    Cancel an existing appointment.
    """
    if appointment_id in appointments:
        deleted = appointments.pop(appointment_id)
        return {
            "action": "cancel_appointment",
            "appointment_id": appointment_id,
            "vehicle": deleted["vehicle"],
            "date": deleted["date"],
            "time": deleted["time"],
            "status": "canceled"
        }
    return {"action": "cancel_appointment", "status": "not_found"}


def reschedule_appointment(appointment_id: str, new_date: str, new_time: str) -> dict:
    """
    Reschedule an existing appointment.
    """
    if appointment_id in appointments:
        appointments[appointment_id]["date"] = new_date
        appointments[appointment_id]["time"] = new_time
        return {
            "action": "reschedule_appointment",
            "appointment_id": appointment_id,
            "vehicle": appointments[appointment_id]["vehicle"],
            "date": new_date,
            "time": new_time,
            "status": "rescheduled"
        }
    return {"action": "reschedule_appointment", "status": "not_found"}


def check_appointment(appointment_id: str) -> dict:
    """
    Check details of an appointment.
    """
    if appointment_id in appointments:
        return {
            "action": "check_appointment",
            "appointment_id": appointment_id,
            "details": appointments[appointment_id],
            "status": "found"
        }
    return {"action": "check_appointment", "status": "not_found"}


# ---------------------------
# Router Function
# ---------------------------
def handle(query: str) -> dict:
    """
    Appointment Agent Tool Router.
    Maps queries to appointment functions.
    """
    query_lower = query.lower()

    if "book" in query_lower or "appointment" in query_lower:
        vehicle = "Unknown vehicle"
        if "civic" in query_lower:
            vehicle = "Honda Civic"
        elif "accord" in query_lower:
            vehicle = "Honda Accord"
        return book_appointment(vehicle)

    if "cancel" in query_lower:
        return {"action": "cancel_appointment", "message": "Please provide appointment ID to cancel."}

    if "reschedule" in query_lower:
        return {"action": "reschedule_appointment", "message": "Please provide appointment ID and new time."}

    if "check" in query_lower or "status" in query_lower:
        return {"action": "check_appointment", "message": "Please provide appointment ID to check status."}

    return {"action": "fallback", "message": "Sorry, I could not understand your appointment request."}
