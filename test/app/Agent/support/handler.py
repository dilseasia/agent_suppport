from .tool import handle as support_router

def handle_support(query: str, session_id: str = None, conversation_history=None) -> str:
    """
    Handle support-related queries by routing them to support tools.
    Returns a user-friendly response string.
    """
    result = support_router(query)

    action = result.get("action")

    # ---- Check Ticket Status ----
    if action == "check_ticket_status":
        status = result.get("status", "Unknown")
        return f"🔎 Ticket {result['ticket_id']} status: {status}"

    # ---- Create Ticket ----
    elif action == "create_ticket":
        return (
            f"✅ New support ticket created!\n"
            f"Ticket ID: {result['ticket_id']}\n"
            f"Issue: {result['issue']}\n"
            f"Priority: {result['priority'].capitalize()}"
        )

    # ---- Escalate Ticket ----
    elif action == "escalate_ticket":
        return (
            f"⚠️ Ticket {result['ticket_id']} has been escalated "
            f"to {result['escalated_to']} team."
        )

    # ---- FAQs ----
    elif action == "get_faq":
        topic = result.get("topic") or "general"
        answer = result.get("answer")
        return f"📘 FAQ - {topic.capitalize()}:\n{answer}"

    # ---- Fallback ----
    elif action == "fallback":
        return "❓ Sorry, I couldn’t understand that. Could you rephrase?"

    else:
        return "⚠️ Something went wrong while processing your support request."
