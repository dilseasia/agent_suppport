import os
import logging
import json
from fastapi import APIRouter
from dotenv import load_dotenv
from sse_starlette.sse import EventSourceResponse
from typing import Dict, List

from app.models.model import QueryRequest
from app.services.llm import GroqLLMClient
from app.Agent.appointment import tool as appointment_tool, schema as appointment_schema
from app.Agent.service import tool as service_tool, schema as service_schema
from app.Agent.support import tool as support_tool, schema as support_schema
from app.services.tools import weather, dealership
from app.Agent.classifier import classify_query_with_gemini

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
chatbot_route = APIRouter()

# -------------------------------
# Tool Registry
# -------------------------------
available_functions = {
    "get_weather": weather.get_weather,
    "get_dealership_address": dealership.get_dealership_address,

    # Appointment
    "book_appointment": appointment_tool.book_appointment,
    "cancel_appointment": appointment_tool.cancel_appointment,
    "reschedule_appointment": appointment_tool.reschedule_appointment,
    "check_appointment": appointment_tool.check_appointment,

    # Service
    "list_services": service_tool.list_services,
    "book_service": service_tool.book_service,
    "check_service": service_tool.check_service,
    "cancel_service": service_tool.cancel_service,

    # Support
    "check_ticket_status": support_tool.check_ticket_status,
    "create_ticket": support_tool.create_ticket,
    "escalate_ticket": support_tool.escalate_ticket,
    "get_faq": support_tool.get_faq,
}

# Merge schema tools
tools = [
    *appointment_schema.tools,
    *service_schema.tools,
    *support_schema.tools,
]

# -------------------------------
# System message for intents
# -------------------------------
def get_system_message_for_intent(intent: str) -> str:
    messages = {
        "appointment": (
            "You are Lex, a smart appointment assistant for a luxury car dealership. "
            "Help the user book, cancel, reschedule, or check appointments efficiently."
        ),
        "service": (
            "You are Lex, a service assistant for a luxury car dealership. "
            "Help the user book, check, or cancel car services."
        ),
        "support": (
            "You are Lex, a support assistant for a luxury car dealership. "
            "Help the user check ticket status, create tickets, escalate issues, and answer FAQs."
        ),
        "general": (
            "You are Lex, a friendly AI assistant for a luxury car dealership. "
            "You can help with general questions about cars, dealership locations, and services."
        ),
    }
    return messages.get(intent, messages["general"])

# -------------------------------
# In-memory session storage
# -------------------------------
session_storage: Dict[str, List[Dict[str, str]]] = {}

