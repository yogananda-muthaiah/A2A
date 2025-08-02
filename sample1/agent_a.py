from fastapi import FastAPI
from pydantic import BaseModel
import httpx
import os

PORT = int(os.getenv("AGENT_A_PORT", 8000))
B_URL = os.getenv("AGENT_B_URL", "http://localhost:8001")

app = FastAPI(title="Agent-A")

class EchoRequest(BaseModel):
    text: str

class EchoResponse(BaseModel):
    source: str
    echoed: str

@app.post("/echo", response_model=EchoResponse)
async def echo(req: EchoRequest):
    # Optionally forward to Agent-B
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{B_URL}/reverse", json={"text": req.text})
        r.raise_for_status()
        reversed_text = r.json()["reversed"]
    return EchoResponse(source="Agent-A", echoed=reversed_text)
