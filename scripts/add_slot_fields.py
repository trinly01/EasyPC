import json, urllib.request
TOKEN = "oyvvW-gfxUT8cVn0UutUXji9jtvVl1sr"
BASE = "https://likha-playground.zyberlab.com"
def api(method, path, body=None):
    r = urllib.request.Request(BASE + path, method=method,
        headers={"Authorization":"Bearer "+TOKEN,"Content-Type":"application/json","User-Agent":"curl/8.5.0"},
        data=json.dumps(body).encode() if body else None)
    try:
        return json.load(urllib.request.urlopen(r))
    except urllib.error.HTTPError as e:
        return {"ERR": e.code, "body": e.read().decode()[:300]}
for f,t,meta in [
    ("slot_minutes","integer",{"interface":"input","note":"Minutes per bookable slot"}),
    ("slot_capacity","integer",{"interface":"input","note":"Bookings allowed per time slot"}),
]:
    print(f, api("POST","/fields/easypc_stores",{"field":f,"type":t,"meta":meta}))
# seed defaults on the 3 stores
stores = api("GET","/items/easypc_stores?fields=id,code,daily_capacity")
print("stores:", stores)
for s in stores.get("data",[]):
    print(api("PATCH",f"/items/easypc_stores/{s['id']}",{"slot_minutes":60,"slot_capacity":2}))