# -------------------------------
# Query Endpoint
# -------------------------------
@chatbot_route.post("/query")
async def process_query(request: QueryRequest):
    logger.info(f"Received query: {request.query} (Session ID: {request.session_id})")

    # ---------------------------
    # Step 1: Classification (Gemini first, Groq fallback)
    # ---------------------------
    try:
        classification_result = classify_query_with_gemini(request.query)
        logger.info(f"Classification (Gemini): {classification_result}")
    except Exception as e:
        logger.warning(f"Gemini classification failed: {e}")
        logger.info("Falling back to Groq classifier...")
        try:
            groq_client = GroqLLMClient()
            prompt = f"""
            Classify the following query into one of these intents: 
            appointment, service, support, general.
            Query: "{request.query}"
            Respond in JSON format: {{ "primary_intent": "<intent>", "corrected_query": "<maybe corrected query>" }}
            """
            response = groq_client.generate_response(messages=[{"role": "user", "content": prompt}])
            classification_json = json.loads(response.choices[0].message.content)
            classification_result = classification_json
            logger.info(f"Classification (Groq fallback): {classification_result}")
        except Exception as ge:
            logger.error(f"Groq fallback failed: {ge}")
            classification_result = {
                "primary_intent": "general",
                "corrected_query": request.query,
                "out_of_context": False,
                "intent": {"general": 1.0},
            }

    primary_intent = classification_result.get("primary_intent", "general").lower()
    corrected_query = classification_result.get("corrected_query", request.query)
    out_of_context = classification_result.get("out_of_context", False)
    intent_scores = classification_result.get("intent", {})

    # ---------------------------
    # Step 2: Prepare conversation history
    # ---------------------------
    system_message = get_system_message_for_intent(primary_intent)
    conversation_history = session_storage.get(
        request.session_id, [{"role": "system", "content": system_message}]
    )

    MAX_HISTORY_LENGTH = 10
    if len(conversation_history) > MAX_HISTORY_LENGTH:
        conversation_history = [conversation_history[0]] + conversation_history[-MAX_HISTORY_LENGTH:]

    classification_context = f"[Intent: {primary_intent}, Confidence: {intent_scores.get(primary_intent, 0.0):.2f}]"
    conversation_history.append({"role": "user", "content": f"{classification_context} {corrected_query}"})
    session_storage[request.session_id] = conversation_history

    # ---------------------------
    # Step 3: Response Generation
    # ---------------------------
    groq_client = GroqLLMClient()

    async def event_generator():
        try:
            # Send classification info
            yield {
                "event": "classification",
                "data": json.dumps({
                    "primary_intent": primary_intent,
                    "intent_scores": intent_scores,
                    "out_of_context": out_of_context,
                    "corrected_query": corrected_query,
                }),
            }

            # Handle out-of-context queries
            if out_of_context:
                out_response = (
                    "I'm Lex, your SuperCar dealership assistant. 🚗 "
                    "I can help with car sales, appointments, service, and support. "
                    "Could you rephrase your question related to these topics?"
                )
                yield {"event": "chunk", "data": out_response}
                conversation_history.append({"role": "assistant", "content": out_response})
                session_storage[request.session_id] = conversation_history
                return

            # ---------------------------
            # Tool Path (appointment/service/support)
            # ---------------------------
            response = groq_client.generate_response(messages=conversation_history, tools=tools)
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls or []

            # ---------------------------
            # Force tool execution if no tool_calls
            # ---------------------------
            if not tool_calls:
                logger.info("Forcing tool execution based on intent...")
                if primary_intent in ["appointment", "appointment_agent"]:
                    tool_name = "book_appointment"
                elif primary_intent in ["service", "service_agent"]:
                    tool_name = "list_services"
                elif primary_intent in ["support", "support_agent"]:
                    tool_name = "check_ticket_status"
                else:
                    tool_name = None

                if tool_name:
                    tool_func = available_functions.get(tool_name)
                    if tool_func:
                        tool_response = tool_func()
                        final_response = groq_client.final_response(
                            user_query=request.query,
                            function_response=json.dumps(tool_response)
                        )
                        data = {
                            "name": tool_name,
                            "output": tool_response,
                            "message": final_response.content,
                        }
                        yield {"event": "tool_output", "data": json.dumps(data)}
                        conversation_history.extend([
                            {"role": "tool", "name": tool_name, "content": str(tool_response)},
                            {"role": "assistant", "content": final_response.content},
                        ])
                        session_storage[request.session_id] = conversation_history
                        return

            # ---------------------------
            # Normal response path
            # ---------------------------
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions.get(function_name)
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(**function_args)
                final_response = groq_client.final_response(
                    user_query=request.query,
                    function_response=json.dumps(function_response)
                )
                data = {
                    "name": function_name,
                    "output": function_response,
                    "message": final_response.content,
                }
                yield {"event": "tool_output", "data": json.dumps(data)}
                conversation_history.extend([
                    {"role": "tool", "name": function_name, "content": str(function_response)},
                    {"role": "assistant", "content": final_response.content},
                ])
                session_storage[request.session_id] = conversation_history

            # ---------------------------
            # General path if still no response
            # ---------------------------
            if not tool_calls and primary_intent not in ["appointment", "appointment_agent", "service", "service_agent", "support", "support_agent"]:
                llm_output = response_message.content
                yield {"event": "chunk", "data": llm_output}
                conversation_history.append({"role": "assistant", "content": llm_output})
                session_storage[request.session_id] = conversation_history

        except Exception as e:
            logger.exception("Error while processing query")
            yield {"event": "error", "data": str(e)}

    return EventSourceResponse(event_generator())
