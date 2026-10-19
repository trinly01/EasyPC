import urllib.request, json, os
TOKEN = os.environ['DIRECTUS_TOKEN']
B = 'https://likha-playground.zyberlab.com'
H = {'Authorization': f'Bearer {TOKEN}', 'User-Agent': 'curl/8.5.0', 'Content-Type': 'application/json'}
FLOW = '9bf3bc0a-1bb5-4613-be99-1f6dac87eee4'
def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    return json.loads(urllib.request.urlopen(urllib.request.Request(B + path, data=data, headers=H, method=method)).read() or b'{}')
ops = {o['key']: o['id'] for o in req('GET', f'/operations?filter%5Bflow%5D%5B_eq%5D={FLOW}&fields=id,key')['data']}

# validate: escape single quotes for raw SQL interpolation
req('PATCH', f"/operations/{ops['validate']}", {'options': {'code': r'''module.exports = async function(data){
  const b = (data.$trigger && data.$trigger.body) || {};
  const req = ['store','service','first_name','mobile','email','preferred_date'];
  for (const k of req) if (!b[k]) throw new Error('Missing: ' + k);
  let mob = String(b.mobile).replace(/\D/g,'');
  if (mob.startsWith('63')) mob = '0' + mob.slice(2);
  if (!/^0\d{10}$/.test(mob)) throw new Error('Invalid mobile number');
  if (!/^\S+@\S+\.\S+$/.test(b.email)) throw new Error('Invalid email');
  const dt = new Date(b.preferred_date + 'T00:00:00');
  if (isNaN(dt)) throw new Error('Invalid date');
  const q = s => String(s || '').replace(/'/g, "''");
  return { store: q(b.store), service: q(b.service), first_name: q(b.first_name),
    last_name: q(b.last_name || ''), mobile: mob, email: q((b.email||'').trim()),
    email_raw: (b.email||'').trim(), first_name_raw: String(b.first_name||''),
    preferred_date: q(b.preferred_date), preferred_time: q(b.preferred_time || ''),
    unit_type: q(b.unit_type || ''), concern: q(b.concern || ''), dow: dt.getDay() };
}'''}})

# capcheck: {{}} interpolation
req('PATCH', f"/operations/{ops['capcheck']}", {'options': {'sql': r"""SELECT s.daily_capacity, s.open_days, s.max_advance_days, s.name AS store_name,
  (SELECT count(*) FROM easypc_appointments a
   WHERE a.store = s.id AND a.preferred_date = '{{validate.preferred_date}}'::date AND a.status = 'confirmed') AS booked
FROM easypc_stores s WHERE s.id = '{{validate.store}}'::uuid"""}})

# findcust: {{}} interpolation
req('PATCH', f"/operations/{ops['findcust']}", {'options': {'sql': r"""WITH found AS (SELECT id FROM easypc_customers WHERE mobile = '{{validate.mobile}}' LIMIT 1),
ins AS (INSERT INTO easypc_customers (id, first_name, last_name, mobile, email, status)
        SELECT gen_random_uuid(), '{{validate.first_name}}', '{{validate.last_name}}', '{{validate.mobile}}', '{{validate.email}}', 'published'
        WHERE NOT EXISTS (SELECT 1 FROM found) RETURNING id)
SELECT id FROM found UNION ALL SELECT id FROM ins LIMIT 1"""}})

# mail: use raw (unescaped) values for display
req('PATCH', f"/operations/{ops['confmail']}", {'options': {
    'to': '{{validate.email_raw}}',
    'subject': 'EasyPC appointment confirmed — {{mktoken.num}}',
    'body': "Hi {{validate.first_name_raw}},\n\nYour service appointment is confirmed.\n\nAppointment: {{mktoken.num}}\nBranch: {{gate.store_name}}\nDate: {{validate.preferred_date}} {{validate.preferred_time}}\n\nBring this reference and your unit. To view, reschedule, or cancel online: {{mktoken.track_url}}/book — use your appointment number + registered mobile.\n\n— EasyPC"}})

print('patched validate/capcheck/findcust/confmail')
