import os
import json
import logging
import asyncio
from groq import Groq
from typing import AsyncGenerator, Dict, List, Dict, Any, Optional
from dotenv import load_dotenv
from app.config.prompt import final_prompt

# Load environment variables
load_dotenv()

class GroqLLMClient:
    def __init__(self):
        """
        Initialize Groq client with API key from environment
        """
        self.api_key = os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("Groq API key is required")
        
        self.client = Groq(api_key=self.api_key)
        self.logger = logging.getLogger(__name__)

    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        tools: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Generate AI response using Groq API with optional tool calling
        """
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Updated model
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            logging.warning("checking gpt response")
            logging.warning(response)
            return response
        except Exception as e:
            self.logger.error(f"Error in Groq API call: {e}")
            return None
        
    def final_response(self, user_query: List[Dict[str, str]], function_response: List[Dict[str, str]]):
        """
        Generate AI response using Groq API with optional tool calling
        """
        messages = [
            {"role": "system", "content": f"your task is from give function_response:{function_response} and user_query make the answer like a human response, result should be as per query, result in string and return only final human response. dont explain any thing. "},
            {"role": "user", "content": user_query}
        ]
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Updated model
                messages=messages
            )
            return response.choices[0].message
        except Exception as e:
            self.logger.error(f"Error in Groq API call: {e}")
            return None
        
    def knowledge_base_response(self, user_query: List[Dict[str, str]]):
        """
        Generate AI response using Groq API with optional tool calling
        """
        messages = [
            {"role": "system", "content": f"{final_prompt}"},
            {"role": "user", "content": user_query}
        ]
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",  # Updated model
                messages=messages
            )
            return response.choices[0].message
        except Exception as e:
            self.logger.error(f"Error in Groq API call: {e}")
            return None


        

# class GroqLLMClient:
#     def __init__(self):
#         """
#         Initialize Groq client with API key from environment
#         """
#         self.api_key = os.getenv('GROQ_API_KEY')
#         if not self.api_key:
#             raise ValueError("Groq API key is required")
        
#         self.client = Groq(api_key=self.api_key)
#         self.logger = logging.getLogger(__name__)

#     def generate_response(
#         self, 
#         messages: List[Dict[str, str]], 
#         tools: Optional[List[Dict[str, Any]]] = None
#     ):
#         """
#         Generate AI response using Groq API with optional tool calling
#         """
#         try:
#             response = self.client.chat.completions.create(
#                 model="llama3-70b-8192",  # Llama 3.3 70B Versatile
#                 messages=messages,
#                 tools=tools,
#                 tool_choice="auto"
#             )

#             response_message = response.choices[0].message
#             tool_calls = response_message.tool_calls

#             # If no tool calls, return direct response
#             if not tool_calls:
#                 return response_message.content

#             # Process tool calls
#             messages.append(response_message)

#             for tool_call in tool_calls:
#                 function_name = tool_call.function.name
#                 function_to_call = self.available_functions.get(function_name)
                
#                 if not function_to_call:
#                     raise ValueError(f"Unknown function: {function_name}")

#                 function_args = json.loads(tool_call.function.arguments)
                
#                 try:
#                     # Call the function and get the response
#                     function_response = function_to_call(**function_args)
                    
#                     # Add tool response to messages
#                     messages.append({
#                         "tool_call_id": tool_call.id,
#                         "role": "tool",
#                         "name": function_name,
#                         "content": json.dumps(function_response.model_dump())
#                     })
#                 except Exception as e:
#                     # Handle function-specific errors
#                     messages.append({
#                         "tool_call_id": tool_call.id,
#                         "role": "tool",
#                         "name": function_name,
#                         "content": f"Error: {str(e)}"
#                     })

#             # Make a second API call with updated conversation
#             final_response = self.client.chat.completions.create(
#                 model="llama3-70b-8192",
#                 messages=messages
#             )

#             return final_response.choices[0].message.content

#         except Exception as e:
#             self.logger.error(f"Error in Groq API call: {e}")
#             return None