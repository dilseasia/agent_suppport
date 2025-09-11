# app/Agent/appointment/schema.py

from typing import List, Dict, Any

tools: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "book_appointment",
            "description": "Book a new appointment for vehicle servicing.",
            "parameters": {
                "type": "object",
                "properties": {
                    "vehicle": {"type": "string", "description": "The vehicle for the appointment (e.g., Honda Civic)."},
                    "date": {"type": "string", "description": "The appointment date in YYYY-MM-DD format."},
                    "time": {"type": "string", "description": "The appointment time (e.g., 10:00 AM)."}
                },
                "required": ["vehicle"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_appointment",
            "description": "Cancel an existing appointment by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "string", "description": "The ID of the appointment (e.g., A101)."}
                },
                "required": ["appointment_id"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reschedule_appointment",
            "description": "Reschedule an existing appointment by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "string", "description": "The ID of the appointment (e.g., A102)."},
                    "new_date": {"type": "string", "description": "The new appointment date in YYYY-MM-DD format."},
                    "new_time": {"type": "string", "description": "The new appointment time (e.g., 3:00 PM)."}
                },
                "required": ["appointment_id", "new_date", "new_time"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_appointment",
            "description": "Check the details of an existing appointment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "string", "description": "The ID of the appointment (e.g., A103)."}
                },
                "required": ["appointment_id"]
            },
        },
    },
]
