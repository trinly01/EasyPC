import urllib.request, json, os
TOKEN = os.environ['DIRECTUS_TOKEN']
B = 'https://likha-playground.zyberlab.com'
H = {'Authorization': f'Bearer {TOKEN}', 'User-Agent': 'curl/8.5.0', 'Content-Type': 'application/json'}
def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    return json.loads(urllib.request.urlopen(urllib.request.Request(B + path, data=data, headers=H, method=method)).read() or b'{}')
ops = {o['key']: o['id'] for o in req('GET', '/operations?filter%5Bflow%5D%5B_eq%5D=6374c703-9835-4f1e-a534-46ef8f41306f&fields=id,key')['data']}
sql = """SELECT a.id, a.appointment_no, a.status, a.customer, a.store, a.service,
       a.unit_type, a.concern, a.preferred_date::text AS preferred_date, a.preferred_time,
       c.name AS customer_name, sv.name AS service_name, a.work_order
FROM easypc_appointments a
JOIN easypc_customers c ON c.id = a.customer
LEFT JOIN easypc_services sv ON sv.id = a.service
WHERE a.id = NULLIF('{{$trigger.keys.0}}','')::int"""
req('PATCH', f"/operations/{ops['load']}", {'options': {'sql': sql}})
print('patched')
