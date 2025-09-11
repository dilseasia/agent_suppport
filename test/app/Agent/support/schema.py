# app/Agent/support/schema.py

from typing import List, Dict, Any

# ---------------------------
# Tool Schemas for Support Agent
# ---------------------------

tools: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "check_ticket_status",
            "description": "Check the status of an existing support ticket by ticket ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "The ID of the ticket (e.g., T123)."
                    }
                },
                "required": ["ticket_id"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_ticket",
            "description": "Create a new support ticket for an issue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue": {
                        "type": "string",
                        "description": "Description of the issue reported by the user."
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "The priority of the ticket. Defaults to medium."
                    }
                },
                "required": ["issue"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_ticket",
            "description": "Escalate an existing support ticket to a higher level (e.g., L2, L3).",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {
                        "type": "string",
                        "description": "The ID of the ticket (e.g., T124)."
                    },
                    "level": {
                        "type": "string",
                        "enum": ["L1", "L2", "L3"],
                        "description": "The escalation level. Defaults to L2."
                    }
                },
                "required": ["ticket_id"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_faq",
            "description": "Retrieve FAQ information about services, dealership, or appointments.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic to search FAQs for (e.g., appointment, dealership, services). Optional."
                    }
                },
                "required": []
            },
        },
    },
]
