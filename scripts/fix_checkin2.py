import urllib.request, json, os
TOKEN = os.environ['DIRECTUS_TOKEN']
B = 'https://likha-playground.zyberlab.com'
H = {'Authorization': f'Bearer {TOKEN}', 'User-Agent': 'curl/8.5.0', 'Content-Type': 'application/json'}
FLOW = '6374c703-9835-4f1e-a534-46ef8f41306f'
def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    return json.loads(urllib.request.urlopen(urllib.request.Request(B + path, data=data, headers=H, method=method)).read() or b'{}')
ops = {o['key']: o['id'] for o in req('GET', f'/operations?filter%5Bflow%5D%5B_eq%5D={FLOW}&fields=id,key')['data']}

# mkwo: emit events so numbering flow fires; plain hyphen (em-dash mojibake)
req('PATCH', f"/operations[{0}]".replace('[0]',''), {}) if False else None
req('PATCH', f"/operations/{ops['mkwo']}", {'options': {'collection': 'easypc_work_orders',
    'permissions': '$full', 'emitEvents': True,
    'payload': {
      'status': 'registered',
      'customer': '{{load.rows.0.customer}}',
      'store': '{{load.rows.0.store}}',
      'unit_type': '{{load.rows.0.unit_type}}',
      'customer_concern': 'Booked {{load.rows.0.appointment_no}} ({{load.rows.0.service_name}}) - {{load.rows.0.concern}}'}}})

# linkappt: mkwo result is an ARRAY of keys
req('PATCH', f"/operations[{0}]".replace('[0]',''), {}) if False else None
req('PATCH', f"/operations/{ops['linkappt']}", {'options': {'collection': 'easypc_appointments',
    'permissions': '$full', 'emitEvents': False,
    'payload': {'status': 'arrived', 'work_order': '{{mkwo.0}}'}}})

# cleanup: delete phantom + bad WOs, reset appointment
for wid in ['c6ba10d8-3896-415d-ad3c-1b09490f16f5', '9980552c-b927-43c5-9e10-1759b98c13c7']:
    req('DELETE', f'/items/easypc_work_orders/{wid}'); print('deleted wo', wid[:8])
req('PATCH', '/items/easypc_appointments/2', {'status': 'confirmed', 'work_order': None})
print('reset APPT-2026-0002')
