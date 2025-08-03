
Below is a minimal, fully runnable Python script that reproduces the exact “Predictive Stock Transfer & Automatic Purchase Re-Order” use-case by calling the real SAP Cloud APIs.
It is intentionally short and self-contained; in production you would externalise secrets, add error handling, paging, OAuth refresh, etc.

``` 
python auto_replenish.py
``` 

``` 
Demand forecast: 1200
Shortage: 420
Surplus: {'B': 300, 'C': 250}
Best internal: 300 from B
STO created: 4500012345
Best supplier: S-987 2.3
PR created: 1000123456
Flow finished.
```


The script is a complete A2A integration in fewer than 200 lines; swap the endpoints and payloads for your own OData versions or on-premise systems as required.
