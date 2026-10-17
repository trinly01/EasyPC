"""Reorganize easypc_work_orders tabs around the service journey + user story.

Changes:
- new tab grp_testing (test_result, test_remarks, additional_findings)
- terms_* move grp_unit -> grp_intake (T&C is signed at intake on paper)
- video_call_link -> grp_updates (customer comms)
- print -> grp_intake
- friendly tab labels via meta.translations
- child sort order matches journey/reading order
"""
import json, os, urllib.request, urllib.error

BASE = 'https://likha-playground.zyberlab.com'
TOKEN = os.environ.get('DIRECTUS_TOKEN', '')
COLL = 'easypc_work_orders'

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

# --- 1) new Testing tab ----------------------------------------------------
st, res = api('POST', '/fields/' + COLL, {
    'field': 'grp_testing', 'type': 'alias',
    'meta': {'interface': 'group-raw', 'special': ['alias', 'no-data', 'group'],
             'group': 'grp_tabs', 'sort': 6,
             'translations': [{'language': 'en-US', 'translation': 'Testing'}]},
})
print('grp_testing', st, '' if st in (200, 201) else res)

# --- 2) tab labels + order --------------------------------------------------
TABS = [
    ('grp_intake',     1, 'Intake'),
    ('grp_unit',       2, 'Unit & Services'),
    ('grp_parts',      3, 'Parts & Photos'),
    ('grp_assessment', 4, 'Assessment & Approvals'),
    ('grp_work',       5, 'Repair'),
    ('grp_testing',    6, 'Testing'),
    ('grp_releasing',  7, 'Release'),
    ('grp_updates',    8, 'Updates & Notifications'),
]
for fld, sort, label in TABS:
    st, res = api('PATCH', '/fields/%s/%s' % (COLL, fld), {'meta': {
        'sort': sort,
        'translations': [{'language': 'en-US', 'translation': label}]}})
    print('tab', fld, '->', label, st, '' if st == 200 else res)

# --- 3) child field placement ----------------------------------------------
PLAN = {
    'grp_intake':     ['job_order_no', 'odoo_ticket', 'store', 'date_time_in', 'intake_path',
                       'customer', 'received_by', 'warranty_claim_of',
                       'terms_accepted', 'terms_accepted_at', 'terms_version', 'print'],
    'grp_unit':       ['unit_type', 'unit_brand_model', 'password_handling', 'customer_concern', 'services'],
    'grp_parts':      ['cpu_socket_pins_photographed', 'photo_count', 'parts', 'files'],
    'grp_assessment': ['diagnostics', 'diagnosis_findings', 'recommended_solution',
                       'assessed_by', 'assessed_at', 'approvals'],
    'grp_work':       ['processes', 'parts_used'],
    'grp_testing':    ['test_result', 'test_remarks', 'additional_findings'],
    'grp_releasing':  ['so_number', 'amount', 'old_parts_disposition', 'released_by', 'released_at',
                       'receiver_name', 'receiver_id', 'service_warranty_until', 'warranty_claims'],
    'grp_updates':    ['updates', 'video_call_link'],
}
for grp, fields in PLAN.items():
    for i, fld in enumerate(fields, 1):
        st, res = api('PATCH', '/fields/%s/%s' % (COLL, fld), {'meta': {'group': grp, 'sort': i}})
        tag = '' if st == 200 else (' ERR ' + json.dumps(res)[:120])
        print(' ', grp, i, fld, st, tag)

st, res = api('POST', '/utils/cache/clear')
print('cache:', st)
