import urllib.request, urllib.error, json, os
TOKEN = os.environ['DIRECTUS_TOKEN']
B = 'https://likha-playground.zyberlab.com'
H = {'Authorization': f'Bearer {TOKEN}', 'User-Agent': 'curl/8.5.0', 'Content-Type': 'application/json'}

def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(B + path, data=data, headers=H, method=method)
    try:
        return json.loads(urllib.request.urlopen(r).read() or b'{}')
    except urllib.error.HTTPError as e:
        print('ERR', method, path, e.code, e.read()[:400]); raise

def mkop(flow, key, typ, opts, x, y):
    r = req('POST', '/operations', {'flow': flow, 'name': key, 'key': key, 'type': typ,
        'position_x': x, 'position_y': y, 'options': opts})['data']
    print('  op', key); return r['id']

def link(a, b): req('PATCH', f'/operations/{a}', {'resolve': b})

# ============ BOOK FLOW (POST) ============
f = req('POST', '/flows', {'name': 'easypc_appointment_book', 'icon': 'event_available',
    'status': 'active', 'trigger': 'webhook', 'options': {'method': 'POST', 'async': False}})['data']['id']
print('flow', f)

# 1 validate + normalize input
o_val = mkop(f, 'validate', 'exec', {'code': r'''module.exports = async function(data){
  const b = (data.$trigger && data.$trigger.body) || {};
  const req = ['store','service','first_name','mobile','preferred_date'];
  for (const k of req) if (!b[k]) throw new Error('Missing: ' + k);
  let mob = String(b.mobile).replace(/\D/g,'');
  if (mob.startsWith('63')) mob = '0' + mob.slice(2);
  if (!/^0\d{10}$/.test(mob)) throw new Error('Invalid mobile number');
  const dt = new Date(b.preferred_date + 'T00:00:00');
  if (isNaN(dt)) throw new Error('Invalid date');
  return { store: b.store, service: b.service, first_name: b.first_name,
    last_name: b.last_name || '', mobile: mob, email: (b.email||'').trim(),
    preferred_date: b.preferred_date, preferred_time: b.preferred_time || '',
    unit_type: b.unit_type || '', concern: b.concern || '', dow: dt.getDay() };
}'''}, 0, 0)

# 2 store + capacity check
o_chk = mkop(f, 'capcheck', 'likha_sql', {'sql': '''SELECT s.daily_capacity, s.open_days, s.max_advance_days, s.name AS store_name,
  (SELECT count(*) FROM easypc_appointments a
   WHERE a.store = s.id AND a.preferred_date = $2::date AND a.status = 'confirmed') AS booked
FROM easypc_stores s WHERE s.id = $1::uuid''', 'binding': ['{{validate.store}}','{{validate.preferred_date}}']}, 0, 100)

# 3 gate: open day, capacity, advance window, not past
o_gate = mkop(f, 'gate', 'exec', {'code': r'''module.exports = async function(data){
  const v = data.validate, rows = (data.capcheck && data.capcheck.rows) || [];
  const st = rows[0];
  if (!st) throw new Error('Store not found');
  const days = ['sun','mon','tue','wed','thu','fri','sat'];
  const open = st.open_days || [];
  if (open.length && open.indexOf(days[v.dow]) === -1) throw new Error('Branch closed on that day');
  const today = new Date(); today.setHours(0,0,0,0);
  const d = new Date(v.preferred_date + 'T00:00:00');
  if (d < today) throw new Error('Date is in the past');
  if (st.max_advance_days && (d - today)/86400000 > st.max_advance_days) throw new Error('Too far ahead — max ' + st.max_advance_days + ' days');
  if (st.daily_capacity && Number(st.booked) >= st.daily_capacity) throw new Error('That date is fully booked at ' + st.store_name);
  return { ok: true, store_name: st.store_name };
}'''}, 0, 200)

