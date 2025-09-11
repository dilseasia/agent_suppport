# app/Agent/service/handler.py

from .tool import handle as service_router

def handle_service(query: str, session_id: str = None, conversation_history=None) -> str:
    """
    Handle service-related queries by routing them to service tools.
    Returns a user-friendly response string.
    """
    result = service_router(query)
    action = result.get("action")

    # ---- List Services ----
    if action == "list_services":
        services = result.get("services", [])
        services_list = "\n".join([f"- {s}" for s in services])
        return f"🛠️ Available Services:\n{services_list}"

    # ---- Book Service ----
    elif action == "book_service":
        if "message" in result:  # Missing service specification
            return f"⚠️ {result['message']}"
        return (
            f"✅ Service booked successfully!\n"
            f"Service ID: {result['service_id']}\n"
            f"Service: {result['service']}\n"
            f"Date: {result['date']} at {result['time']}"
        )

    # ---- Cancel Service ----
    elif action == "cancel_service":
        if result.get("status") == "canceled":
            return (
                f"❌ Service {result['service_id']} ({result['service']}) "
                f"scheduled on {result['date']} at {result['time']} has been canceled."
            )
        elif "message" in result:
            return f"⚠️ {result['message']}"
        return f"⚠️ Service cancellation failed. ID not found."

    # ---- Check Service ----
    elif action == "check_service":
        if result.get("status") == "found":
            details = result["details"]
            return (
                f"🔎 Service {result['service_id']} Details:\n"
                f"- Service: {details['service']}\n"
                f"- Date: {details['date']}\n"
                f"- Time: {details['time']}"
            )
        elif "message" in result:
            return f"⚠️ {result['message']}"
        return f"⚠️ Service not found. Please check the Service ID."

    # ---- Fallback ----
    elif action == "fallback":
        return "❓ Sorry, I couldn’t understand your service request. Could you rephrase?"

    else:
        return "⚠️ Something went wrong while processing your service request."
