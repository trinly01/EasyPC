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
        return {"ERR": e.code, "body": e.read().decode()[:400]}

# --- 1) options flow: expose slot config ---
opts = api("GET","/operations?filter%5Bflow%5D%5B_eq%5D=ed1c258e-54b1-4183-9a3a-492f4d054efc&fields=id,name")["data"]
op = {o["name"]: o["id"] for o in opts}
print(api("PATCH",f"/operations/{op['load']}",{"options":{"sql":
  "SELECT id, name, code, daily_capacity, slot_minutes, slot_capacity, open_days, open_time, close_time, max_advance_days FROM easypc_stores WHERE active = true ORDER BY name"}}))
print(api("PATCH",f"/operations/{op['shape']}",{"options":{"code":"""module.exports = async function(data){
  const st = (data.load && data.load.rows) || [];
  const sv = (data.loadsvc && data.loadsvc.rows) || [];
  return { stores: st.map(s => ({id: s.id, name: s.name, code: s.code,
    daily_capacity: s.daily_capacity, slot_minutes: s.slot_minutes, slot_capacity: s.slot_capacity,
    open_days: s.open_days, open_time: s.open_time, close_time: s.close_time,
    max_advance_days: s.max_advance_days})),
    services: sv.map(s => ({id: s.id, name: s.name, price: s.price})) };
}"""}}))

# --- 2) NEW FLOW: easypc_appointment_slots (GET ?store=&date=) ---
flow = api("POST","/flows",{"name":"easypc_appointment_slots","status":"active",
  "trigger":"webhook","options":{"method":"GET","async":False},
  "icon":"calendar_view_day","description":"Public feed: slot grid for a store+date (Calendly-style)."})
print("FLOW:", flow)
fid = flow.get("data",{}).get("id") or flow.get("id")

def mkop(name, otype, options, resolve=None, flow_id=fid):
    return api("POST","/operations",{"flow":flow_id,"name":name,"type":otype,"options":options,"resolve":resolve,"position_x":19,"position_y":19})

load = mkop("load","likha_sql",{"sql":"""SELECT s.name AS store_name, s.slot_minutes, s.slot_capacity, s.daily_capacity,
       s.open_days, s.open_time, s.close_time, s.max_advance_days
FROM easypc_stores s WHERE s.id = '{{$trigger.query.store}}'::uuid AND s.active = true;
SELECT a.preferred_time, count(*) AS n FROM easypc_appointments a
WHERE a.store = '{{$trigger.query.store}}'::uuid AND a.preferred_date = '{{$trigger.query.date}}'::date
  AND a.status = 'confirmed' GROUP BY a.preferred_time"""})
print("load:", load)

resp_code = """module.exports = async function(data){
  const rs = (data.load && data.load.results) || null;
  const rows = rs ? rs[0] : ((data.load && data.load.rows) || []);
  const counts = rs ? rs[1] : [];
  const st = rows[0];
  if (!st) throw new Error('Store not found');
  const q = (data.$trigger && data.$trigger.query) || {};
  const dt = new Date(String(q.date || '') + 'T00:00:00');
  if (isNaN(dt)) throw new Error('date YYYY-MM-DD required');
  const days = ['sun','mon','tue','wed','thu','fri','sat'];
  if ((st.open_days || []).indexOf(days[dt.getDay()]) === -1)
    return { store: st.store_name, date: q.date, closed: true, slots: [] };
  // PH "now" for same-day past-slot disabling
  const nowPH = new Date(new Date().toLocaleString('en-US', {timeZone: 'Asia/Manila'}));
  const isToday = q.date === nowPH.toISOString().slice(0,10);
  const parse12 = t => { const m = String(t).trim().match(/^(\d{1,2}):(\d{2})\s*([AaPp][Mm])$/);
    if (!m) return null; let h = parseInt(m[1]) % 12; if (/p/i.test(m[3])) h += 12;
    return h*60 + parseInt(m[2]); };
  const fmt12 = mm => { let h = Math.floor(mm/60), mi = mm%60, ap = h>=12?'PM':'AM';
    h = h%12 || 12; return h + ':' + String(mi).padStart(2,'0') + ' ' + ap; };
  const o = parse12(st.open_time) ?? 540, c = parse12(st.close_time) ?? 1080;
  const step = st.slot_minutes || 60, cap = st.slot_capacity || 1;
  const booked = {}; for (const r of counts) booked[r.preferred_time] = parseInt(r.n);
  const slots = [];
  for (let m = o; m + step <= c; m += step) {
    const label = fmt12(m);
    const n = booked[label] || 0;
    const past = isToday && (m <= nowPH.getHours()*60 + nowPH.getMinutes());
    slots.push({ time: label, remaining: Math.max(cap - n, 0),
      available: !past && n < cap });
  }
  return { store: st.store_name, date: q.date, closed: false, slots: slots };
}"""
resp = mkop("respond","exec",{"code":resp_code})
print("respond:", resp)
# wire trigger -> load -> respond
print(api("PATCH",f"/flows/{fid}",{"operation": load["data"]["id"]}))
print(api("PATCH",f"/operations/{load['data']['id']}",{"resolve": resp["data"]["id"]}))
print("SLOTS FLOW ID:", fid)
