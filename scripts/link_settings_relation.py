"""Add easypc_work_orders.settings (M2O -> easypc_settings singleton row).
Live values (tracking_url, support_email, video_base_url) resolve through the
relation in print/email contexts; legal text stays snapshotted on the WO.

- M2O field + relation
- numbering flow: getset also selects id -> pick emits settings_id -> setnum writes it
- backfill existing WOs
"""
import json, os, urllib.request, urllib.error

BASE = 'https://likha-playground.zyberlab.com'
TOKEN = os.environ.get('DIRECTUS_TOKEN', '')
FLOW = '44615a57-1342-406e-947e-653e964809f8'
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

# --- 1) M2O field + relation ---------------------------------------------
st, res = api('POST', '/fields/easypc_work_orders', {
    'field': 'settings', 'type': 'uuid',
    'meta': {'interface': 'select-dropdown-m2o', 'special': ['m2o'], 'hidden': True, 'readonly': True,
             'note': 'Live link to easypc_settings singleton — resolves current tracking_url / support contacts / video base in print & emails'},
})
print('field settings', st, '' if st in (200, 201) else res)
st, res = api('POST', '/relations', {
    'collection': 'easypc_work_orders', 'field': 'settings',
    'related_collection': 'easypc_settings',
})
print('relation', st, '' if st in (200, 201) else res)

# --- 2) flow: getset selects id too; pick emits settings_id ---------------
import urllib.parse
q = urllib.parse.urlencode({'filter[flow][_eq]': FLOW, 'fields': 'id,key', 'limit': '-1'})
ops = api('GET', '/operations?' + q)[1]['data']
getset_id = [o['id'] for o in ops if o['key'] == 'getset'][0]
pick_id = [o['id'] for o in ops if o['key'] == 'pick'][0]

st, res = api('PATCH', '/operations/' + getset_id, {'options': {
    'sql': 'SELECT id, terms_version, terms_conditions, liability_waiver FROM easypc_settings LIMIT 1;'}})
print('getset', st)

pick_code = '''module.exports = async function(data){
  const g = data.getset || {};
  const row = (g.rows && g.rows[0]) || {};
  return {
    settings_id: row.id || null,
    terms_version: row.terms_version || "",
    terms_snapshot: row.terms_conditions || "",
    waiver_snapshot: row.liability_waiver || ""
  };
}'''
st, res = api('PATCH', '/operations/' + pick_id, {'options': {'code': pick_code}})
print('pick', st)

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
        'settings': '{{pick.settings_id}}',
    },
    'permissions': '$full',
}})
print('setnum', st, '' if st == 200 else res)

# --- 3) backfill ----------------------------------------------------------
st, res = api('POST', '/flows', {'name': 'easypc_backfill_settings_link', 'icon': 'bolt',
    'trigger': 'webhook', 'options': {'method': 'POST', 'async': False},
    'status': 'active', 'accountability': 'all'})
bf = res['data']['id']
st, res = api('POST', '/operations', {'flow': bf, 'key': 'run', 'name': 'Backfill',
    'type': 'likha_sql', 'position_x': 0, 'position_y': 0,
    'options': {'sql': 'UPDATE easypc_work_orders SET settings = (SELECT id FROM easypc_settings LIMIT 1) WHERE settings IS NULL;'}})
api('PATCH', '/flows/' + bf, {'operation': res['data']['id']})
st, res = api('POST', '/flows/trigger/' + bf)
print('backfill', st)
api('PATCH', '/flows/' + bf, {'status': 'inactive'})

st, res = api('POST', '/utils/cache/clear')
print('cache:', st)
