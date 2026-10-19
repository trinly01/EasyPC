import urllib.request, json, os
TOKEN = os.environ['DIRECTUS_TOKEN']
B = 'https://likha-playground.zyberlab.com'
H = {'Authorization': f'Bearer {TOKEN}', 'User-Agent': 'curl/8.5.0', 'Content-Type': 'application/json'}
def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    return json.loads(urllib.request.urlopen(urllib.request.Request(B + path, data=data, headers=H, method=method)).read() or b'{}')

# find the 3 policies
pols = req('GET', '/policies?filter%5Bname%5D%5B_starts_with%5D=easypc&fields=id,name')['data']
P = {p['name']: p['id'] for p in pols}
print(P)

FIELDS = ['id','status','appointment_no','preferred_date','preferred_time','unit_type','concern',
          'notes','manage_token','store','customer','service','work_order',
          'user_created','date_created','user_updated','date_updated']

def add_perm(policy, action, fields, perms=None):
    body = {'policy': policy, 'collection': 'easypc_appointments', 'action': action,
            'fields': fields, 'permissions': perms or {}, 'presets': {}}
    req('POST', '/permissions', body)

branch = {'store': {'_eq': '$CURRENT_USER.easypc_store'}}

# front desk: full CRUD within branch (they manage bookings + checkin)
for act in ['create','read','update','delete']:
    add_perm(P['easypc_front_desk_policy'], act, FIELDS, branch)
# technician: read only within branch
add_perm(P['easypc_technician_policy'], 'read', FIELDS, branch)
# manager: full, unfiltered
for act in ['create','read','update','delete']:
    add_perm(P['easypc_manager_policy'], act, FIELDS, {})

# move collection into easypc_operations folder
try:
    req('PATCH', '/collections/easypc_appointments', {'meta': {'group': 'easypc_operations', 'sort': 0}})
    print('grouped under easypc_operations')
except Exception as e:
    print('group err', e)
print('DONE')
