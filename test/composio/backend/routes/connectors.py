from fastapi import APIRouter
from pydantic import BaseModel
from backend.config import BASE_URL, HEADERS
from backend.utils.http_client import http_get

router = APIRouter()

class ToolSearchRequest(BaseModel):
    search_term: str

@router.post("/search-toolkits")
def search_toolkits(body: ToolSearchRequest):
    url = f"{BASE_URL}/toolkits"
    params = {"limit": 100}

    # Use the reusable http_get helper
    data = http_get(url, headers=HEADERS, params=params)
    items = data.get("items", [])

    results = [
        item for item in items
        if body.search_term.lower() in item.get("name", "").lower()
        or body.search_term.lower() in item.get("slug", "").lower()
    ]
    return results
