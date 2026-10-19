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

f = req('POST', '/flows', {'name': 'easypc_appointment_manage', 'icon': 'edit_calendar',
    'status': 'active', 'trigger': 'webhook', 'options': {'method': 'POST', 'async': False}})['data']['id']
print('flow', f)

o_auth = mkop(f, 'auth', 'exec', {'code': r'''module.exports = async function(data){
  const b = (data.$trigger && data.$trigger.body) || {};
  const ref = String(b.ref || b.appointment_no || '').trim().toUpperCase();
  if (!/^APPT-\d{4}-\d{4}$/.test(ref)) throw new Error('Bad reference');
  let mob = String(b.mobile || '').replace(/\D/g,'');
  if (mob.startsWith('63')) mob = '0' + mob.slice(2);
  if (!/^\d{4,11}$/.test(mob)) throw new Error('Invalid mobile');
  const action = String(b.action || 'view').toLowerCase();
  if (!['view','cancel','reschedule'].includes(action)) throw new Error('Bad action');
  const nd = String(b.new_date || '').trim();
  if (action === 'reschedule' && !/^\d{4}-\d{2}-\d{2}$/.test(nd)) throw new Error('Reschedule needs new_date YYYY-MM-DD');
  return { ref: ref, mobile: mob, action: action,
    new_date: String(nd).replace(/'/g,''), new_time: String(b.new_time || '').replace(/'/g,'') };
}'''}, 0, 0)

o_fetch = mkop(f, 'fetch', 'likha_sql', {'sql': r"""SELECT a.id, a.appointment_no, a.status, a.preferred_date::text AS preferred_date,
       a.preferred_time, a.unit_type, a.concern, a.store, a.service,
       s.name AS store_name, sv.name AS service_name, sv.price AS service_price,
       c.name AS customer_name
FROM easypc_appointments a
JOIN easypc_customers c ON c.id = a.customer
LEFT JOIN easypc_stores s ON s.id = a.store
LEFT JOIN easypc_services sv ON sv.id = a.service
WHERE a.appointment_no = '{{auth.ref}}'
  AND right(regexp_replace(c.contact_no,'[^0-9]','','g'), char_length('{{auth.mobile}}')) = '{{auth.mobile}}'"""}, 0, 100)

o_cap = mkop(f, 'capcheck', 'likha_sql', {'sql': r"""SELECT s.daily_capacity, s.open_days,
  (SELECT count(*) FROM easypc_appointments x
   WHERE x.store = a.store AND x.preferred_date = '{{auth.new_date}}'::date AND x.status = 'confirmed') AS booked
FROM easypc_appointments a JOIN easypc_stores s ON s.id = a.store
WHERE a.appointment_no = '{{auth.ref}}'"""}, 0, 200)

o_dec = mkop(f, 'decide', 'exec', {'code': r'''module.exports = async function(data){
  const a = data.auth;
  const row = ((data.fetch && data.fetch.rows) || [])[0];
  if (!row) return {armed: '0', notfound: true};
  if (['cancelled','arrived'].includes(row.status)) return {armed: '0', blocked: row.status};
  if (a.action === 'view') return {armed: '0'};
  if (a.action === 'cancel') return {armed: '1', new_status: 'cancelled', new_date: '', new_time: ''};
  // reschedule
  const cap = ((data.capcheck && data.capcheck.rows) || [])[0] || {};
  const d = new Date(a.new_date + 'T00:00:00');
  const days = ['sun','mon','tue','wed','thu','fri','sat'];
  const open = cap.open_days || [];
  if (open.length && open.indexOf(days[d.getDay()]) === -1) throw new Error('Branch closed that day');
  const today = new Date(); today.setHours(0,0,0,0);
  if (d < today) throw new Error('Date is in the past');
  if (cap.daily_capacity && Number(cap.booked) >= cap.daily_capacity) throw new Error('That date is fully booked');
  return {armed: '1', new_status: 'confirmed', new_date: a.new_date, new_time: a.new_time};
}'''}, 0, 300)

o_apply = mkop(f, 'apply', 'likha_sql', {'sql': r"""UPDATE easypc_appointments
SET status = '{{decide.new_status}}',
    preferred_date = COALESCE(NULLIF('{{decide.new_date}}',''), preferred_date)::date,
    preferred_time = COALESCE(NULLIF('{{decide.new_time}}',''), preferred_time)
WHERE id = (SELECT id FROM easypc_appointments WHERE appointment_no = '{{auth.ref}}')
  AND '{{decide.armed}}' = '1'"""}, 0, 400)

o_res = mkop(f, 'respond', 'exec', {'code': r'''module.exports = async function(data){
  if (data.decide && data.decide.notfound) return {found: false};
  if (data.decide && data.decide.blocked) return {found: true, error: 'Booking is already ' + data.decide.blocked};
  const row = ((data.fetch && data.fetch.rows) || [])[0];
  const a = data.auth;
  const status = a.action === 'view' ? row.status : (a.action === 'cancel' ? 'cancelled' : 'confirmed');
  return { found: true, action: a.action, status: status,
    booking: { appointment_no: row.appointment_no, store: row.store_name,
      service: row.service_name, service_price: row.service_price,
      date: a.action === 'reschedule' ? a.new_date : row.preferred_date,
      time: a.action === 'reschedule' ? (a.new_time || row.preferred_time) : row.preferred_time,
      unit_type: row.unit_type, customer_name: row.customer_name } };
}'''}, 0, 500)

link(o_auth, o_fetch); link(o_fetch, o_cap); link(o_cap, o_dec); link(o_dec, o_apply); link(o_apply, o_res)
req('PATCH', f'/flows/{f}', {'operation': o_auth})
print('MANAGE FLOW DONE', f)
