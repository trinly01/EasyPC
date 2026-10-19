import urllib.request, urllib.error, json, os
TOKEN = os.environ['DIRECTUS_TOKEN']
B = 'https://likha-playground.zyberlab.com'
H = {'Authorization': f'Bearer {TOKEN}', 'User-Agent': 'curl/8.5.0', 'Content-Type': 'application/json'}
FLOW = '9bf3bc0a-1bb5-4613-be99-1f6dac87eee4'
def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    return json.loads(urllib.request.urlopen(urllib.request.Request(B + path, data=data, headers=H, method=method)).read() or b'{}')

ops = {o['key']: o['id'] for o in req('GET', f'/operations?filter%5Bflow%5D%5B_eq%5D={FLOW}&fields=id,key')['data']}

# 1. email required in validate
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
  return { store: b.store, service: b.service, first_name: b.first_name,
    last_name: b.last_name || '', mobile: mob, email: (b.email||'').trim(),
    preferred_date: b.preferred_date, preferred_time: b.preferred_time || '',
    unit_type: b.unit_type || '', concern: b.concern || '', dow: dt.getDay() };
}'''}})

# 2. mknum also reads tracking_url
req('PATCH', f"/operations/{ops['mknum']}", {'options': {'sql':
    "SELECT (SELECT count(*) FROM easypc_appointments) + 1 AS seq, (SELECT tracking_url FROM easypc_settings LIMIT 1) AS track_url"}})

# 3. mktoken carries track_url
req('PATCH', f"/operations/{ops['mktoken']}", {'options': {'code': r'''module.exports = async function(data){
  const rows = (data.mknum && data.mknum.rows) || [];
  const r0 = rows[0] || {};
  const n = parseInt(r0.seq) || 1;
  const yr = (data.validate.preferred_date || '').slice(0,4) || new Date().getFullYear();
  const tok = Math.random().toString(36).slice(2,10) + Math.random().toString(36).slice(2,10);
  return { num: 'APPT-' + yr + '-' + String(n).padStart(4,'0'), token: tok,
    track_url: (r0.track_url || 'https://trinly01.github.io/EasyPC') };
}'''}})

# 4. mail body uses real URL
req('PATCH', f"/operations/{ops['confmail']}", {'options': {
    'to': '{{validate.email}}',
    'subject': 'EasyPC appointment confirmed — {{mktoken.num}}',
    'body': "Hi {{validate.first_name}},\n\nYour service appointment is confirmed.\n\nAppointment: {{mktoken.num}}\nBranch: {{gate.store_name}}\nDate: {{validate.preferred_date}} {{validate.preferred_time}}\n\nBring this reference and your unit. To view, reschedule, or cancel online: {{mktoken.track_url}}/book — use your appointment number + registered mobile.\n\n— EasyPC"}})

print('patched validate/mknum/mktoken/confmail')
