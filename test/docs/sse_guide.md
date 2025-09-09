# Working with Server-Sent Events (SSE) in FastAPI

This guide explains how to implement Server-Sent Events (SSE) in your FastAPI application for the SuperCar Virtual Sales Assistant.

## What are Server-Sent Events (SSE)?

Server-Sent Events (SSE) is a technology that enables a server to push updates to a client over an HTTP connection. Unlike WebSockets, which provide bidirectional communication, SSE is unidirectional, allowing only the server to send data to the client.

Key features of SSE:
- One-way communication (server to client)
- Uses standard HTTP
- Automatic reconnection
- Text-based protocol

## Implementing SSE in FastAPI

### 1. Install Required Packages

For FastAPI, we'll use the `sse-starlette` package:

```bash
pip install sse-starlette
```

### 2. Implementing the Query Endpoint

For the SuperCar Assistant, you need to implement a POST endpoint that handles user messages and returns an SSE stream of responses:

```python
from fastapi import FastAPI
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from typing import Dict, List, Any, AsyncGenerator

app = FastAPI()

class QueryRequest(BaseModel):
    query: str
    session_id: str

async def generate_assistant_response(query: str) -> AsyncGenerator[Dict[str, Any], None]:
    # Example implementation - you'll replace this with Groq API
    # Send chunks of text
    yield {
        "event": "chunk",
        "data": "Processing your question..."
    }
    await asyncio.sleep(0.5)
    
    # If we need to use a tool, indicate it
    if "weather" in query.lower():
        yield {
            "event": "tool_use",
            "data": "get_weather"
        }
        await asyncio.sleep(0.5)
        
        # Tool result
        tool_result = {
            "name": "get_weather",
            "output": {
                "temperature": "34°C",
                "conditions": "Sunny",
                "city": "New York"
            }
        }
        
        yield {
            "event": "tool_output",
            "data": json.dumps(tool_result)
        }
        await asyncio.sleep(0.5)
        
        # Continue with text response
        yield {
            "event": "chunk",
            "data": "The weather in New York is 34°C and it's sunny."
        }
    
    # Always end the stream
    yield {
        "event": "end",
        "data": ""
    }

@app.post("/query")
async def query_endpoint(payload: QueryRequest):
    return EventSourceResponse(generate_assistant_response(payload.query))
```

### 3. Adding CORS Support

Since your frontend will be running on a different port/domain, you need to add CORS support:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Set to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Event Types for SuperCar Assistant

For the SuperCar Assistant, you need to implement four types of events:

1. **chunk**: Text chunks from the AI assistant
   ```python
   yield {"event": "chunk", "data": "Some text from the assistant"}
   ```

2. **tool_use**: When the AI decides to use a tool
   ```python
   yield {"event": "tool_use", "data": "get_weather"}
   ```

3. **tool_output**: The result of a tool execution
   ```python
   tool_result = {
       "name": "get_weather",
       "output": {"temperature": "34°C", "city": "New York"}
   }
   yield {"event": "tool_output", "data": json.dumps(tool_result)}
   ```

4. **end**: Signals the end of the response stream
   ```python
   yield {"event": "end", "data": ""}
   ```

## Testing SSE Endpoints

You can test your SSE endpoint using curl:

```bash
curl -X POST -N -H "Content-Type: application/json" \
  -d '{"query": "What is the weather?", "session_id": "test123"}' \
  http://localhost:8000/query
```

## Resources

- [SSE Starlette Documentation](https://github.com/sysid/sse-starlette)
- [MDN Web Docs: Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [FastAPI Documentation](https://fastapi.tiangolo.com/) 