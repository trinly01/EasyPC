import urllib.request, json, os
TOKEN = os.environ['DIRECTUS_TOKEN']
B = 'https://likha-playground.zyberlab.com'
H = {'Authorization': f'Bearer {TOKEN}', 'User-Agent': 'curl/8.5.0', 'Content-Type': 'application/json'}
FLOW = '671f175c-b048-4e87-88e9-2563e5a972db'
def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    return json.loads(urllib.request.urlopen(urllib.request.Request(B + path, data=data, headers=H, method=method)).read() or b'{}')
ops = {o['key']: o['id'] for o in req('GET', f'/operations?filter%5Bflow%5D%5B_eq%5D={FLOW}&fields=id,key')['data']}

req('PATCH', f"/operations[{0}]".replace('[0]',''), {}) if False else None

req('PATCH', f"/operations/{ops['capcheck']}", {'options': {'sql': r"""SELECT s.daily_capacity, s.open_days,
  (SELECT count(*) FROM easypc_appointments x
   WHERE x.store = a.store AND x.preferred_date = NULLIF('{{auth.new_date}}','')::date AND x.status = 'confirmed') AS booked
FROM easypc_appointments a JOIN easypc_stores s ON s.id = a.store
WHERE a.appointment_no = '{{auth.ref}}'"""}})

req('PATCH', f"/operations/{ops['apply']}", {'options': {'sql': r"""UPDATE easypc_appointments
SET status = '{{decide.new_status}}',
    preferred_date = COALESCE(NULLIF('{{decide.new_date}}','')::date, preferred_date),
    preferred_time = COALESCE(NULLIF('{{decide.new_time}}',''), preferred_time)
WHERE id = (SELECT id FROM easypc_appointments WHERE appointment_no = '{{auth.ref}}')
  AND '{{decide.armed}}' = '1'"""}})

print('patched capcheck/apply')
