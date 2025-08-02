from fastapi import FastAPI
from pydantic import BaseModel
import os

PORT = int(os.getenv("AGENT_B_PORT", 8001))

app = FastAPI(title="Agent-B")

class ReverseRequest(BaseModel):
    text: str

class ReverseResponse(BaseModel):
    source: str
    reversed: str

@app.post("/reverse", response_model=ReverseResponse)
def reverse(req: ReverseRequest):
    return ReverseResponse(source="Agent-B", reversed=req.text[::-1])
