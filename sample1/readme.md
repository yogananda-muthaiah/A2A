

## Part 1
* https://community.sap.com/t5/technology-blog-posts-by-sap/building-collaborative-microservices-in-python-with-fastapi-echo-amp/ba-p/14170025




## Kill anything on Port 8000

lsof -ti:8000 | xargs kill -9 2>/dev/null || true

## Kill anything on Port 8001
lsof -ti:8001 | xargs kill -9 2>/dev/null || true     
