from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os
import random

PORT = int(os.getenv("PORT", 8002))
TARGET = os.getenv("TARGET_URL", "http://localhost:8003")   # downstream agent

app = FastAPI(title="Fake-Weather-Agent")

class Location(BaseModel):
    city: str

class WeatherReport(BaseModel):
    source: str
    city: str
    temperature: float   # °C
    condition: str
    humidity: int        # %
    wind_kmh: float

CONDITIONS = ["Sunny", "Cloudy", "Rain", "Snow", "Thunderstorm"]

@app.post("/weather", response_model=WeatherReport)
async def get_weather(loc: Location):
    """Generate a fake weather report for the given city."""
    # Optionally call another agent (e.g. a “data-enrichment” service)
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(
                f"{TARGET}/enrich",
                json={"city": loc.city}
            )
            r.raise_for_status()
            extra = r.json()
        except Exception:
            extra = {}

    return WeatherReport(
        source="Fake-Weather-Agent",
        city=loc.city,
        temperature=round(random.uniform(-10, 40), 1),
        condition=random.choice(CONDITIONS),
        humidity=random.randint(20, 95),
        wind_kmh=round(random.uniform(0, 40), 1),
        **extra
    )
