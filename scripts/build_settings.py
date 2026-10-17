"""Create easypc_settings (singleton) — centrally managed T&C/waiver text +
shop policy values. Also adds the documented-but-missing O2M aliases
(customers.work_orders, stores.work_orders). Idempotent-ish: skips existing.
"""
import json, os, urllib.request, urllib.error

BASE = 'https://likha-playground.zyberlab.com'
TOKEN = os.environ.get('DIRECTUS_TOKEN', '')

POLICIES = {
    'easypc_technician_policy': '010c73a2-5c75-43de-b75c-a83679fd9c09',
    'easypc_front_desk_policy': '19d6a338-cf58-4e2a-b429-9fea8c40baa8',
    'easypc_manager_policy': '6b6bef39-0897-4011-b0d0-e2296037875c',
}

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

def field(collection, name, ftype, interface=None, note=None, options=None, special=None, readonly=False, hidden=False):
    meta = {}
    if interface: meta['interface'] = interface
    if note: meta['note'] = note
    if options: meta['options'] = options
    if special: meta['special'] = special
    if readonly: meta['readonly'] = True
    if hidden: meta['hidden'] = True
    f = {'field': name, 'type': ftype}
    if meta: f['meta'] = meta
    st, res = api('POST', '/fields/' + collection, f)
    print('field', collection + '.' + name, st, '' if st in (200, 201) else res)

# --- 1) singleton collection --------------------------------------------
st, res = api('POST', '/collections', {
    'collection': 'easypc_settings', 'singleton': True,
    'meta': {'singleton': True, 'icon': 'settings', 'note': 'EasyPC shop settings — T&C text, warranty policy, tracking/print references'},
    'schema': {},
    'fields': [{'field': 'id', 'type': 'uuid', 'meta': {'hidden': True, 'readonly': True, 'interface': 'input', 'special': ['uuid']}, 'schema': {'is_primary_key': True}}],
})
print('collection easypc_settings', st, '' if st in (200, 201) else res)

# --- 2) fields -----------------------------------------------------------
field('easypc_settings', 'terms_version', 'string', 'input', 'Shown on printed forms; snapshot into work_orders.terms_version at intake')
field('easypc_settings', 'terms_conditions', 'text', 'input-rich-text-html', 'Full EasyPC Terms & Conditions — single source for tracker page, emails, and reprints')
field('easypc_settings', 'liability_waiver', 'text', 'input-rich-text-html', 'Liability waiver text printed on the service form')
field('easypc_settings', 'service_warranty_days', 'integer', 'input', 'Labor/service warranty length — used by easypc_warranty_stamp (currently hardcoded 30d; migrate later)')
field('easypc_settings', 'part_warranty_default_days', 'integer', 'input', 'Default when a catalog part has no warranty_days')
field('easypc_settings', 'unclaimed_days', 'integer', 'input', 'Days in ready_for_release before a unit may be marked unclaimed (T&C clause 6)')
field('easypc_settings', 'tracking_url', 'string', 'input', 'Public tracker base URL printed on forms')
field('easypc_settings', 'video_base_url', 'string', 'input', 'Jitsi base used by easypc_video_link')
field('easypc_settings', 'support_email', 'string', 'input')
field('easypc_settings', 'support_phone', 'string', 'input')

# --- 3) seed the singleton row -------------------------------------------
st, existing = api('GET', '/items/easypc_settings')
if st == 200 and existing.get('data'):
    print('settings row exists — skipping seed')
else:
    st, res = api('POST', '/items/easypc_settings', {
        'terms_version': 'EPC-TC-2026-01',
        'terms_conditions': (
            '<ol>'
            '<li>Additional work or cost discovered during service requires the customer&#39;s approval before proceeding.</li>'
            '<li>EasyPC is not responsible for data loss — customers must back up their data before service.</li>'
            '<li>Diagnosis/assessment fees apply as quoted at intake.</li>'
            '<li>Replacement parts installed by EasyPC carry the stated parts warranty; labor carries the service warranty.</li>'
            '<li>Customer-supplied parts carry no EasyPC warranty — warranty remains with the seller.</li>'
            '<li>Units not claimed within the stated claim window after notification may be subject to storage fees or disposition; a valid ID is required at release.</li>'
            '</ol>'),
        'liability_waiver': (
            '<p>The customer acknowledges that EasyPC&#39;s liability is limited to the service fees paid. '
            'EasyPC is not liable for pre-existing damage, data loss, or units left beyond the claim window. '
            'The signed paper service form remains the legal copy.</p>'),
        'service_warranty_days': 30,
        'part_warranty_default_days': 90,
        'unclaimed_days': 30,
        'tracking_url': 'https://trinly01.github.io/EasyPC',
        'video_base_url': 'https://meet.jit.si',
        'support_email': 'support@easypc.com',
        'support_phone': '',
    })
    print('seed settings row', st, '' if st in (200, 201) else res)

# --- 4) permissions: read for all staff, write for manager ---------------
for pol in (POLICIES['easypc_technician_policy'], POLICIES['easypc_front_desk_policy'], POLICIES['easypc_manager_policy']):
    st, res = api('POST', '/permissions', {'policy': pol, 'collection': 'easypc_settings', 'action': 'read', 'fields': ['*']})
    print('perm read', pol[:24], st, '' if st in (200, 201) else res)
st, res = api('POST', '/permissions', {'policy': POLICIES['easypc_manager_policy'], 'collection': 'easypc_settings', 'action': 'update', 'fields': ['*']})
print('perm manager update', st, '' if st in (200, 201) else res)

# --- 5) missing O2M aliases (documented but never created) ---------------
for coll, fld, rel_field, rel_coll in [
    ('easypc_customers', 'work_orders', 'customer', 'easypc_work_orders'),
    ('easypc_stores', 'work_orders', 'store', 'easypc_work_orders'),
]:
    st, res = api('POST', '/fields/' + coll, {
        'field': fld, 'type': 'alias',
        'meta': {'interface': 'list-o2m', 'special': ['o2m'], 'options': {'template': '{{work_order_number}} — {{status}}'}},
    })
    print('alias field', coll + '.' + fld, st, '' if st in (200, 201) else res)
    st, res = api('POST', '/relations', {
        'collection': rel_coll, 'field': rel_field,
        'related_collection': coll,
        'meta': {'one_field': fld, 'sort_field': None},
    })
    print('relation', rel_coll + '.' + rel_field, '->', coll, st, '' if st in (200, 201) else res)

st, res = api('POST', '/utils/cache/clear')
print('cache clear:', st)
