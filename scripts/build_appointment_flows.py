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

def mkflow(name, trigger, opts=None):
    body = {'name': name, 'icon': 'event_available', 'status': 'active', 'trigger': trigger, 'options': opts or {}}
    r = req('POST', '/flows', body)['data']
    print('flow', name, r['id']); return r['id']

def mkop(flow, key, typ, opts, x, y):
    r = req('POST', '/operations', {'flow': flow, 'name': key, 'key': key, 'type': typ,
        'position_x': x, 'position_y': y, 'options': opts})['data']
    print('  op', key, r['id']); return r['id']

def link(op_id, resolve=None):
    if resolve: req('PATCH', f'/operations/{op_id}', {'resolve': resolve})

# ============ 1. OPTIONS FLOW (GET) ============
# returns bookable stores + services for the public form
f = mkflow('easypc_appointment_options', 'webhook', {'method': 'GET', 'async': False})
o1 = mkop(f, 'load', 'likha_sql', {'sql':
    "SELECT id, name, code, address, daily_capacity, open_days, open_time, close_time, max_advance_days FROM easypc_stores ORDER BY name"}, 0, 0)
o2 = mkop(f, 'loadsvc', 'likha_sql', {'sql':
    "SELECT id, name, price FROM easypc_services ORDER BY name"}, 0, 100)
o3 = mkop(f, 'shape', 'exec', {'code': '''module.exports = async function(data){
  const st = (data.load && data.load.rows) || [];
  const sv = (data.loadsvc && data.loadsvc.rows) || [];
  return { stores: st.map(s => ({id: s.id, name: s.name, code: s.code, address: s.address,
    daily_capacity: s.daily_capacity, open_days: s.open_days, open_time: s.open_time,
    close_time: s.close_time, max_advance_days: s.max_advance_days})),
    services: sv.map(s => ({id: s.id, name: s.name, price: s.price})) };
}'''}, 0, 200)
link(o1, o2); link(o2, o3)
req('PATCH', f'/flows/{f}', {'operation': o1})
