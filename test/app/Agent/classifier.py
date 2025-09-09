
import os
import json
import re
import requests
from datetime import datetime
from typing import Dict, Any
from prompt import CLASSIFICATION_PROMPT

MODEL_ID = "gemini-1.5-flash-latest"  # or "gemini-1.5-pro-latest"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:generateContent"
HEADERS = {"Content-Type": "application/json"}

INTENT_KEYS = ["greeting", "support", "appointment", "estimate", "information", "general"]

def _extract_json(text: str) -> Dict[str, Any]:
    """Return the first valid JSON object from text (tolerates code fences)."""
    cleaned = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end > start:
        return json.loads(cleaned[start:end+1])
    m = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if m:
        return json.loads(m.group(0))
    raise ValueError("No valid JSON object found in model output")

def _coerce_float(x, default=0.0):
    try:
        v = float(x)
        if v < 0: return 0.0
        if v > 1: return 1.0
        return v
    except Exception:
        return default

def _normalize_result(r: Dict[str, Any], original_query: str) -> Dict[str, Any]:
    # Ensure required top-level keys
    r.setdefault("original_query", original_query)
    r.setdefault("corrected_query", original_query)

    # Ensure intent dict with all keys
    intent = r.get("intent") or {}
    fixed_intent = {}
    for key in INTENT_KEYS:
        fixed_intent[key] = _coerce_float(intent.get(key, 0.0), 0.0)
    r["intent"] = fixed_intent

    # Primary intent: highest score, tie-breaker preference
    max_score = max(fixed_intent.values()) if fixed_intent else 0.0
    # tie-break preference order
    pref_order = ["support", "appointment", "estimate", "information", "general", "greeting"]
    candidates = [k for k, v in fixed_intent.items() if v == max_score]
    chosen = None
    for p in pref_order:
        if p in candidates:
            chosen = p
            break
    r["primary_intent"] = chosen or "general"

    # out_of_context rule (true only if all < 0.2)
    r["out_of_context"] = bool(all(v < 0.2 for v in fixed_intent.values()))

    return r

def classify_query_with_gemini(query: str, api_key: str | None = None) -> Dict[str, Any]:
    """
    Returns a dict:
    {
      "original_query": ...,
      "corrected_query": ...,
      "intent": {... six keys ...},
      "primary_intent": "...",
      "out_of_context": false
    }
    """
    api_key = ("AIzaSyCr8QZd_EhfS584o0pI3B0ektSgIAAHsS0")
    if not api_key:
        raise ValueError("Gemini API key is required. Set GEMINI_API_KEY or pass api_key.")

    prompt = CLASSIFICATION_PROMPT.format(query=query)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 200,
            "responseMimeType": "application/json"  # ask for JSON-only
        }
    }

    resp = requests.post(f"{API_URL}?key={api_key}", headers=HEADERS, json=payload, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text}")

    data = resp.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    raw = _extract_json(text)
    result = _normalize_result(raw, original_query=query)

    # add useful metadata (optional)
    result["_meta"] = {
        "model": MODEL_ID,
        "timestamp": datetime.now().isoformat()
    }
    return result

if __name__ == "__main__":
    tests = [
        "I need plumbing help",
        "Can I book a service slot tomorrow at 10 AM?",                                                                               
        "How much cost to replace a faucet?",
        "What is the weather in New York?",
        "Hi there!",
    ]
    for q in tests:
        try:
            print(classify_query_with_gemini(q))
        except Exception as e:
            print({"error": str(e), "query": q})
