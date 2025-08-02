#!/usr/bin/env bash
trap 'kill 0' SIGINT
python3 -m uvicorn agent_a:app --port 8000 --reload &
python3 -m uvicorn agent_b:app --port 8001 --reload &
wait
