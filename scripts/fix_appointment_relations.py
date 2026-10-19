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
        print('ERR', method, path, e.code, e.read()[:300]); raise

TPL = {'easypc_stores': '{{name}}', 'easypc_customers': '{{first_name}} {{last_name}}',
       'easypc_services': '{{name}}', 'easypc_work_orders': '{{work_order_number}}'}

for fname, target in [('store','easypc_stores'), ('customer','easypc_customers'),
                      ('service','easypc_services'), ('work_order','easypc_work_orders')]:
    try:
        req('POST', '/relations', {
            'collection': 'easypc_appointments', 'field': fname,
            'related_collection': target,
            'schema': {'on_delete': 'SET NULL'}})
        print('relation', fname, '->', target)
    except urllib.error.HTTPError as e:
        print('relation err', fname, e.code)
    try:
        req('PATCH', f'/fields/easypc_appointments/{fname}',
            {'meta': {'interface': 'select-dropdown-m2o', 'options': {'template': TPL[target]}, 'width': 'half'}})
    except urllib.error.HTTPError:
        pass

# verify resolution
r = req('GET', '/relations/easypc_appointments?fields=collection,field,related_collection')
print(json.dumps(r['data'], indent=1))
