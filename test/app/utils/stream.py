import re
import logging
from typing import Dict, Any, AsyncGenerator
from app.models.model import ToolResponse
from app.services.tools import weather, dealership, appointment

async def stream_response(
    response_text: str, 
    tool_calls: list = None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Generate SSE events for streaming AI responses
    
    Args:
        response_text: Full text response from AI
        tool_calls: List of tool calls made by the AI
    
    Yields:
        SSE events for streaming
    """
    # logging.info("checking AI response")
    # logging.info(response_text.text)
    words = re.findall(r'\S+|\s+', response_text)
    
    # Stream words
    for word in words:
        yield {
            "event": "chunk", 
            "data": word
        }

    # Handle tool calls if present
    if tool_calls:
        for tool_call in tool_calls:
            # Yield tool use event
            yield {
                "event": "tool_use", 
                "data": tool_call.function.name
            }

            # Prepare tool output (execute the tool)
            tool_name = tool_call.function.name
            tool_args = eval(tool_call.function.arguments)

            # Map tool name to actual tool function
            tool_map = {
                "get_weather": weather.get_weather,
                "get_dealership_address": dealership.get_dealership_address,
                "check_appointment_availability": appointment.check_appointment_availability,
                "schedule_appointment": appointment.schedule_appointment
            }

            # Execute the tool
            if tool_name in tool_map:
                tool_result = tool_map[tool_name](**tool_args)

                # Yield tool output event
                yield {
                    "event": "tool_output", 
                    "data": {
                        "name": tool_name, 
                        "output": tool_result.model_dump()
                    }
                }

    # End of stream event
    yield {
        "event": "end", 
        "data": ""
    }