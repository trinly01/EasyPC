import urllib.request, json, os
TOKEN = os.environ['DIRECTUS_TOKEN']
B = 'https://likha-playground.zyberlab.com'
H = {'Authorization': f'Bearer {TOKEN}', 'User-Agent': 'curl/8.5.0', 'Content-Type': 'application/json'}
FLOW = '6374c703-9835-4f1e-a534-46ef8f41306f'
def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    return json.loads(urllib.request.urlopen(urllib.request.Request(B + path, data=data, headers=H, method=method)).read() or b'{}')
ops = {o['key']: o['id'] for o in req('GET', f'/operations?filter%5Bflow%5D%5B_eq%5D={FLOW}&fields=id,key')['data']}

# insert pick exec op as FIRST op: extract appointment id robustly
pick = req('POST', '/operations', {'flow': FLOW, 'name': 'pick', 'key': 'pick', 'type': 'exec',
    'position_x': -200, 'position_y': 0,
    'options': {'code': '''module.exports = async function(data){
  const t = data.$trigger || {};
  const keys = t.keys || (t.body && t.body.keys) || [];
  const id = keys[0] || t.key || (t.body && t.body.key);
  if (id === undefined || id === null) throw new Error('No appointment selected');
  return { appt_id: String(id).replace(/'/g, '') };
}'''}})['data']

req('PATCH', f"/operations/{ops['load']}", {'options': {'sql': """SELECT a.id, a.appointment_no, a.status, a.customer, a.store, a.service,
       a.unit_type, a.concern, a.preferred_date::text AS preferred_date, a.preferred_time,
       c.name AS customer_name, sv.name AS service_name, a.work_order
FROM easypc_appointments a
JOIN easypc_customers c ON c.id = a.customer
LEFT JOIN easypc_services sv ON sv.id = a.service
WHERE a.id = NULLIF('{{pick.appt_id}}','')::int"""}})

# rewire: flow starts at pick, pick -> load
req('PATCH', f"/operations/{pick['id']}", {'resolve': ops['load']})
req('PATCH', f'/flows/{FLOW}', {'operation': pick['id']})
print('pick inserted before load')
