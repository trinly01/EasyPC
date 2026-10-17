import json, os, urllib.request, urllib.error

BASE = 'https://likha-playground.zyberlab.com'
TOKEN = os.environ.get('DIRECTUS_TOKEN', '')

def api(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method,
        headers={'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json', 'User-Agent': 'curl/8.5.0'},
        data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read(); return r.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b'{}')

# 1) field — hidden from staff forms, machine-only
st, res = api('POST', '/fields/easypc_work_orders', {
    'field': 'tracking_token', 'type': 'string',
    'meta': {'interface': 'input', 'readonly': True, 'hidden': True,
             'note': 'Public tracking token — used in /track/<wo>/<token> URLs'}})
print('field:', st)

# 2) numbering flow: format generates token too, setnum writes it
st, fls = api('GET', '/flows?filter%5Bname%5D%5B_eq%5D=easypc_generate_wo_number')
fid = fls['data'][0]['id']
st, ops = api('GET', '/operations?filter%5Bflow%5D%5B_eq%5D=' + fid)
fmt = [o for o in ops['data'] if o['key'] == 'format'][0]
setnum = [o for o in ops['data'] if o['key'] == 'setnum'][0]

code_fmt = '''module.exports = async function(data){
  const c = data.$last;
  let n = Array.isArray(c) ? (c[0] && c[0].count) : (c && c.count);
  if (n && typeof n === 'object') n = n.id;
  n = parseInt(n) || 1;
  const t = data.$trigger || {};
  const key = t.key || (t.payload && (t.payload.key || (t.payload.keys||[])[0])) || (t.keys||[])[0];
  const yr = new Date().getFullYear();
  const tok = Math.random().toString(36).slice(2,10) + Math.random().toString(36).slice(2,10);
  return { key: key, num: 'WO-' + yr + '-' + String(n).padStart(4,'0'), token: tok };
}'''
api('PATCH', '/operations/' + fmt['id'], {'options': {'code': code_fmt}})
api('PATCH', '/operations/' + setnum['id'], {'options': {
    'collection': 'easypc_work_orders', 'key': '{{$last.key}}', 'emitEvents': False,
    'payload': {'work_order_number': '{{$last.num}}', 'tracking_token': '{{$last.token}}'},
    'permissions': '$full'}})
print('numbering flow updated')
