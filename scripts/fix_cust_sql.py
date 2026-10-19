import urllib.request, json, os
TOKEN = os.environ['DIRECTUS_TOKEN']
B = 'https://likha-playground.zyberlab.com'
H = {'Authorization': f'Bearer {TOKEN}', 'User-Agent': 'curl/8.5.0', 'Content-Type': 'application/json'}
FLOW = '9bf3bc0a-1bb5-4613-be99-1f6dac87eee4'
def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    return json.loads(urllib.request.urlopen(urllib.request.Request(B + path, data=data, headers=H, method=method)).read() or b'{}')
ops = {o['key']: o['id'] for o in req('GET', f'/operations?filter%5Bflow%5D%5B_eq%5D={FLOW}&fields=id,key')['data']}

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
  const full = (String(b.first_name) + ' ' + String(b.last_name || '')).trim();
  return { store: q(b.store), service: q(b.service), full_name: q(full),
    mobile: mob, email: q((b.email||'').trim()),
    email_raw: (b.email||'').trim(), first_name_raw: String(b.first_name||''),
    preferred_date: q(b.preferred_date), preferred_time: q(b.preferred_time || ''),
    unit_type: q(b.unit_type || ''), concern: q(b.concern || ''), dow: dt.getDay() };
}'''}})

req('PATCH', f"/operations/{ops['findcust']}", {'options': {'sql': r"""WITH found AS (SELECT id FROM easypc_customers WHERE contact_no = '{{validate.mobile}}' LIMIT 1),
ins AS (INSERT INTO easypc_customers (id, name, contact_no, email)
        SELECT gen_random_uuid(), '{{validate.full_name}}', '{{validate.mobile}}', '{{validate.email}}'
        WHERE NOT EXISTS (SELECT 1 FROM found) RETURNING id)
SELECT id FROM found UNION ALL SELECT id FROM ins LIMIT 1"""}})

print('patched')
