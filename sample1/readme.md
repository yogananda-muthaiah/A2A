

# Kill anything on 8000

lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Kill anything on 8001
lsof -ti:8001 | xargs kill -9 2>/dev/null || true     
