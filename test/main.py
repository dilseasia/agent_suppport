from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# from app.routes.chatbot import chatbot_route
from app.routes.chatbot_1 import chatbot_route


app = FastAPI()

# Add CORS middleware to allow requests from the frontend
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # In production, you'd want to specify exact origins
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chatbot_route)
