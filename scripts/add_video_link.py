import json, os, urllib.request, urllib.error

BASE = 'https://likha-playground.zyberlab.com'
TOKEN = os.environ.get("DIRECTUS_TOKEN", "")

def api(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method,
        headers={'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json', 'User-Agent': 'curl/8.5.0'},
        data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read(); return r.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b'{}')

# 1) field on easypc_work_orders
st, res = api('POST', '/fields/easypc_work_orders', {
    'field': 'video_call_link', 'type': 'string',
    'meta': {'interface': 'input', 'readonly': True, 'group': 'grp_intake',
             'note': 'Jitsi room link — auto-generated, share with customer for remote diagnosis'}})
print('field:', st)

# 2) flow: on create -> generate link -> update row
st, res = api('POST', '/flows', {
    'name': 'easypc_video_link', 'icon': 'videocam', 'trigger': 'event',
    'options': {'type': 'action', 'scope': ['items.update'], 'collections': ['easypc_work_orders']},
    'status': 'active', 'accountability': 'all'})
fid = res['data']['id']
print('flow:', st, fid)

code = '''module.exports = async function(data){
  const t = data.$trigger || {};
  const p = t.payload || {};
  // run only when the numbering flow just stamped work_order_number
  const wo = p.work_order_number;
  if (!wo) throw new Error("no wo number in payload");
  const key = (t.keys||[])[0] || (p.keys||[])[0] || p.key || t.key;
  const rand = Math.random().toString(36).slice(2, 10);
  const slug = ('easypc-' + wo + '-' + rand).toLowerCase().replace(/[^a-z0-9-]/g,'');
  return { key: key, link: 'https://meet.jit.si/' + slug };
}'''
st, res = api('POST', '/operations', {'flow': fid, 'key': 'genlink', 'name': 'Generate link',
    'type': 'exec', 'position_x': 0, 'position_y': 0, 'options': {'code': code}})
oid = res['data']['id']
print('genlink op:', st, oid)

st, res = api('POST', '/operations', {'flow': fid, 'key': 'setlink', 'name': 'Set link',
    'type': 'item-update', 'position_x': 0, 'position_y': 200,
    'options': {'collection': 'easypc_work_orders', 'key': '{{$last.key}}', 'emitEvents': False,
                'payload': {'video_call_link': '{{$last.link}}'}, 'permissions': '$full'}})
setid = res['data']['id']
print('setlink op:', st, setid)

st, res = api('PATCH', '/operations/' + oid, {'resolve': setid})
print('wire:', st)
st, res = api('PATCH', '/flows/' + fid, {'operation': oid})
print('entry:', st)
