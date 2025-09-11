# import os
# import logging
# import json
# from fastapi import APIRouter
# from dotenv import load_dotenv
# from sse_starlette.sse import EventSourceResponse
# from app.models.model import QueryRequest, ToolResponse
# from app.services.llm import GroqLLMClient
# from typing import Dict, List
# from app.utils.stream import stream_response
# from app.services.tools import weather, dealership, appointment


# # Load environment variables
# load_dotenv()

# # Configure logging
# logging.basicConfig(
#     level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper()),
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )

# # Initialize logger
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


# chatbot_route = APIRouter()


# # Map tool name to actual tool function
# available_functions= {
#     "get_weather": weather.get_weather,
#     "get_dealership_address": dealership.get_dealership_address,
#     "check_appointment_availability": appointment.check_appointment_availability,
#     "schedule_appointment": appointment.schedule_appointment
# }




# @chatbot_route.get("/")
# def healthcheck():
#     """Health check endpoint."""
#     return {
#         "status": "OK",
#         "message": "SuperCar Virtual Sales Assistant API is running! Replace this with your implementation."
#     } 


# # In-memory session storage (replace with Redis/database in production)
# session_storage: Dict[str, List[Dict[str, str]]] = {}

# @chatbot_route.post("/query")
# async def process_query(request: QueryRequest):
#     """
#     Main query endpoint that streams responses using Server-Sent Events
#     """
#     logger.info(f"Received query request: {request.query} (Session ID: {request.session_id})")
    
#     # Initialize Groq client
#     groq_client = GroqLLMClient()
#     logger.warning("cheking session_storage")
#     logger.warning(session_storage)
    
#     # Retrieve or initialize conversation history
#     conversation_history = session_storage.get(
#         request.session_id, 
#         [{"role": "system", "content": "You are a helpful sales assistant for SuperCar dealerships. you should know to call the tools or use"}]
#     )
#     logger.info(f"Conversation history retrieved for session {request.session_id}")

#     # Limit conversation history to prevent excessive memory usage
#     MAX_HISTORY_LENGTH = 10
#     if len(conversation_history) > MAX_HISTORY_LENGTH:
#         # Keep the system message and the most recent messages
#         conversation_history = [conversation_history[0]] + conversation_history[-MAX_HISTORY_LENGTH:]
    
#     # Add user's current query to conversation history
#     conversation_history.append({
#         "role": "user", 
#         "content": request.query
#     })
#     session_storage[request.session_id] = conversation_history
#     # logger.info(f"User query appended to conversation history: {request.query}")

#     # Define available tools (same as before)
#     tools = [
#         {
#             "type": "function",
#             "function": {
#                 "name": "get_weather",
#                 "description": "Get current weather for a city",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "city": {"type": "string"}
#                     },
#                     "required": ["city"]
#                 }
#             }
#         },
#         {
#             "type": "function",
#             "function": {
#                 "name": "get_dealership_address",
#                 "description": "Retrieve dealership address and details",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "dealership_id": {"type": "string"}
#                     },
#                     "required": ["dealership_id"]
#                 }
#             }
#         },
#         {
#             "type": "function",
#             "function": {
#                 "name": "check_appointment_availability",
#                 "description": "Check available appointment slots for a dealership on a specific date",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "dealership_id": {"type": "string"},
#                         "date": {"type": "string"}
#                     },
#                     "required": ["dealership_id", "date"]
#                 }
#             }
#         },
#         {
#             "type": "function",
#             "function": {
#                 "name": "schedule_appointment",
#                 "description": "Schedule an appointment at a SuperCar dealership",
#                 "parameters": {
#                     "type": "object",
#                     "properties": {
#                         "user_id": {"type": "string"},
#                         "dealership_id": {"type": "string"},
#                         "date": {"type": "string"},
#                         "time": {"type": "string"},
#                         "car_model": {"type": "string"}
#                     },
#                     "required": ["user_id", "dealership_id", "date", "time", "car_model"]
#                 }
#             }
#         }
#     ]
    
#     async def event_generator():
#         try:
#             logger.info("Calling Groq API for response generation...")
#             # Call Groq API
#             response = groq_client.generate_response(
#                 messages=conversation_history,
#                 tools=tools
#             )
            
#             if not response:
#                 logger.error("Failed to generate response from Groq API")
#                 yield {"event": "error", "data": "Failed to generate response"}
#                 return
            
#             response_message = response.choices[0].message
#             tool_calls = response_message.tool_calls

#             # If no tool calls, return direct response
#             if not tool_calls:
#                 full_response = response_message.content
#                 yield {"event": "chunk", "data": full_response}

