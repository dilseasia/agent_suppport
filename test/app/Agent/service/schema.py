# app/Agent/service/schema.py

from typing import List, Dict, Any

tools: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "list_services",
            "description": "List all available vehicle services.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_service",
            "description": "Book a new vehicle service appointment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {"type": "string", "description": "The service to book (e.g., Oil & Filter Change)."},
                    "date": {"type": "string", "description": "Service date in YYYY-MM-DD format."},
                    "time": {"type": "string", "description": "Service time (e.g., 9:00 AM)."}
                },
                "required": ["service"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_service",
            "description": "Cancel a booked service by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {"type": "string", "description": "The ID of the booked service (e.g., S123)."}
                },
                "required": ["service_id"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_service",
            "description": "Check the details of a booked service by ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {"type": "string", "description": "The ID of the booked service (e.g., S124)."}
                },
                "required": ["service_id"]
            },
        },
    },
]
