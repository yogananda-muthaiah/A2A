# Terminal 1
uvicorn fake_weather:app --port 8002 --reload

# Terminal 2
uvicorn data_enricher:app --port 8003 --reload
