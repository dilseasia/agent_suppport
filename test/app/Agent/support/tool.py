# app/Agent/support/tool.py

import re
import random

# ---------------------------
# Support Tool Functions
# ---------------------------

def check_ticket_status(ticket_id: str) -> dict:
    """
    Simulate checking the status of a support ticket.
    """
    fake_status = {
        "T123": "Open - waiting for customer",
        "T124": "In Progress - assigned to technician",
        "T125": "Resolved - closed",
    }
    status = fake_status.get(ticket_id, "Ticket not found")

    return {"action": "check_ticket_status", "ticket_id": ticket_id, "status": status}


def create_ticket(issue: str, priority: str = "medium") -> dict:
    """
    Simulate creating a new support ticket.
    """
    ticket_id = f"T{random.randint(100,999)}"

    return {
        "action": "create_ticket",
        "ticket_id": ticket_id,
        "issue": issue,
        "priority": priority,
        "status": "created"
    }


def escalate_ticket(ticket_id: str, level: str = "L2") -> dict:
    """
    Simulate escalating a support ticket.
    """
    return {
        "action": "escalate_ticket",
        "ticket_id": ticket_id,
        "escalated_to": level,
        "status": "escalated"
    }


def get_faq(topic: str = None) -> dict:
    """
    Return FAQs or knowledge base entries.
    """
    faqs = {
        "appointment": "You can book, reschedule, or cancel appointments directly with our support agent.",
        "dealership": "Find dealership details by providing the dealership ID (e.g., NYC01, LA01).",
        "services": "We offer maintenance, repairs, inspections, and more. Ask for a full list of services.",
    }

    if topic:
        answer = faqs.get(topic.lower(), "No FAQ found for this topic.")
    else:
        answer = faqs

    return {"action": "get_faq", "topic": topic, "answer": answer}


# ---------------------------
# Router Function
# ---------------------------
def handle(query: str) -> dict:
    """
    Support Agent Tool Router.
    Takes a user query and decides which function to call.
    """

    query_lower = query.lower()

    # --- Check Ticket Status ---
    match = re.search(r"(ticket\s*#?\s*(\w+))|(status\s*of\s*ticket\s*(\w+))", query_lower)
    if match:
        ticket_id = match.group(2) or match.group(4)
        return check_ticket_status(ticket_id)

    # --- Create Ticket ---
    if "create ticket" in query_lower or "new ticket" in query_lower or "raise issue" in query_lower:
        # Extract priority if mentioned
        if "high" in query_lower:
            priority = "high"
        elif "low" in query_lower:
            priority = "low"
        else:
            priority = "medium"
        return create_ticket(issue=query, priority=priority)

    # --- Escalate Ticket ---
    if "escalate" in query_lower:
        match = re.search(r"ticket\s*#?\s*(\w+)", query_lower)
        ticket_id = match.group(1) if match else "Unknown"
        return escalate_ticket(ticket_id)

    # --- FAQs ---
    if "faq" in query_lower or "help" in query_lower or "support" in query_lower:
        # Extract topic keyword
        if "appointment" in query_lower:
            return get_faq("appointment")
        elif "dealership" in query_lower:
            return get_faq("dealership")
        elif "service" in query_lower:
            return get_faq("services")
        else:
            return get_faq()

    # --- Default Fallback ---
    return {"action": "fallback", "message": "Sorry, I could not understand your request."}
