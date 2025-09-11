# app/Agent/appointment/handler.py

from .tool import handle as appointment_router

def handle_appointment(query: str, session_id: str = None, conversation_history=None) -> str:
    """
    Handle appointment-related queries by routing them to appointment tools.
    Returns a user-friendly response string.
    """
    result = appointment_router(query)
    action = result.get("action")

    # ---- Book Appointment ----
    if action == "book_appointment":
        if "message" in result:  # Missing vehicle/service details
            return f"⚠️ {result['message']}"
        return (
            f"✅ Appointment booked successfully!\n"
            f"Appointment ID: {result['appointment_id']}\n"
            f"Vehicle: {result['vehicle']}\n"
            f"Date: {result['date']} at {result['time']}"
        )

    # ---- Cancel Appointment ----
    elif action == "cancel_appointment":
        if result.get("status") == "canceled":
            return (
                f"❌ Appointment {result['appointment_id']} for {result['vehicle']} "
                f"on {result['date']} at {result['time']} has been canceled."
            )
        elif "message" in result:
            return f"⚠️ {result['message']}"
        return "⚠️ Appointment cancellation failed. ID not found."

    # ---- Reschedule Appointment ----
    elif action == "reschedule_appointment":
        if result.get("status") == "rescheduled":
            return (
                f"🔄 Appointment {result['appointment_id']} has been rescheduled!\n"
                f"Vehicle: {result['vehicle']}\n"
                f"New Date: {result['date']} at {result['time']}"
            )
        elif "message" in result:
            return f"⚠️ {result['message']}"
        return "⚠️ Reschedule failed. Appointment not found."

    # ---- Check Appointment ----
    elif action == "check_appointment":
        if result.get("status") == "found":
            details = result["details"]
            return (
                f"🔎 Appointment {result['appointment_id']} Details:\n"
                f"- Vehicle: {details['vehicle']}\n"
                f"- Date: {details['date']}\n"
                f"- Time: {details['time']}"
            )
        elif "message" in result:
            return f"⚠️ {result['message']}"
        return "⚠️ Appointment not found. Please check the Appointment ID."

    # ---- Fallback ----
    elif action == "fallback":
        return "❓ Sorry, I couldn’t understand your appointment request. Could you rephrase?"

    else:
        return "⚠️ Something went wrong while processing your appointment request."