#                 # Add assistant's response to conversation history
#                 conversation_history.append({
#                     "role": "assistant", 
#                     "content": full_response
#                 })
                
#                 # Update session storage
#                 session_storage[request.session_id] = conversation_history
#                 return
            
#             else:
           
#                 for tool_call in tool_calls:
#                     function_name = tool_call.function.name
#                     function_to_call = available_functions.get(function_name)
#                     function_args = json.loads(tool_call.function.arguments)
#                     logging.warning("function_args")
#                     logging.warning(function_args)

#                     # Call the function and get the response
#                     function_response = function_to_call(**function_args)
#                     logging.warning("function_response")
#                     logging.warning(function_response)

#                     final_response = groq_client.final_response(user_query=request.query, function_response=f"{function_response}")
#                     logger.warning("checking final response")
#                     logger.warning(final_response)

#                     data = {"name": function_name, "output": function_response, "message":final_response.content}
#                     yield {"event": "tool_output", "data":json.dumps(data)}

#                      # Update conversation history with tool call and response
#                     conversation_history.extend([
#                         {
#                             "role": "tool", 
#                             "name": function_name,
#                             "content": f"Function {function_name} returned: {function_response}"
#                         },
#                         {
#                             "role": "assistant", 
#                             "content": final_response.content
#                         }
#                     ])

#                     # Update session storage
#                     session_storage[request.session_id] = conversation_history
#                     return
            
#         except Exception as e:
#             logger.exception("Error occurred while processing query")
#             yield {"event": "error", "data": str(e)}
    
#     return EventSourceResponse(event_generator())




########################################

import os
import logging
import json
from fastapi import APIRouter
from dotenv import load_dotenv
from sse_starlette.sse import EventSourceResponse
from app.models.model import QueryRequest
from app.services.llm import GroqLLMClient
from typing import Dict, List
from app.services.tools import weather, dealership, appointment
from app.Agent.classifier import classify_query_with_gemini


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)



available_agents = {
    # "greeting": greeting.handle_greeting,  # For greeting-related queries
    # "support": support.handle_support,  # For support-related queries
    "appointment": appointment.handle_appointment,  # For appointment-related queries
    # "estimate": estimate.handle_estimate,  # For estimate-related queries
    # "information": information.handle_information,  # For information-related queries
    "general": None  # In case no relevant agent is found
}


# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

chatbot_route = APIRouter()

# Map tool name to actual tool function
available_functions = {
    "get_weather": weather.get_weather,
    "get_dealership_address": dealership.get_dealership_address,
    "check_appointment_availability": appointment.check_appointment_availability,
    "schedule_appointment": appointment.schedule_appointment
}

def get_system_message_for_intent(intent: str) -> str:
    """
    Return intent-specific system messages for better contextual responses
    """
    system_messages = {
        "greeting": "You are Lex, a friendly and professional sales assistant for SuperCar dealerships. Respond warmly to greetings and offer assistance with car sales, appointments, or information.",
        "support": "You are Lex, a helpful technical support assistant for SuperCar dealerships. Focus on solving problems, troubleshooting issues, and providing clear solutions. Be patient and thorough in your assistance.",
        "appointment": "You are Lex, a scheduling specialist for SuperCar dealerships. Help customers book appointments, check availability, and manage their service needs. Use the appointment tools when needed.",
        "estimate": "You are Lex, a pricing specialist for SuperCar dealerships. Provide accurate cost estimates, explain pricing structures, and help customers understand the value of our services and vehicles.",
        "information": "You are Lex, an information specialist for SuperCar dealerships. Provide detailed, accurate information about our vehicles, services, policies, and procedures. Be comprehensive and helpful.",
        "general": "You are Lex, a knowledgeable sales assistant for SuperCar dealerships. Assist with any questions about our luxury vehicles, services, appointments, or general inquiries. Use available tools when appropriate."
    }
    return system_messages.get(intent, system_messages["general"])

@chatbot_route.get("/")
def healthcheck():
    """Health check endpoint."""
    return {
        "status": "OK",
        "message": "SuperCar Virtual Sales Assistant API is running! Replace this with your implementation."
    }

# In-memory session storage (replace with Redis/database in production)
session_storage: Dict[str, List[Dict[str, str]]] = {}

