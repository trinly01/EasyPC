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

# 1) revert setnum to numbering-only
st, fls = api('GET', '/flows?filter%5Bname%5D%5B_eq%5D=easypc_generate_wo_number')
fid_num = fls['data'][0]['id']
st, ops = api('GET', '/operations?filter%5Bflow%5D%5B_eq%5D=' + fid_num)
fmt = [o for o in ops['data'] if o['key'] == 'format'][0]
setnum = [o for o in ops['data'] if o['key'] == 'setnum'][0]

code_fmt = '''module.exports = async function(data){
  const c = data.$last;
  let n = Array.isArray(c) ? (c[0] && c[0].count) : (c && c.count);
  if (n && typeof n === 'object') n = n.id;
  n = parseInt(n) || 1;
  const t = data.$trigger || {};
  const key = t.key || (t.payload && (t.payload.key || (t.payload.keys||[])[0])) || (t.keys||[])[0];
  const yr = new Date().getFullYear();
  return { key: key, num: 'WO-' + yr + '-' + String(n).padStart(4,'0') };
}'''
api('PATCH', '/operations/' + fmt['id'], {'options': {'code': code_fmt}})
api('PATCH', '/operations/' + setnum['id'], {'options': {
    'collection': 'easypc_work_orders', 'key': '{{$last.key}}', 'emitEvents': False,
    'payload': {'work_order_number': '{{$last.num}}'}, 'permissions': '$full'}})
print('numbering flow reverted')

# 2) rewire easypc_video_link: rd(item-read) -> genlink(exec) -> setlink(update) -> mkupdate(create update row)
st, fls = api('GET', '/flows?filter%5Bname%5D%5B_eq%5D=easypc_video_link')
fid = fls['data'][0]['id']
st, ops = api('GET', '/operations?filter%5Bflow%5D%5B_eq%5D=' + fid)
genlink = [o for o in ops['data'] if o['key'] == 'genlink'][0]
setlink = [o for o in ops['data'] if o['key'] == 'setlink'][0]

# item-read current WO (to check existing link)
st, res = api('POST', '/operations', {'flow': fid, 'key': 'rd', 'name': 'Read WO',
    'type': 'item-read', 'position_x': 0, 'position_y': 0,
    'options': {'collection': 'easypc_work_orders', 'key': '{{$trigger.keys[0]}}',
                'query': {'fields': ['id', 'video_call_link', 'work_order_number']}, 'permissions': '$full'}})
rd = res['data']['id']
print('rd:', st, rd)

code_gen = '''module.exports = async function(data){
  const t = data.$trigger || {};
  const p = t.payload || {};
  if (p.status !== "in_repair") throw new Error("not entering in_repair");
  const wo = data.$last || {};
  if (wo.video_call_link) throw new Error("link already exists");
  const key = (t.keys||[])[0];
  const rand = Math.random().toString(36).slice(2, 10);
  const num = wo.work_order_number || String(key).slice(0,8);
  const slug = ("easypc-" + num + "-" + rand).toLowerCase().replace(/[^a-z0-9-]/g,"");
  const link = "https://meet.jit.si/" + slug;
  return { key: key, link: link, msg: "Your unit is now being worked on by our technician. Join the video call for updates/questions: " + link };
}'''
api('PATCH', '/operations/' + genlink['id'], {'options': {'code': code_gen}, 'resolve': setlink['id']})

api('PATCH', '/operations/' + setlink['id'], {'options': {
    'collection': 'easypc_work_orders', 'key': '{{$last.key}}', 'emitEvents': False,
    'payload': {'video_call_link': '{{$last.link}}'}, 'permissions': '$full'}})

st, res = api('POST', '/operations', {'flow': fid, 'key': 'mkupdate', 'name': 'Notify customer',
    'type': 'item-create', 'position_x': 0, 'position_y': 400,
    'options': {'collection': 'easypc_work_order_updates',
                'payload': {'work_order': '{{genlink.key}}', 'update_type': 'milestone',
                            'milestone': 'in_repair', 'message': '{{genlink.msg}}',
                            'notify_customer': True},
                'permissions': '$full'}})
mkid = res['data']['id']
api('PATCH', '/operations/' + setlink['id'], {'resolve': mkid})
api('PATCH', '/operations/' + rd, {'resolve': genlink['id']})
api('PATCH', '/flows/' + fid, {'operation': rd})
print('rewired: rd -> genlink -> setlink -> mkupdate')
