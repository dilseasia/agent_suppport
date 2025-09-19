from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import workflow_routes

app = FastAPI(title="Auth Config Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

# Routes
app.include_router(workflow_routes.router, prefix="/workflow")

@app.get("/")
def root():
    return {"message": "Backend running ✅"}
