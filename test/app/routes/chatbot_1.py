import os
import logging
import json
import re
from fastapi import APIRouter
from dotenv import load_dotenv
from sse_starlette.sse import EventSourceResponse
from app.models.model import QueryRequest, ToolResponse
from app.services.llm import GroqLLMClient
from typing import Dict, List
from app.utils.stream import stream_response
from app.services.tools import weather, dealership, appointment
# from app.config.prompt import prompt
# from app.config.sample_data import final_prompt


# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


chatbot_route = APIRouter()


# Map tool name to actual tool function
available_functions= {
    "get_weather": weather.get_weather,
    "get_dealership_address": dealership.get_dealership_address,
    "check_appointment_availability": appointment.check_appointment_availability,
    "schedule_appointment": appointment.schedule_appointment
}




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
    """
    logger.info(f"Received query request: {request.query} (Session ID: {request.session_id})")
    

    # Initialize Groq client
    groq_client = GroqLLMClient()
    logger.warning("checking session_storage")
    logger.warning(session_storage)
    
    # Retrieve or initialize conversation history
    conversation_history = session_storage.get(
        request.session_id, 
        [{"role": "system", "content": "You are a helpful sales assistant for SuperCar dealerships. you should know to call the tools or use"}]
    )
    logger.info(f"Conversation history retrieved for session {request.session_id}")

    # Limit conversation history to prevent excessive memory usage
    MAX_HISTORY_LENGTH = 10
    if len(conversation_history) > MAX_HISTORY_LENGTH:
        # Keep the system message and the most recent messages
        conversation_history = [conversation_history[0]] + conversation_history[-MAX_HISTORY_LENGTH:]
    
    # Add user's current query to conversation history
    conversation_history.append({
        "role": "user", 
        "content": request.query
    })
    session_storage[request.session_id] = conversation_history
    # logger.info(f"User query appended to conversation history: {request.query}")

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
        # {
        #     "type": "function",
        #     "function": {
        #         "name": "knowledge_base",
        #         "description": "You are an AI Sales Assistant for SuperCar Dealerships, designed to provide comprehensive, helpful, and professional automotive support. Based on user query decide that you need to use tool or you need to look your knowledge_base documents",
        #         "parameters": {
        #             "type": "object",
        #             "properties": {
        #             },
        #             "required": []
        #         }
        #     }
        # }
    ]
    
    async def event_generator():
        try:
            # Check if user wants to end the conversation
            if request.query.lower().strip() in ["end conversation", "exit", "quit", "goodbye", "bye"]:
                # Clear the session from storage if user wants to end
                if request.session_id in session_storage:
                    del session_storage[request.session_id]
                logger.info(f"Ending conversation for session {request.session_id}")
                yield {"event": "chunk", "data": "I am glad i could help you"}
                # yield {"event": "end", "data":None}
                return 
            
            logger.info("Calling Groq API for response generation...")
            # Call Groq API
            response = groq_client.generate_response(
                messages=conversation_history,
                tools=tools
            )
            
            if not response:
                logger.error("Failed to generate response from Groq API")
                yield {"event": "error", "data": "Failed to generate response"}
                return
            
            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # If no tool calls, return direct response
            if not tool_calls:
                logger.info("checking chunk event")
                full_response = response_message.content
                yield {"event": "chunk", "data": full_response}

                # Add assistant's response to conversation history
                conversation_history.append({
                    "role": "assistant", 
                    "content": full_response
                })
                
                # Update session storage
                session_storage[request.session_id] = conversation_history
                return
            
            if tool_calls:
                logger.info("I am in tools call")
                for tool_call in tool_calls:
                    function_name = tool_call.function.name

                    # Validate function exists
                    if function_name not in available_functions:
                        # error_msg = f"Requested function {function_name} is not available"
                        # logger.error(error_msg)
                        # yield {"event": "chunk", "data":"your query is out of context"}
                        # return
                        knowledge_base_response  = groq_client.knowledge_base_response(user_query=request.query)

                        match = re.search(r"\{(.*?)\}", knowledge_base_response)
                        if match:
                            gpt_response = match.group(1)
                            if gpt_response:
                                gpt_response = gpt_response.replace("```json", "")
                                gpt_response = gpt_response.replace("```", "")
                                gpt_response = gpt_response.strip()
                                response_data = json.loads(gpt_response)
                                result = response_data.get("response")
                                yield {"event": "chunk", "data":result}
                                return
                        yield {"event": "chunk", "data":knowledge_base_response.content}
                        return


                    
                    function_to_call = available_functions.get(function_name)
                    function_args = json.loads(tool_call.function.arguments)
                    logging.warning("function_args")
                    logging.warning(function_args)


                    # Validate required parameters
                    required_params = []
                    for tool in tools:
                        if tool["type"] == "function" and tool["function"]["name"] == function_name:
                            required_params = tool["function"]["parameters"].get("required", [])
                            break


                    missing_params = [param for param in required_params if param not in function_args or not function_args[param]]
                    if missing_params:
                        error_msg = f"Missing required parameters for function '{function_name}': {', '.join(missing_params)}"
                        logger.error(error_msg)
                        
                        # Handle missing parameters by requesting them from the user
                        missing_params_response = f"I need more information to help you. Please provide: {', '.join(missing_params)}"
                        yield {"event": "chunk", "data": missing_params_response}
                        
                        # Add to conversation history
                        conversation_history.append({
                            "role": "assistant",
                            "content": missing_params_response
                        })
                        
                        # Update session storage and return
                        session_storage[request.session_id] = conversation_history
                        return
                    

                    # Call the function and get the response
                    function_response = function_to_call(**function_args)
                    logging.warning("function_response")
                    logging.warning(function_response)

                    final_response = groq_client.final_response(user_query=request.query, function_response=f"{function_response}")
                    logger.warning("checking final response")
                    logger.warning(final_response)

                    data = {"name": function_name, "output": function_response, "message":final_response.content}
                    yield {"event": "tool_output", "data":json.dumps(data)}

                     # Update conversation history with tool call and response
                    conversation_history.extend([
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool", 
                            "name": function_name,
                            "content": f"Function {function_name} returned: {function_response}"
                        },
                        {
                            "role": "assistant", 
                            "content": final_response.content
                        }
                    ])

                    # Update session storage
                    session_storage[request.session_id] = conversation_history
                    return
            else:
                yield {"event": "chunk", "data": "I dit not get it could you please califiy it"}
                return
            
        except Exception as e:
            logger.exception("Error occurred while processing query")
            yield {"event": "error", "data": str(e)}
    
    return EventSourceResponse(event_generator())