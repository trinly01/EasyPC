import json, urllib.request
TOKEN = "oyvvW-gfxUT8cVn0UutUXji9jtvVl1sr"
BASE = "https://likha-playground.zyberlab.com"
def api(method, path, body=None):
    r = urllib.request.Request(BASE + path, method=method,
        headers={"Authorization":"Bearer "+TOKEN,"Content-Type":"application/json","User-Agent":"curl/8.5.0"},
        data=json.dumps(body).encode() if body else None)
    return json.load(urllib.request.urlopen(r))
for fid in ["ed1c258e-54b1-4183-9a3a-492f4d054efc","9bf3bc0a-1bb5-4613-be99-1f6dac87eee4","671f175c-b048-4e87-88e9-2563e5a972db"]:
    f = api("GET",f"/flows/{fid}?fields=id,name")["data"]
    ops = api("GET",f"/operations?filter%5Bflow%5D%5B_eq%5D={fid}&fields=id,name,type,options,resolve,reject")["data"]
    print("="*30, f["name"], f["id"])
    for o in sorted(ops, key=lambda x:x["name"]):
        print(f"--- {o['name']} ({o['type']}) resolve={o['resolve']} reject={o['reject']}")
        opts = o["options"] or {}
        if o["type"]=="likha_sql": print("  SQL:", opts.get("sql","")[:500])
        elif o["type"]=="exec": print("  CODE:", opts.get("code","")[:800])
        else: print("  OPTS:", json.dumps(opts)[:400])
