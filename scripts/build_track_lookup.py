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

PUB = 'abf8a154-5b1c-4a46-ac9c-7300570f4f17'

# 1) remove the public read perms created earlier — flow-based lookup replaces them
st, res = api('GET', '/permissions?filter%5Bpolicy%5D%5B_eq%5D=' + PUB + '&fields=id,collection&limit=-1')
for p in res.get('data', []):
    if p['collection'].startswith('easypc'):
        api('DELETE', '/permissions/' + str(p['id']))
        print('removed public read on', p['collection'])

# 2) flow: validate -> likha_sql fetch -> shape -> (response = $last)
st, res = api('POST', '/flows', {
    'name': 'easypc_track_lookup', 'icon': 'travel_explore', 'trigger': 'webhook',
    'options': {'method': 'POST', 'async': False},
    'status': 'active', 'accountability': 'all'})
fid = res['data']['id']
print('flow:', fid)

code_validate = '''module.exports = async function(data){
  const b = (data.$trigger && data.$trigger.body) || {};
  const wo = String(b.wo || "").trim().toUpperCase();
  const token = String(b.token || "").trim().toLowerCase();
  if (!/^WO-\\d{4}-\\d{4}$/.test(wo)) throw new Error("bad wo");
  if (!/^[a-z0-9]{8,32}$/.test(token)) throw new Error("bad token");
  return { wo: wo, token: token };
}'''
st, res = api('POST', '/operations', {'flow': fid, 'key': 'validate', 'name': 'Validate input',
    'type': 'exec', 'position_x': 0, 'position_y': 0, 'options': {'code': code_validate}})
validate_id = res['data']['id']

sql = '''SELECT w.id, w.work_order_number, w.status, w.date_time_in, w.released_at,
       w.service_warranty_until, w.video_call_link, w.unit_type, w.unit_brand_model,
       w.test_result, s.name AS store_name, s.code AS store_code
FROM easypc_work_orders w
LEFT JOIN easypc_stores s ON s.id = w.store
WHERE w.work_order_number = '{{validate.wo}}'
  AND w.tracking_token = '{{validate.token}}'
LIMIT 1;'''
st, res = api('POST', '/operations', {'flow': fid, 'key': 'fetch', 'name': 'Fetch work order',
    'type': 'likha_sql', 'position_x': 0, 'position_y': 200, 'options': {'sql': sql}})
fetch_id = res['data']['id']

sql2 = '''SELECT u.milestone, u.message, u.date_created
FROM easypc_work_order_updates u
JOIN easypc_work_orders w ON w.id = u.work_order
WHERE w.work_order_number = '{{validate.wo}}'
  AND w.tracking_token = '{{validate.token}}'
ORDER BY u.date_created ASC;'''
st, res = api('POST', '/operations', {'flow': fid, 'key': 'fetch_updates', 'name': 'Fetch updates',
    'type': 'likha_sql', 'position_x': 200, 'position_y': 200, 'options': {'sql': sql2}})
fetchu_id = res['data']['id']

sql3 = '''SELECT sv.name, js.charged_price
FROM easypc_work_orders_services js
JOIN easypc_work_orders w ON w.id = js.easypc_work_orders_id
JOIN easypc_services sv ON sv.id = js.easypc_services_id
WHERE w.work_order_number = '{{validate.wo}}'
  AND w.tracking_token = '{{validate.token}}';'''
st, res = api('POST', '/operations', {'flow': fid, 'key': 'fetch_services', 'name': 'Fetch services',
    'type': 'likha_sql', 'position_x': 400, 'position_y': 200, 'options': {'sql': sql3}})
fetchs_id = res['data']['id']

code_shape = '''module.exports = async function(data){
  const rows = data.fetch || [];
  const wo = Array.isArray(rows) ? rows[0] : rows;
  if (!wo || !wo.id) return { found: false };
  return {
    found: true,
    work_order: {
      number: wo.work_order_number,
      status: wo.status,
      received: wo.date_time_in,
      released_at: wo.released_at,
      service_warranty_until: wo.service_warranty_until,
      video_call_link: wo.video_call_link,
      unit_type: wo.unit_type,
      unit: wo.unit_brand_model,
      test_result: wo.test_result,
      store: wo.store_name ? { name: wo.store_name, code: wo.store_code } : null,
      services: (data.fetch_services || []),
      updates: (data.fetch_updates || [])
    }
  };
}'''
st, res = api('POST', '/operations', {'flow': fid, 'key': 'shape', 'name': 'Shape response',
    'type': 'exec', 'position_x': 200, 'position_y': 400, 'options': {'code': code_shape}})
shape_id = res['data']['id']

# wiring: validate -> fetch (resolve) -> fetch_updates -> fetch_services -> shape
api('PATCH', '/operations/' + validate_id, {'resolve': fetch_id})
api('PATCH', '/operations/' + fetch_id, {'resolve': fetchu_id})
api('PATCH', '/operations/' + fetchu_id, {'resolve': fetchs_id})
api('PATCH', '/operations/' + fetchs_id, {'resolve': shape_id})
api('PATCH', '/flows/' + fid, {'operation': validate_id})
print('wired: validate -> fetch -> fetch_updates -> fetch_services -> shape')
print('ENDPOINT: POST /flows/trigger/' + fid + '  body: {"wo":"WO-2026-0001","token":"..."}')
