import urllib.request, urllib.error, json, os
TOKEN = os.environ['DIRECTUS_TOKEN']
B = 'https://likha-playground.zyberlab.com'
H = {'Authorization': f'Bearer {TOKEN}', 'User-Agent': 'curl/8.5.0', 'Content-Type': 'application/json'}

def req(method, path, body=None, quiet=False):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(B + path, data=data, headers=H, method=method)
    try:
        return json.loads(urllib.request.urlopen(r).read() or b'{}')
    except urllib.error.HTTPError as e:
        if not quiet: print('ERR', method, path, e.code, e.read()[:400])
        raise

# 1. collection
try:
    req('POST', '/collections', {
        'collection': 'easypc_appointments',
        'schema': {}, 'meta': {'icon': 'event_available', 'note': 'Customer-facing service bookings — precede work orders',
            'display_template': '{{appointment_no}} — {{customer.first_name}} {{customer.last_name}} ({{preferred_date}})'}
    })
    print('collection created')
except urllib.error.HTTPError as e:
    print('collection exists:', e.code)

def field(collection, name, typ, interface=None, opts=None, meta=None, special=None):
    body = {'field': name, 'type': typ, 'meta': dict(meta or {})}
    if interface: body['meta']['interface'] = interface
    if opts is not None: body['meta']['options'] = opts
    if special: body['schema'] = {'special': special} if isinstance(special, list) else special
    try:
        req('POST', f'/fields/{collection}', body)
        print('field', name)
    except urllib.error.HTTPError as e:
        print('field exists', name)

C = 'easypc_appointments'
field(C, 'status', 'string', 'select-dropdown', {'choices': [
    {'text': 'Confirmed', 'value': 'confirmed'},
    {'text': 'Arrived', 'value': 'arrived'},
    {'text': 'Cancelled', 'value': 'cancelled'},
    {'text': 'No-show', 'value': 'no_show'},
    {'text': 'Rescheduled', 'value': 'rescheduled'}]},
    {'width': 'half', 'note': 'Instant-confirmed on booking; arrived/cancelled/no_show updated by front desk or customer'})

field(C, 'appointment_no', 'string', 'input', None, {'width': 'half', 'readonly': True,
    'note': 'APPT-YYYY-NNNN assigned by easypc_appointment_book'})
field(C, 'preferred_date', 'date', 'datetime', {'includeSeconds': False}, {'width': 'half', 'required': True})
field(C, 'preferred_time', 'string', 'input', None, {'width': 'half',
    'note': 'Free-form advisory time, e.g. "2:00 PM" — capacity is daily'})
field(C, 'unit_type', 'string', 'input', None, {'width': 'half'})
field(C, 'concern', 'text', 'input-multiline', None, {'width': 'full'})
field(C, 'manage_token', 'string', 'input', None, {'hidden': True, 'readonly': True,
    'note': 'Random key for public manage (view/cancel/reschedule) — like tracking_token'})
field(C, 'notes', 'text', 'input-multiline', None, {'width': 'full'})

# relations
def m2o(field_name, target, sort=None):
    try:
        req('POST', f'/relations/{C}', {
            'collection': C, 'field': field_name,
            'related_collection': target,
            'schema': {'on_delete': 'SET NULL'}})
        print('relation', field_name)
    except urllib.error.HTTPError as e:
        print('relation exists/err', field_name, e.code)
    field(C, field_name, 'uuid', 'select-dropdown-m2o',
          {'template': '{{work_order_number}}' if target=='easypc_work_orders' else '{{name}}'},
          {'width': 'half', 'sort': sort})

m2o('store', 'easypc_stores')
m2o('customer', 'easypc_customers')
m2o('service', 'easypc_services')
m2o('work_order', 'easypc_work_orders')

# fix customer/service/store display templates
req('PATCH', f'/fields/{C}/customer', {'meta': {'options': {'template': '{{first_name}} {{last_name}}'}}}, quiet=True)
req('PATCH', f'/fields/{C}/service', {'meta': {'options': {'template': '{{name}} — ₱{{price}}'}}}, quiet=True)

# 2. stores: capacity + schedule fields
S = 'easypc_stores'
field(S, 'daily_capacity', 'integer', 'input', None, {'width': 'half', 'note': 'Max confirmed appointments per day'})
field(S, 'open_days', 'json', 'select-multiple-checkbox', {'choices': [
    {'text': 'Mon', 'value': 'mon'}, {'text': 'Tue', 'value': 'tue'}, {'text': 'Wed', 'value': 'wed'},
    {'text': 'Thu', 'value': 'thu'}, {'text': 'Fri', 'value': 'fri'}, {'text': 'Sat', 'value': 'sat'},
    {'text': 'Sun', 'value': 'sun'}]}, {'width': 'full'})
field(S, 'open_time', 'string', 'input', None, {'width': 'half', 'note': 'e.g. "9:00 AM"'})
field(S, 'close_time', 'string', 'input', None, {'width': 'half'})
field(S, 'max_advance_days', 'integer', 'input', None, {'width': 'half', 'note': 'How far ahead customers can book (0 = same-day only limit off)'})

# seed defaults on existing stores
r = req('GET', '/items/easypc_stores?fields=id,code')
for s in r['data']:
    req('PATCH', f"/items/easypc_stores/{s['id']}", {'daily_capacity': 10, 'open_days': ['mon','tue','wed','thu','fri','sat'],
        'open_time': '9:00 AM', 'close_time': '6:00 PM', 'max_advance_days': 30})
    print('seeded', s['code'])
print('DONE')
