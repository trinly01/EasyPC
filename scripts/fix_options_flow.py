import urllib.request, json, os
TOKEN = os.environ['DIRECTUS_TOKEN']
B = 'https://likha-playground.zyberlab.com'
H = {'Authorization': f'Bearer {TOKEN}', 'User-Agent': 'curl/8.5.0', 'Content-Type': 'application/json'}
def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    return json.loads(urllib.request.urlopen(urllib.request.Request(B + path, data=data, headers=H, method=method)).read() or b'{}')

req('PATCH', '/operations/0e9afff8-e67f-411b-9567-e4b592e6c368', {'options': {'sql':
    "SELECT id, name, code, daily_capacity, open_days, open_time, close_time, max_advance_days FROM easypc_stores WHERE active = true ORDER BY name"}})

# also fix shape op (drop address)
req('PATCH', '/operations/dd637fe8-ae61-435f-afab-9c69cff54cdf', {'options': {'code': '''module.exports = async function(data){
  const st = (data.load && data.load.rows) || [];
  const sv = (data.loadsvc && data.loadsvc.rows) || [];
  return { stores: st.map(s => ({id: s.id, name: s.name, code: s.code,
    daily_capacity: s.daily_capacity, open_days: s.open_days, open_time: s.open_time,
    close_time: s.close_time, max_advance_days: s.max_advance_days})),
    services: sv.map(s => ({id: s.id, name: s.name, price: s.price})) };
}'''}})
print('patched')
