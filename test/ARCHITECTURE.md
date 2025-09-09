# SuperCar Assistant Architecture

This document outlines the architecture of the SuperCar Virtual Sales Assistant application, focusing on the interaction between the frontend and backend components.

## System Architecture

```
┌─────────────────┐        ┌─────────────────────────────────────────┐
│                 │        │                                         │
│    Frontend     │        │               Backend                   │
│    (Next.js)    │        │               (FastAPI)                 │
│                 │        │                                         │
├─────────────────┤        ├─────────────────┬───────────────────────┤
│                 │        │                 │                       │
│  Chat Interface │◄──────►│  /query (SSE)   │  Groq API             │
│                 │ POST   │                 │  Integration          │
│  Message Input  │ request│                 │                       │
│                 │        │                 │                       │
│  Response       │        │                 │                       │
│  Display        │        │                 │                       │
│                 │        │                 │                       │
│  Tool Output    │        │                 │                       │
│  Components     │        │                 │                       │
│                 │        │                 │                       │
└─────────────────┘        └─────────────────┼───────────────────────┘
                                             │
                                  ┌──────────┴───────────┐
                                  │                      │
                                  │    Tool Functions    │
                                  │                      │
                                  ├──────────────────────┤
                                  │                      │
                                  │  get_weather         │
                                  │                      │
                                  │  get_dealership_     │
                                  │  address             │
                                  │                      │
                                  │  check_appointment_  │
                                  │  availability        │
                                  │                      │
                                  │  schedule_           │
                                  │  appointment         │
                                  │                      │
                                  └──────────────────────┘
```

## Data Flow

1. **User Input**:
   - User enters a message in the frontend chat interface
   - Frontend sends a POST request to `/query` with the message and session ID

2. **Backend Processing**:
   - Backend receives the request and adds it to the chat history
   - The query is sent to Groq API with Llama 3.3 70B Versatile
   - The model processes the query and either:
     - Generates a direct text response
     - OR decides to use a tool to get information

3. **SSE Stream**:
   - The backend streams the response back to the frontend using SSE
   - Different event types are sent:
     - `chunk`: Text chunks from the AI assistant
     - `tool_use`: When the AI decides to use a tool
     - `tool_output`: The result of a tool execution
     - `end`: Signals the end of the response stream

4. **Frontend Rendering**:
   - The frontend processes the SSE stream in real-time
   - Text chunks are displayed as they arrive
   - Tool use events trigger loading indicators
   - Tool output events render specialized UI components based on the tool type
   - The end event finalizes the response

## Tool Calling Process

1. **Tool Definition**:
   - Tools are defined with their name, description, and parameters
   - These tool definitions are passed to the Groq API

2. **Tool Selection and Execution**:
   - The model identifies when a tool should be used based on user input
   - It extracts parameters from the user message
   - The backend executes the corresponding function
   - The result is streamed back to the frontend

## Session Management

- Each conversation has a unique `session_id`
- The backend maintains conversation history for each session
- This enables context-aware responses in ongoing conversations

## Required Tools

| Tool Name | Description | Parameters | Output Format |
|-----------|-------------|------------|--------------|
| `get_weather` | Gets weather information for a city | `city` (string) | Weather data object |
| `get_dealership_address` | Returns address for a dealership | `dealership_id` (string) | Dealership address object |
| `check_appointment_availability` | Checks available slots | `dealership_id`, `date` | List of time slots |
| `schedule_appointment` | Books a test drive | `user_id`, `dealership_id`, `date`, `time`, `car_model` | Booking confirmation object | 