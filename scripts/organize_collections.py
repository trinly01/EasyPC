"""Organize easypc_* collections into change-frequency subgroups.

EasyPC (existing top group)
  easypc_operations   — transactional rows touched daily
  easypc_master_data  — lookups edited occasionally
  easypc_settings     — singleton config, sits at EasyPC root
"""
import json, os, urllib.request, urllib.error

BASE = 'https://likha-playground.zyberlab.com'
TOKEN = os.environ.get('DIRECTUS_TOKEN', '')

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

# --- 1) subgroup folders ---------------------------------------------------
for name, icon, note, sort in [
    ('easypc_operations', 'folder_open', 'Transactional — rows created/edited daily', 1),
    ('easypc_master_data', 'folder', 'Lookups — edited occasionally (prices, SKUs, branches)', 2),
]:
    st, res = api('POST', '/collections', {
        'collection': name,
        'meta': {'group': 'EasyPC', 'icon': icon, 'note': note, 'sort': sort},
        'schema': None,
    })
    print('group', name, st, '' if st in (200, 201) else res)

# --- 2) move collections + sort by change frequency ------------------------
PLAN = [
    # operations — ordered most-touched first
    ('easypc_work_orders',           'easypc_operations', 1),
    ('easypc_customers',             'easypc_operations', 2),
    ('easypc_work_order_updates',    'easypc_operations', 3),
    ('easypc_work_order_parts_used', 'easypc_operations', 4),
    ('easypc_job_processes',         'easypc_operations', 5),
    ('easypc_diagnostics',           'easypc_operations', 6),
    ('easypc_approvals',             'easypc_operations', 7),
    ('easypc_work_order_parts',      'easypc_operations', 8),
    ('easypc_work_orders_services',  'easypc_operations', 9),
    ('easypc_work_orders_files',     'easypc_operations', 10),
    # master data
    ('easypc_services',              'easypc_master_data', 1),
    ('easypc_parts_catalog',         'easypc_master_data', 2),
    ('easypc_stores',                'easypc_master_data', 3),
    # config — stays at EasyPC root, sorted after the groups
    ('easypc_settings',              'EasyPC', 10),
]
for coll, grp, sort in PLAN:
    st, res = api('PATCH', '/collections/' + coll, {'meta': {'group': grp, 'sort': sort}})
    print('move', coll, '->', grp, st, '' if st == 200 else res)

st, res = api('POST', '/utils/cache/clear')
print('cache:', st)
