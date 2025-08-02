from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Data-Enricher")

class EnrichRequest(BaseModel):
    city: str

class EnrichResponse(BaseModel):
    population: int
    country: str

FAKE_DB = {
    "london": {"population": 9_000_000, "country": "UK"},
    "paris":  {"population": 2_100_000, "country": "France"},
    "tokyo":  {"population": 14_000_000, "country": "Japan"},
}

@app.post("/enrich", response_model=EnrichResponse)
def enrich(req: EnrichRequest):
    city = req.city.lower()
    if city not in FAKE_DB:
        return EnrichResponse(population=0, country="Unknown")
    return FAKE_DB[city]
