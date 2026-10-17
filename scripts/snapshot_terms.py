"""Snapshot easypc_settings legal text onto each work order at create.

- adds easypc_work_orders.terms_snapshot / waiver_snapshot (readonly)
- numbering flow gains: getset (likha_sql read settings) -> pick (exec flatten)
  -> setnum now writes terms_version + terms_snapshot + waiver_snapshot too
- backfills existing work orders
"""
import json, os, urllib.request, urllib.error

BASE = 'https://likha-playground.zyberlab.com'
TOKEN = os.environ.get('DIRECTUS_TOKEN', '')
FLOW = '44615a57-1342-406e-947e-653e964809f8'
OP_FORMAT = '4edacb64-4233-4034-ae74-fdb7ecdd2cff'
OP_SETNUM = '5027759c-2520-485a-9f79-c2484161aff6'

def api(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method,
        headers={'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json',
                 'User-Agent': 'curl/8.5.0'},
        data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read(); return r.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b'{}')

# --- 1) fields -----------------------------------------------------------
for name, note in [
    ('terms_snapshot', 'T&C text (HTML) snapshotted from easypc_settings at intake — printed on the form'),
    ('waiver_snapshot', 'Liability waiver text (HTML) snapshotted at intake'),
]:
    st, res = api('POST', '/fields/easypc_work_orders', {
        'field': name, 'type': 'text',
        'meta': {'interface': 'input-rich-text-html', 'readonly': True, 'hidden': True, 'note': note}})
    print('field', name, st, '' if st in (200, 201) else res)

# --- 2) flow: getset (sql) -> pick (exec) -> setnum -----------------------
st, res = api('POST', '/operations', {'flow': FLOW, 'key': 'getset', 'name': 'Read settings',
    'type': 'likha_sql', 'position_x': 400, 'position_y': 0,
    'options': {'sql': 'SELECT terms_version, terms_conditions, liability_waiver FROM easypc_settings LIMIT 1;'}})
getset_id = res['data']['id']

pick_code = '''module.exports = async function(data){
  const g = data.getset || {};
  const row = (g.rows && g.rows[0]) || {};
  return {
    terms_version: row.terms_version || "",
    terms_snapshot: row.terms_conditions || "",
    waiver_snapshot: row.liability_waiver || ""
  };
}'''
st, res = api('POST', '/operations', {'flow': FLOW, 'key': 'pick', 'name': 'Pick settings fields',
    'type': 'exec', 'position_x': 600, 'position_y': 0, 'options': {'code': pick_code}})
pick_id = res['data']['id']

# rewire: format -> getset -> pick -> setnum
api('PATCH', '/operations/' + OP_FORMAT, {'resolve': getset_id})
api('PATCH', '/operations/' + getset_id, {'resolve': pick_id})
api('PATCH', '/operations/' + pick_id, {'resolve': OP_SETNUM})
st, res = api('PATCH', '/operations/' + OP_SETNUM, {'options': {
    'collection': 'easypc_work_orders',
    'key': '{{format.key}}',
    'emitEvents': False,
    'payload': {
        'work_order_number': '{{format.num}}',
        'tracking_token': '{{format.token}}',
        'terms_version': '{{pick.terms_version}}',
        'terms_snapshot': '{{pick.terms_snapshot}}',
        'waiver_snapshot': '{{pick.waiver_snapshot}}',
    },
    'permissions': '$full',
}})
print('setnum rewire', st, '' if st == 200 else res)

# --- 3) backfill existing work orders ------------------------------------
st, res = api('POST', '/flows/trigger/e66dbe3a-0000-0000-0000-000000000000')  # placeholder guard
sql = '''UPDATE easypc_work_orders w
SET terms_version   = s.terms_version,
    terms_snapshot  = s.terms_conditions,
    waiver_snapshot = s.liability_waiver
FROM easypc_settings s
WHERE w.terms_snapshot IS NULL;'''
# run via a throwaway webhook flow with likha_sql
st, res = api('POST', '/flows', {'name': 'easypc_backfill_terms', 'icon': 'bolt', 'trigger': 'webhook',
    'options': {'method': 'POST', 'async': False}, 'status': 'active', 'accountability': 'all'})
bf = res['data']['id']
st, res = api('POST', '/operations', {'flow': bf, 'key': 'run', 'name': 'Backfill',
    'type': 'likha_sql', 'position_x': 0, 'position_y': 0, 'options': {'sql': sql}})
op = res['data']['id']
api('PATCH', '/flows/' + bf, {'operation': op})
st, res = api('POST', '/flows/trigger/' + bf)
print('backfill', st, json.dumps(res)[:150])
api('PATCH', '/flows/' + bf, {'status': 'inactive'})

st, res = api('POST', '/utils/cache/clear')
print('cache:', st)
