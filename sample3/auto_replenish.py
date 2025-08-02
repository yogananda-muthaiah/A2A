#!/usr/bin/env python3
"""
End-to-end A2A flow:
1. Read demand forecast (IBP)
2. Check stock & MRP in Plant A
3. Search surplus stock in Plants B/C
4. Run ATP check
5. Create STO (cheapest internal)
6. Create PR for remaining qty (Ariba best price)
"""

import os, json, math
from datetime import datetime, timedelta
from dotenv import load_dotenv
from requests import Session
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient

load_dotenv()

# ---------- CONFIG ----------
MATERIAL = "FG-100"
PLANT_A  = "A"
PLANTS_SURPLUS = ["B", "C"]
DEMAND_WEEKS   = 4
TRANSPORT_DAYS = 2
# ----------------------------

s = Session()

# ---------- 0.  OAUTH TOKEN for S/4 ----------
def s4_token():
    url = f"{os.getenv('S4_HOST')}/oauth/token"
    r = s.post(url,
               auth=(os.getenv('S4_USER'), os.getenv('S4_PASSWORD')),
               data={'grant_type':'client_credentials'})
    r.raise_for_status()
    return r.json()['access_token']

s.headers.update({'Authorization': f"Bearer {s4_token()}"})

# ---------- 1.  IBP – demand forecast ----------
def ibp_forecast():
    url = (f"{os.getenv('S4_HOST')}/sap/opu/odata/sap/"
           f"API_DEMAND_PLANNING_SRV/DemandForecast")
    params = {
        "$filter": f"Material eq '{MATERIAL}' and Plant eq '{PLANT_A}'",
        "$select": "DemandQuantity",
        "$format": "json"
    }
    r = s.get(url, params=params)
    r.raise_for_status()
    total = sum(item['DemandQuantity'] for item in r.json()['d']['results'])
    return total

demand_qty = ibp_forecast()
print("Demand forecast:", demand_qty)

# ---------- 2.  Stock & MRP ----------
def plant_stock(plant):
    url = (f"{os.getenv('S4_HOST')}/sap/opu/odata/sap/"
           f"API_MATERIAL_STOCK_SRV/MaterialStock")
    params = {
        "$filter": f"Material eq '{MATERIAL}' and Plant eq '{plant}' and "
                   f"StorageLocation ne ''",
        "$format": "json"
    }
    r = s.get(url, params=params)
    r.raise_for_status()
    return sum(item['UnrestrictedStockQuantity']
               for item in r.json()['d']['results'])

def plant_receipts(plant):
    url = (f"{os.getenv('S4_HOST')}/sap/opu/odata/sap/"
           f"API_MRP_COCKPIT_SRV/MrpItems")
    params = {
        "$filter": f"Material eq '{MATERIAL}' and Plant eq '{plant}' and "
                   f"MrpElementCategory eq 'AR'",
        "$format": "json"
    }
    r = s.get(url, params=params)
    r.raise_for_status()
    return sum(item['Quantity'] for item in r.json()['d']['results'])

stock_A = plant_stock(PLANT_A)
receipts_A = plant_receipts(PLANT_A)
shortage = max(0, demand_qty - stock_A - receipts_A)
print("Shortage:", shortage)
if shortage == 0:
    print("No action needed.")
    exit()

# ---------- 3.  Surplus stock ----------
surplus = {}
for p in PLANTS_SURPLUS:
    surplus[p] = plant_stock(p)
print("Surplus:", surplus)

# ---------- 4.  ATP check ----------
def atp_ok(plant, qty, req_date):
    url = (f"{os.getenv('S4_HOST')}/sap/opu/odata/sap/"
           f"API_ATP_CHECK_SRV/CheckAvailability")
    body = {
        "Material": MATERIAL,
        "Plant": plant,
        "DemandQuantity": str(qty),
        "RequiredDate": req_date.isoformat()
    }
    r = s.post(url, json=body)
    r.raise_for_status()
    return r.json()['d']['ConfirmedQuantity'] == str(qty)

best_internal = None
needed = shortage
for plant, qty in surplus.items():
    take = min(qty, needed)
    req = datetime.utcnow().date() + timedelta(days=TRANSPORT_DAYS)
    if atp_ok(plant, take, req):
        best_internal = (plant, take)
        break
if best_internal:
    plant, qty = best_internal
    print(f"Best internal: {qty} from {plant}")

    # ---------- 5.  Create STO ----------
    url = (f"{os.getenv('S4_HOST')}/sap/opu/odata/sap/"
           f"API_STOCK_TRANSPORT_ORDER_SRV/A_StockTransportOrder")
    body = {
        "SupplyingPlant": plant,
        "ReceivingPlant": PLANT_A,
        "Material": MATERIAL,
        "OrderQuantity": str(qty),
        "DeliveryDate": req.isoformat()
    }
    r = s.post(url, json=body)
    r.raise_for_status()
    sto = r.json()['d']['StockTransportOrder']
    print("STO created:", sto)
    shortage -= qty

# ---------- 6.  Ariba – best external price ----------
if shortage > 0:
    client = BackendApplicationClient(client_id=os.getenv('ARIBA_CLIENT_ID'))
    oauth = OAuth2Session(client=client)
    token = oauth.fetch_token(
        token_url=os.getenv('ARIBA_TOKEN_URL'),
        client_id=os.getenv('ARIBA_CLIENT_ID'),
        client_secret=os.getenv('ARIBA_CLIENT_SECRET')
    )
    url = "https://api.ariba.com/v2/suppliers/catalog"
    params = {
        "material": MATERIAL,
        "qty": shortage,
        "currency": "EUR"
    }
    r = oauth.get(url, params=params)
    r.raise_for_status()
    best = min(r.json()['offers'], key=lambda x: float(x['price']))
    print("Best supplier:", best['supplier'], best['price'])

    # ---------- 7.  Create PR ----------
    url = (f"{os.getenv('S4_HOST')}/sap/opu/odata/sap/"
           f"API_PURCHASEREQ_PROCESS_SRV/A_PurchaseRequisitionHeader")
    body = {
        "Material": MATERIAL,
        "Plant": PLANT_A,
        "Quantity": str(shortage),
        "DeliveryDate": (datetime.utcnow().date()
                         + timedelta(days=int(best['leadtime']))).isoformat(),
        "SupplierHint": best['supplier']
    }
    r = s.post(url, json=body)
    r.raise_for_status()
    pr = r.json()['d']['PurchaseRequisition']
    print("PR created:", pr)

print("Flow finished.")
