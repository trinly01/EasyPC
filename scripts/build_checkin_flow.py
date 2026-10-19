import urllib.request, json, os
TOKEN = os.environ['DIRECTUS_TOKEN']
B = 'https://likha-playground.zyberlab.com'
H = {'Authorization': f'Bearer {TOKEN}', 'User-Agent': 'curl/8.5.0', 'Content-Type': 'application/json'}
def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    return json.loads(urllib.request.urlopen(urllib.request.Request(B + path, data=data, headers=H, method=method)).read() or b'{}')
def mkop(flow, key, typ, opts, x, y):
    r = req('POST', '/operations', {'flow': flow, 'name': key, 'key': key, 'type': typ,
        'position_x': x, 'position_y': y, 'options': opts})['data']
    print('  op', key); return r['id']
def link(a, b): req('PATCH', f'/operations/{a}', {'resolve': b})

f = req('POST', '/flows', {'name': 'easypc_appointment_checkin', 'icon': 'how_to_reg',
    'status': 'active', 'trigger': 'manual',
    'options': {'collections': ['easypc_appointments'], 'location': 'item', 'requireConfirmation': True}})['data']['id']
print('flow', f)

o_load = mkop(f, 'load', 'likha_sql', {'sql': r"""SELECT a.id, a.appointment_no, a.status, a.customer, a.store, a.service,
       a.unit_type, a.concern, a.preferred_date::text AS preferred_date, a.preferred_time,
       c.name AS customer_name, sv.name AS service_name
FROM easypc_appointments a
JOIN easypc_customers c ON c.id = a.customer
LEFT JOIN easypc_services sv ON sv.id = a.service
WHERE a.id = '{{$trigger.keys.0}}'::uuid"""}, 0, 0)

o_guard = mkop(f, 'guard', 'exec', {'code': r'''module.exports = async function(data){
  const row = ((data.load && data.load.rows) || [])[0];
  if (!row) throw new Error('Appointment not found');
  if (row.work_order || row.status === 'arrived') throw new Error('Already checked in');
  if (row.status === 'cancelled') throw new Error('Booking was cancelled');
  return row;
}'''}, 0, 100)

o_make = mkop(f, 'mkwo', 'item-create', {'collection': 'easypc_work_orders', 'permissions': '$full',
  'payload': {
    'status': 'registered',
    'customer': '{{load.rows.0.customer}}',
    'store': '{{load.rows.0.store}}',
    'unit_type': '{{load.rows.0.unit_type}}',
    'customer_concern': 'Booked {{load.rows.0.appointment_no}} ({{load.rows.0.service_name}}) — {{load.rows.0.concern}}'
  }}, 0, 200)

o_link = mkop(f, 'linkappt', 'item-update', {'collection': 'easypc_appointments', 'permissions': '$full',
  'emitEvents': False,
  'payload': {'status': 'arrived', 'work_order': '{{mkwo}}'}}, 0, 300)
# item-create returns the new record id under $last? — use {{$last}} key if needed; keep {{mkwo}} then fix if wrong

o_res = mkop(f, 'respond', 'exec', {'code': r'''module.exports = async function(data){
  const row = ((data.load && data.load.rows) || [])[0] || {};
  return { ok: true, appointment: row.appointment_no,
    work_order_id: data.mkwo && (data.mkwo.id || data.mkwo),
    note: 'Work order created — intake form ready' };
}'''}, 0, 400)

link(o_load, o_guard); link(o_guard, o_make); link(o_make, o_link); link(o_link, o_res)
req('PATCH', f'/flows/{f}', {'operation': o_load})
print('CHECKIN FLOW DONE', f)
