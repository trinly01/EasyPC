import json, urllib.request
TOKEN = "oyvvW-gfxUT8cVn0UutUXji9jtvVl1sr"
BASE = "https://likha-playground.zyberlab.com"
FID = "dfc7c15a-ccaf-47f2-ba7d-bfafd4728e0f"
def api(method, path, body=None):
    r = urllib.request.Request(BASE + path, method=method,
        headers={"Authorization":"Bearer "+TOKEN,"Content-Type":"application/json","User-Agent":"curl/8.5.0"},
        data=json.dumps(body).encode() if body else None)
    try:
        return json.load(urllib.request.urlopen(r))
    except urllib.error.HTTPError as e:
        return {"ERR": e.code, "body": e.read().decode()[:300]}

def mkop(name, otype, options):
    return api("POST","/operations",{"flow":FID,"name":name,"key":name,"type":otype,"options":options})

load = mkop("load","likha_sql",{"sql":"""SELECT s.name AS store_name, s.slot_minutes, s.slot_capacity, s.daily_capacity,
       s.open_days, s.open_time, s.close_time, s.max_advance_days
FROM easypc_stores s WHERE s.id = '{{$trigger.query.store}}'::uuid AND s.active = true;
SELECT a.preferred_time, count(*) AS n FROM easypc_appointments a
WHERE a.store = '{{$trigger.query.store}}'::uuid AND a.preferred_date = '{{$trigger.query.date}}'::date
  AND a.status = 'confirmed' GROUP BY a.preferred_time"""})
print("load:", load)

resp_code = r"""module.exports = async function(data){
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
    slots.push({ time: label, remaining: Math.max(cap - n, 0), available: !past && n < cap });
  }
  return { store: st.store_name, date: q.date, closed: false, slots: slots };
}"""
resp = mkop("respond","exec",{"code":resp_code})
print("respond:", resp)
print(api("PATCH",f"/flows/{FID}",{"operation": load["data"]["id"]}))
print(api("PATCH",f"/operations/{load['data']['id']}",{"resolve": resp["data"]["id"]}))