# 4 find-or-create customer by mobile
o_cust = mkop(f, 'findcust', 'likha_sql', {'sql': '''WITH found AS (SELECT id FROM easypc_customers WHERE mobile = $1 LIMIT 1),
ins AS (INSERT INTO easypc_customers (id, first_name, last_name, mobile, email, status)
        SELECT gen_random_uuid(), $2, $3, $1, $4, 'published'
        WHERE NOT EXISTS (SELECT 1 FROM found) RETURNING id)
SELECT id FROM found UNION ALL SELECT id FROM ins LIMIT 1''',
  'binding': ['{{validate.mobile}}','{{validate.first_name}}','{{validate.last_name}}','{{validate.email}}']}, 0, 300)

# 5 appointment number + token
o_num = mkop(f, 'mknum', 'likha_sql', {'sql': '''SELECT (SELECT count(*) FROM easypc_appointments) + 1 AS seq'''}, 0, 400)

# 6 create appointment
o_make = mkop(f, 'create', 'item-create', {'collection': 'easypc_appointments', 'permissions': '$full', 'payload': {
    'status': 'confirmed',
    'appointment_no': 'APPT-{{validate.preferred_date}}-X',
    'store': '{{validate.store}}', 'service': '{{validate.service}}',
    'preferred_date': '{{validate.preferred_date}}', 'preferred_time': '{{validate.preferred_time}}',
    'unit_type': '{{validate.unit_type}}', 'concern': '{{validate.concern}}',
    'manage_token': '{{mktoken.token}}'}}, 0, 500)

# 5b exec to build number+token (runs before create)
o_tok = mkop(f, 'mktoken', 'exec', {'code': r'''module.exports = async function(data){
  const rows = (data.mknum && data.mknum.rows) || [];
  const n = parseInt(rows[0] && rows[0].seq) || 1;
  const yr = (data.validate.preferred_date || '').slice(0,4) || new Date().getFullYear();
  const tok = Math.random().toString(36).slice(2,10) + Math.random().toString(36).slice(2,10);
  return { num: 'APPT-' + yr + '-' + String(n).padStart(4,'0'), token: tok };
}'''}, 100, 400)

# 7 respond + email
o_mail = mkop(f, 'confmail', 'mail', {
    'to': '{{validate.email}}',
    'subject': 'EasyPC appointment confirmed — {{mktoken.num}}',
    'body': '''Hi {{validate.first_name}},\n\nYour service appointment is confirmed.\n\nAppointment: {{mktoken.num}}\nBranch: {{gate.store_name}}\nDate: {{validate.preferred_date}} {{validate.preferred_time}}\n\nBring this reference and your unit. To view, reschedule, or cancel: {{trackurl}}/book?ref={{mktoken.num}} — use your registered mobile.\n\n— EasyPC''',
    'body_type': 'body'}, 100, 600)

o_res = mkop(f, 'respond', 'exec', {'code': r'''module.exports = async function(data){
  const cust = ((data.findcust && data.findcust.rows) || [])[0] || {};
  return { ok: true, appointment_no: data.mktoken.num, status: 'confirmed',
    store: data.gate.store_name, date: data.validate.preferred_date,
    time: data.validate.preferred_time, manage_ref: data.mktoken.num };
}'''}, 200, 700)

# fix create payload appointment_no + customer now that mktoken/findcust exist
req('PATCH', f'/operations/{o_make}', {'options': {'collection': 'easypc_appointments', 'permissions': '$full', 'payload': {
    'status': 'confirmed',
    'appointment_no': '{{mktoken.num}}',
    'store': '{{validate.store}}', 'service': '{{validate.service}}',
    'customer': "{{findcust.rows.0.id}}",
    'preferred_date': '{{validate.preferred_date}}', 'preferred_time': '{{validate.preferred_time}}',
    'unit_type': '{{validate.unit_type}}', 'concern': '{{validate.concern}}',
    'manage_token': '{{mktoken.token}}'}}})

link(o_val, o_chk); link(o_chk, o_gate); link(o_gate, o_cust); link(o_cust, o_num)
link(o_num, o_tok); link(o_tok, o_make); link(o_make, o_mail); link(o_mail, o_res)
req('PATCH', f'/flows/{f}', {'operation': o_val})
print('BOOK FLOW DONE', f)
