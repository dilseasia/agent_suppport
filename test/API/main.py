from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import Base, engine, get_db
from schemas import AuthRequest, AuthResponse
from service import create_auth_config, save_auth_config_to_db

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Composio Auth API")

@app.post("/create-auth", response_model=AuthResponse)
def create_and_store_auth(req: AuthRequest, db: Session = Depends(get_db)):
    """
    Single endpoint to create an auth config in Composio,
    then store it in the local database and return the record.
    """
    try:
        # 1️⃣ Create auth config in Composio
        print("=== Creating auth config in Composio ===")
        created = create_auth_config(
            composio_api_key=req.composio_api_key,
            toolkit_slug=req.toolkit_slug,
            bearer_token=req.bearer_token,
            api_key_secret=req.api_key_secret,
            scopes=req.scopes,
            config_name=req.config_name
        )
        print("Created response:", created)

        # 2️⃣ Save response to local database
        print("=== Saving auth config to database ===")
        record = save_auth_config_to_db(db, req.organization_id, req.toolkit_slug, created)
        print("Saved record:", record)

        # 3️⃣ Return saved record
        return record

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
