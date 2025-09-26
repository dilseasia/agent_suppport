from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import workflow_routes,calender
from database import Base, engine
from models.item_model import AuthConfig  # import all your models here

app = FastAPI(title="Auth Config Backend")

# Enable CORS (allow frontend to call backend from any origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# Include routes from workflow.py exactly as defined (prefix already set in router)
app.include_router(workflow_routes.router)  # router already has prefix="/routes"
app.include_router(calender.router)

# Root endpoint
@app.get("/")
def root():
    return {"message": "Backend running ✅"}

# Create database tables on startup
@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