@chatbot_route.post("/query")
async def process_query(request: QueryRequest):
    """
    Main query endpoint that streams responses using Server-Sent Events
    First classifies the query, then provides appropriate response
    """
    logger.info(f"Received query request: {request.query} (Session ID: {request.session_id})")

    # Step 1: Classify the query using Gemini classifier
    try:
        classification_result = classify_query_with_gemini(request.query)
        logger.info(f"Query classification: {classification_result}")

        # Extract classification info
        primary_intent = classification_result.get("primary_intent", "general")
        corrected_query = classification_result.get("corrected_query", request.query)
        out_of_context = classification_result.get("out_of_context", False)
        intent_scores = classification_result.get("intent", {})

        logger.info(f"Primary intent: {primary_intent}, Out of context: {out_of_context}")

    except Exception as e:
        logger.error(f"Classification failed: {str(e)}")
        # Fallback to general intent if classification fails
        primary_intent = "general"
        corrected_query = request.query
        out_of_context = False
        intent_scores = {}

    # Initialize Groq client
    groq_client = GroqLLMClient()
    logger.warning("checking session_storage")
    logger.warning(session_storage)

    # Retrieve or initialize conversation history with intent-aware system message
    system_message = get_system_message_for_intent(primary_intent)
    conversation_history = session_storage.get(
        request.session_id,
        [{"role": "system", "content": system_message}]
    )
    logger.info(f"Conversation history retrieved for session {request.session_id}")

    # Limit conversation history to prevent excessive memory usage
    MAX_HISTORY_LENGTH = 10
    if len(conversation_history) > MAX_HISTORY_LENGTH:
        # Keep the system message and the most recent messages
        conversation_history = [conversation_history[0]] + conversation_history[-MAX_HISTORY_LENGTH:]

    # Add classification context and user's query to conversation history
    classification_context = f"[Intent: {primary_intent}, Confidence: {intent_scores.get(primary_intent, 0.0):.2f}]"
    conversation_history.append({
        "role": "user",
        "content": f"{classification_context} {corrected_query}"
    })
    session_storage[request.session_id] = conversation_history

    # Define available tools (same as before)
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get current weather for a city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"}
                    },
                    "required": ["city"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_dealership_address",
                "description": "Retrieve dealership address and details",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dealership_id": {"type": "string"}
                    },
                    "required": ["dealership_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_appointment_availability",
                "description": "Check available appointment slots for a dealership on a specific date",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dealership_id": {"type": "string"},
                        "date": {"type": "string"}
                    },
                    "required": ["dealership_id", "date"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "schedule_appointment",
                "description": "Schedule an appointment at a SuperCar dealership",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "dealership_id": {"type": "string"},
                        "date": {"type": "string"},
                        "time": {"type": "string"},
                        "car_model": {"type": "string"}
                    },
                    "required": ["user_id", "dealership_id", "date", "time", "car_model"]
                }
            }
        }
    ]
    
    async def event_generator():
        try:
            # First, yield classification information
            yield {
                "event": "classification",
                "data": json.dumps({
                    "primary_intent": primary_intent,
                    "intent_scores": intent_scores,
                    "out_of_context": out_of_context,
                    "corrected_query": corrected_query
                })
            }

            # Handle out-of-context queries
            if out_of_context:
                out_of_context_response = (
                    "I'm Lex, your SuperCar dealership assistant. I'm here to help with "
                    "car sales, appointments, service information, and dealership inquiries. "
                    "Could you please rephrase your question related to our automotive services?"
                )
                yield {"event": "chunk", "data": out_of_context_response}

                # Add to conversation history
                conversation_history.append({
                    "role": "assistant",
                    "content": out_of_context_response
                })
                session_storage[request.session_id] = conversation_history
                return

            # Determine the agent with the highest score based on the classification
            highest_intent = max(intent_scores, key=intent_scores.get)
            logger.info(f"Highest intent based on scores: {highest_intent}")

            # Get the corresponding agent function for the highest intent
            agent_function = available_agents.get(highest_intent)

            # If we found an agent for the highest intent
            if agent_function:
                # Call the corresponding agent function (each agent handles its own query type)
                response = agent_function(request.query)
                yield {"event": "chunk", "data": response}

                # Add assistant's response to conversation history
                conversation_history.append({
                    "role": "assistant",
                    "content": response
                })

                # Update session storage
                session_storage[request.session_id] = conversation_history
                return

            else:
                # Handle the case where no matching agent was found
                no_matching_agent_response = "I'm sorry, I couldn't find an appropriate response for your query."
                yield {"event": "chunk", "data": no_matching_agent_response}

                # Add to conversation history
                conversation_history.append({
                    "role": "assistant",
                    "content": no_matching_agent_response
                })
                session_storage[request.session_id] = conversation_history
                return

        except Exception as e:
            logger.exception("Error occurred while processing query")
            yield {"event": "error", "data": str(e)}
    
    return EventSourceResponse(event_generator())
