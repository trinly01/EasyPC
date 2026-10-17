import json, os, urllib.request, urllib.error

BASE = 'https://likha-playground.zyberlab.com'
TOKEN = os.environ.get("DIRECTUS_TOKEN", "")

def api(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method,
        headers={'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json', 'User-Agent': 'curl/8.5.0'},
        data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read(); return r.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b'{}')

CHECK = 'b6480ce1-e707-4f66-b22e-4142a458676e'
STAMP = '797a7f4c-45fe-4d44-af97-c8ecb8398d3b'

code = '''module.exports = async function(data){
  const t = data.$trigger || {};
  const p = t.payload || {};
  if (p.status !== "released") throw new Error("not released");
  const key = (t.keys||[])[0] || (p.keys||[])[0] || p.key || t.key;
  const rel = p.released_at ? new Date(p.released_at) : new Date();
  const DAYS = 30;
  const until = new Date(rel.getTime() + DAYS*86400000).toISOString().slice(0,10);
  return { key: key, until: until, released: rel.toISOString() };
}'''

st, res = api('PATCH', '/operations/' + CHECK, {'options': {'code': code}})
print('check:', st)

st, res = api('PATCH', '/operations/' + STAMP, {'options': {
    'collection': 'easypc_work_orders',
    'key': '{{$last.key}}',
    'emitEvents': False,
    'payload': {
        'service_warranty_until': '{{$last.until}}',
        'released_at': '{{$last.released}}'
    },
    'permissions': '$full'}})
print('stamp:', st)

# verify stored values are intact
for oid in (CHECK, STAMP):
    st, o = api('GET', '/operations/' + oid)
    opts = o['data']['options']
    print(o['data']['key'], '| opts:', json.dumps(opts)[:400])
