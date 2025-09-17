import requests
from fastapi import HTTPException

# Reusable session client
client = requests.Session()

# Helper functions using the client
def http_get(url, headers=None, params=None):
    resp = client.get(url, headers=headers, params=params)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def http_post(url, headers=None, json=None):
    resp = client.post(url, headers=headers, json=json)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def http_delete(url, headers=None):
    resp = client.delete(url, headers=headers)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def http_patch(url, headers=None, json=None):
    resp = client.patch(url, headers=headers, json=json)
    if not resp.ok:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()
