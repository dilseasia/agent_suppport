# app/Agent/service/tool.py

import random
from datetime import datetime, timedelta

# In-memory "database" of service bookings
services = {}

def list_services() -> dict:
    """
    Return a list of available services.
    """
    available_services = [
        "Oil & Filter Change",
        "Brake Inspection & Repair",
        "Transmission Service",
        "Engine Diagnostics",
        "Tire Rotation & Alignment",
        "Battery & Electrical Check",
        "Detailing & Wash",
        "Air-Conditioning Service",
        "Scheduled Maintenance Packages",
    ]
    return {"action": "list_services", "services": available_services}


def book_service(service: str, date: str = None, time: str = None) -> dict:
    """
    Book a service. If no date/time provided, book earliest available slot.
    """
    if not date or not time:
        tomorrow = datetime.now() + timedelta(days=1)
        date = tomorrow.strftime("%Y-%m-%d")
        time = "9:00 AM"

    service_id = f"S{random.randint(100,999)}"
    services[service_id] = {"service": service, "date": date, "time": time}

    return {
        "action": "book_service",
        "service_id": service_id,
        "service": service,
        "date": date,
        "time": time,
        "status": "booked"
    }


def cancel_service(service_id: str) -> dict:
    """
    Cancel a booked service.
    """
    if service_id in services:
        deleted = services.pop(service_id)
        return {
            "action": "cancel_service",
            "service_id": service_id,
            "service": deleted["service"],
            "date": deleted["date"],
            "time": deleted["time"],
            "status": "canceled"
        }
    return {"action": "cancel_service", "status": "not_found"}


def check_service(service_id: str) -> dict:
    """
    Check details of a booked service.
    """
    if service_id in services:
        return {
            "action": "check_service",
            "service_id": service_id,
            "details": services[service_id],
            "status": "found"
        }
    return {"action": "check_service", "status": "not_found"}


# ---------------------------
# Router Function
# ---------------------------
def handle(query: str) -> dict:
    """
    Service Agent Tool Router.
    Maps user queries to service functions.
    """
    query_lower = query.lower()

    if "list services" in query_lower or "available services" in query_lower:
        return list_services()

    if "book" in query_lower or "service" in query_lower:
        # crude example: pick service from query
        if "oil" in query_lower:
            return book_service("Oil & Filter Change")
        elif "brake" in query_lower:
            return book_service("Brake Inspection & Repair")
        elif "diagnostic" in query_lower:
            return book_service("Engine Diagnostics")
        else:
            return {"action": "book_service", "message": "Please specify which service to book."}

    if "cancel" in query_lower:
        return {"action": "cancel_service", "message": "Please provide service ID to cancel."}

    if "check" in query_lower or "status" in query_lower:
        return {"action": "check_service", "message": "Please provide service ID to check status."}

    return {"action": "fallback", "message": "Sorry, I didn’t understand your service request."}
